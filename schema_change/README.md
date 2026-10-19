# Mô phỏng thay đổi schema (schema change)

Bộ này gồm 3 case phổ biến, chạy trên 2 bảng trong schema `bronze` của DB `reportapi`. Mỗi case gồm **DDL** và **DML phát sinh sau thay đổi**. Cần có DML vì CDC hoặc pipeline phía sau chỉ "thấy" schema mới khi có dòng dữ liệu mới.

| File | Case | Bảng.cột | Thay đổi | Ghi lại bảng? |
|---|---|---|---|---|
| [01_add_column.sql](01_add_column.sql) | Thêm cột | `ins_policy_transaction.payment_method` | Thêm `varchar(20)` NULL. Backfill 2.000 giao dịch gần nhất, thêm 5 giao dịch mới có giá trị | Không (chỉ đổi metadata) |
| [02_alter_type.sql](02_alter_type.sql) | Đổi kiểu dữ liệu | `ins_policy_transaction.fx_rate` | `numeric(18,2)` → `numeric(18,6)`. Thêm 3 giao dịch USD với tỷ giá 6 số lẻ | **Có**: ~4,2 triệu dòng, khóa bảng khoảng 1–2 phút |
| [03_drop_column.sql](03_drop_column.sql) | Xóa cột | `ins_policy.renewal_of_policy_id` | Xóa cột lỗi thời (luôn NULL, FK tự tham chiếu), thay bằng `prev_policy_no`. Thêm 1 hợp đồng tái tục mới đầy đủ | Không |
| [04_int_to_string.sql](04_int_to_string.sql) | Đổi số → chuỗi | `ins_channel.sort_order` | `int` → `varchar(10)`, cập nhật `'01'` và `'D7'`. **Làm sink Iceberg FAILED**, xem kết quả test bên dưới | Có (bảng 7 dòng) |
| [99_rollback.sql](99_rollback.sql) | Hoàn tác | cả 3 bảng | Xóa dữ liệu mô phỏng, trả lại cột, kiểu và FK như ban đầu | Có (do đổi lại kiểu `fx_rate`) |
| [00_check_schema.sql](00_check_schema.sql) | Xem schema | cả 2 bảng | Liệt kê cột và kiểu, đếm dòng mô phỏng | — |

Bộ **thêm / đổi tên / xóa cột** trên `ins_customer`, kèm sổ thay đổi schema cho silver (file 05–10, 98): xem [README_add_rename_drop.md](README_add_rename_drop.md).

## Kết quả test thực tế qua CDC (13/10/2026)

Pipeline: Postgres `bronze.ins_*` → Debezium `pg-src-pvi` → Kafka `pg-pvi.bronze.*` → Iceberg sink `io.tabular` 1.5.2 (`evolve-schema-enabled=true`, `upsert-mode-enabled=false`, `errors.tolerance=all`) → Hive `pvi_landing` → Dremio `hive.pvi_landing.*`.

| Case | Postgres | Kafka (Debezium) | Iceberg / Dremio |
|---|---|---|---|
| 1. Thêm cột `payment_method` | ✅ Có cột | ✅ Event có field mới | ✅ **Thêm cột**, dữ liệu đúng |
| 2. `fx_rate` numeric(18,2) → (18,6) | ✅ Ghi lại bảng trong 47 giây | ✅ Decimal scale=6, giá trị `26187.123457` | ⚠️ **Cột vẫn `DECIMAL(38,2)`. Giá trị bị làm tròn âm thầm thành `26187.12`**. Không có lỗi, DLQ trống, connector vẫn `RUNNING` |
| 3. Xóa `renewal_of_policy_id` | ✅ Mất cột | ✅ Event không còn field | ⚠️ **Cột vẫn còn**, dòng mới có giá trị NULL |
| Rollback (xóa `payment_method`) | ✅ Mất cột | — | ⚠️ Cột `payment_method` vẫn còn |
| 4. `ins_channel.sort_order` int → varchar ([04_int_to_string.sql](04_int_to_string.sql)) | ✅ Đổi kiểu, cập nhật `'01'`, `'D7'` | ✅ Field kiểu `string` | ❌ **Task sink FAILED** với `NumberFormatException: For input string: "D7"`. Cột Iceberg vẫn `INTEGER`. `'01'` đổi được thành `1`, `'D7'` thì không. Lỗi xảy ra bên trong sink nên `errors.tolerance=all` **không** bắt được và DLQ trống. Bảng ngừng đồng bộ hoàn toàn |

**Khôi phục sink bị kẹt vì bản ghi lỗi (đã làm cho case 4).** Iceberg không đổi được `int` → `string`, nên dù khởi động lại, sink vẫn chết đúng ở bản ghi đó. Cần bỏ qua offset lỗi:

```bash
# 1. dừng connector (Strimzi)
kubectl -n kafka patch kafkaconnector iceberg-sink-pvi-ins-channel --type merge -p '{"spec":{"state":"stopped"}}'
# 2. dời offset của CẢ HAI consumer group qua bản ghi lỗi (ví dụ sang 9)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group connect-iceberg-sink-pvi-ins-channel \
  --topic pg-pvi.bronze.ins_channel:0 --reset-offsets --to-offset 9 --execute
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group cg-control-iceberg-sink-pvi-ins-channel \
  --topic pg-pvi.bronze.ins_channel:0 --reset-offsets --to-offset 9 --execute
# 3. chạy lại
kubectl -n kafka patch kafkaconnector iceberg-sink-pvi-ins-channel --type merge -p '{"spec":{"state":"running"}}'
```

Nếu nguồn thật cần đổi `int` → `string`, đừng đổi kiểu tại chỗ. Thêm cột mới (ví dụ `sort_code varchar`), hoặc tạo lại bảng Iceberg với kiểu `string` rồi nạp lại dữ liệu.

Kết luận:
- Sink Iceberg chỉ **thêm cột** hoặc **tăng precision** của decimal. Nó không xóa cột và không đổi scale (giới hạn của đặc tả Iceberg).
- Đổi scale của decimal là trường hợp **nguy hiểm nhất**, vì mất độ chính xác mà không có cảnh báo nào. Cách xử lý:
  1. Tạo cột mới (ví dụ `fx_rate_v2 numeric(18,6)`) thay vì đổi kiểu cột cũ.
  2. Hoặc đổi kiểu bảng Iceberg thủ công (tạo lại bảng hoặc ghi lại dữ liệu) trước khi đổi ở nguồn.
- Bảng Iceberg ở chế độ chỉ thêm dòng: mỗi event (`r`/`c`/`u`/`d`) là một dòng. Để có trạng thái hiện tại, lấy dòng có `__source_lsn` lớn nhất theo khóa và bỏ `__deleted = 'true'`.

## Cách chạy bằng DBeaver

1. Mở tunnel bằng `F:\Project\k8s\tunnel-reportapi.cmd`, rồi kết nối tới `127.0.0.1:15432`.
2. Vào **File → Open File…** và chọn file `.sql`. Ở thanh trên editor, chọn connection `reportapi`.
3. Chạy cả file bằng **Execute SQL Script** (`Alt+X`), **không** dùng `Ctrl+Enter` vì phím này chỉ chạy 1 câu lệnh.
4. Thứ tự gợi ý: `00` → `01` → `00` → `02` → `00` → `03` → `00`. Muốn quay về như cũ thì chạy `99`.

## Ghi chú

- **Nhận diện dữ liệu mô phỏng:** giao dịch có `created_by = 'SIM.SCHEMA_CHANGE'`; hợp đồng có `policy_no LIKE 'SIM-%'`.
- **Chạy lại được nhiều lần.** DDL được bỏ qua nếu đã áp dụng. Case 1 và 2 mỗi lần chạy thêm vài giao dịch mới; case 3 chỉ tạo hợp đồng mới ở lần đầu.
- **Ba cột này không nằm trong view nào.** Nếu đổi kiểu hoặc xóa một cột mà `v_ins_revenue_line` hay `mv_ins_*` có dùng (ví dụ `premium_vnd`), PostgreSQL sẽ báo lỗi *cannot alter type of a column used by a view*. Khi đó phải `DROP VIEW` rồi tạo lại. Đây cũng là một tình huống schema change hay gặp.
- **Thứ tự cột sau rollback khác ban đầu.** Sau `99_rollback.sql`, cột `renewal_of_policy_id` được thêm lại ở **cuối bảng**, vì PostgreSQL không chèn cột vào giữa. Kiểu, nullable và FK thì giống ban đầu.
- **Materialized view không tự cập nhật.** `mv_ins_*` không tự thấy các dòng mô phỏng; cần `REFRESH MATERIALIZED VIEW` nếu muốn.
- **Nếu test CDC (Debezium):** các bảng `ins_*` hiện **chưa** nằm trong publication nào (`dbz_*_pub` chỉ gồm bảng `bronze.customer_tiering` và `bronze.transaction`). Muốn Debezium bắt thay đổi thì phải thêm bảng vào publication, ví dụ `ALTER PUBLICATION <pub> ADD TABLE bronze.ins_policy_transaction, bronze.ins_policy;`, và thêm vào `table.include.list` của connector.
