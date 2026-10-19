# Thêm, đổi tên, xóa cột: kịch bản và cách landing / silver xử lý

Bộ file 05–10 và 98 mô phỏng 3 thay đổi trên **một bảng** `bronze.ins_customer` (~1,97 triệu dòng, sink `iceberg-sink-pvi-ins-customer` → `pvi_landing.ins_customer`). Bộ này độc lập với case 01–04 (các case đó dùng `ins_policy`, `ins_policy_transaction`, `ins_channel`).

| File | Chạy trên | Nội dung |
|---|---|---|
| [05_registry_setup.sql](05_registry_setup.sql) | PostgreSQL | Tạo sổ thay đổi schema: `ins_schema_snapshot`, `ins_schema_change_log`, hàm `ins_capture_schema_changes()`. Chụp mốc ban đầu |
| [05b_event_trigger_optional.sql](05b_event_trigger_optional.sql) | PostgreSQL | Tùy chọn. Tự ghi sổ mỗi khi có `ALTER TABLE`. **Cần superuser**: nếu không đủ quyền thì script báo NOTICE và bỏ qua |
| [06_add_column.sql](06_add_column.sql) | PostgreSQL | Thêm `kyc_status varchar(12)`. Backfill 1.000 khách, thêm 3 khách mới |
| [07_rename_column.sql](07_rename_column.sql) | PostgreSQL | Đổi `birth_year` → `year_of_birth`. Sửa 500 khách, thêm 2 khách mới |
| [08_drop_column.sql](08_drop_column.sql) | PostgreSQL | Xóa `gender`. Trước đó sao lưu sang `ins_bak_customer_gender`. Sửa 500 khách, thêm 2 khách mới |
| [09_check_add_rename_drop.sql](09_check_add_rename_drop.sql) | PostgreSQL | Xem cột, sổ thay đổi, trạng thái từng cột. **Sinh sẵn danh sách cột cho silver** (mục 5) |
| [10_silver_dremio.sql](10_silver_dremio.sql) | **Dremio** | Kiểm tra landing và truy vấn silver có hợp nhất cột đổi tên, bỏ cột đã xóa |
| [98_rollback_add_rename_drop.sql](98_rollback_add_rename_drop.sql) | PostgreSQL | Đưa schema về như cũ. Phần trả lại giá trị `gender` là tùy chọn, mặc định để comment |

**Thứ tự chạy trong DBeaver** (mỗi file dùng `Alt+X`): `05` → (`05b`) → `09` → `06` → `09` → `07` → `09` → `08` → `09`. Sau đó chạy `10` trên Dremio, chờ sink commit khoảng 30 giây sau mỗi case. Muốn quay về như cũ thì chạy `98`.

Dòng mô phỏng có `customer_code LIKE 'SIM-C0%'`. Các script chạy lại được nhiều lần.

## 1. Cơ chế hiện tại xử lý 3 trường hợp

Pipeline: Postgres → Debezium `pg-src-pvi` (pgoutput, `ExtractNewRecordState` thêm `__op`, `__source_ts_ms`, `__source_lsn`, `__deleted`) → Kafka `pg-pvi.bronze.*` → sink tabular `iceberg-kafka-connect` **0.6.19** (Iceberg 1.5.2, `evolve-schema-enabled=true`, append-only) → Hive `pvi_landing` → Dremio.

Đã kiểm tra trong mã sink (`iceberg-kafka-connect-0.6.19.jar` lấy từ pod `my-connect-connect-0`): sink chỉ có **3 thao tác đổi schema** là `AddColumn`, `UpdateType` và `MakeOptional`. Sink **không có** thao tác đổi tên hay xóa cột, và khớp field với cột theo **tên**.

| Case | PostgreSQL | Debezium | Landing (Iceberg) | Căn cứ |
|---|---|---|---|---|
| **Thêm cột** | Chỉ đổi metadata | Field mới xuất hiện từ lệnh DML đầu tiên sau DDL (bản thân DDL không phát event) | Sink **thêm cột**. Event cũ = NULL | Test thực tế 13/10 (case 01) |
| **Đổi tên cột** | Chỉ đổi metadata, **giữ attnum**. View vẫn chạy | Field tên cũ biến mất, field tên mới xuất hiện | Sink **thêm cột tên mới**, **giữ cột tên cũ**. Event sau thay đổi: cột cũ = NULL | Suy ra từ mã sink. **Chưa test thực tế**: chạy `07` + `10` để xác nhận |
| **Xóa cột** | Đánh dấu `attisdropped` | Field biến mất | Sink **giữ cột**, event mới có giá trị NULL. Nếu cột đang là required thì sink đổi sang optional | Test thực tế 13/10 (case 03), cùng với mã sink |

Như vậy, với 2 ý đầu trong ý tưởng của bạn, **pipeline hiện tại đã tự làm đúng như vậy**:
- *Landing giữ nguyên, không drop cột*: sink không thể drop cột, nên không cần làm thêm gì.
- *Đổi tên: giữ cột cũ, thêm cột mới*: sink tự làm, vì nó coi tên mới là một cột mới.

**Phần còn thiếu** là landing không ghi lại *vì sao* một cột thôi có giá trị:
- NULL do cột đã bị xóa trông giống hệt NULL nghiệp vụ (ví dụ `gender` của khách tổ chức).
- Không có gì cho biết `year_of_birth` chính là `birth_year` sau khi đổi tên. Nhìn từ landing, đó chỉ là "thêm một cột, một cột khác thôi có giá trị".

Vì vậy silver cần một nguồn thông tin riêng. Đó là **sổ thay đổi schema** ở mục 2.

## 2. Sổ thay đổi schema (`05_registry_setup.sql`)

Ý tưởng chính: so `pg_attribute` theo **attnum**, không theo tên.

| Thao tác PostgreSQL | attnum | Ghi sổ |
|---|---|---|
| `ADD COLUMN` | Cấp attnum mới | `ADD` |
| `RENAME COLUMN` | **Giữ nguyên**, chỉ đổi `attname` | `RENAME` (old → new, cùng attnum) |
| `ALTER COLUMN TYPE` | Giữ nguyên, đổi kiểu | `ALTER_TYPE` |
| `DROP COLUMN` | Giữ nguyên, `attisdropped = true` | `DROP` |

Nhờ vậy sổ phân biệt **chắc chắn** "đổi tên" với "xóa A, thêm B", không phải đoán theo tên hay theo dữ liệu.

**Không cần superuser:** `pg_attribute` ai cũng đọc được. Hàm `ins_capture_schema_changes()` được gọi ngay sau DDL trong 06–08. Nếu có DDL chạy ngoài các script này, lần gọi tiếp theo vẫn ghi đúng loại thay đổi, chỉ có `detected_at` và `wal_lsn` là trễ hơn. Muốn ghi tự động ngay lúc chạy DDL thì dùng `05b`, cần superuser.

Bảng `ins_schema_change_log`:

| Cột | Ý nghĩa |
|---|---|
| `change_type` | `ADD` / `DROP` / `RENAME` / `ALTER_TYPE` |
| `attnum` | Định danh ổn định của cột. Các lần đổi tên của cùng một cột có cùng attnum |
| `old_column_name`, `new_column_name` | Tên trước và sau thay đổi |
| `old_data_type`, `new_data_type` | Kiểu trước và sau thay đổi |
| `wal_lsn_num` | LSN dạng số, so trực tiếp được với `__source_lsn` ở landing. Event có `__source_lsn >= wal_lsn_num` là event sau thay đổi |

Kết quả chạy thử 05 → 08 (PostgreSQL 16 local, dữ liệu giả 5.000 khách):

```
change_type | attnum | old_column_name | new_column_name
ADD         |     11 |                 | kyc_status
RENAME      |     10 | birth_year      | year_of_birth
DROP        |      9 | gender          |
```

Sau `98`, sổ ghi tiếp các thay đổi ngược: `RENAME year_of_birth → birth_year`, `DROP kyc_status`, `ADD gender` (attnum 12, tức là một cột mới, đúng với bản chất của PostgreSQL).

## 3. Silver dùng sổ như thế nào

`09` mục 5 sinh sẵn danh sách cột cho silver:

```sql
customer_code, customer_name, segment_code, tax_code, province_code, home_company_code,
is_aggregated_retail, created_date,
COALESCE(year_of_birth, birth_year) AS year_of_birth,   -- RENAME
kyc_status                                               -- ADD
-- gender: DROP → không select
```

- **Xóa cột:** silver không select các cột có `DROP` trong sổ (và không có lần `ADD` lại sau đó). Landing vẫn giữ dữ liệu cũ nếu sau này cần.
- **Đổi tên:** dùng `COALESCE(tên_mới, tên_cũ)` và **áp dụng trên từng event**, trước khi lấy dòng mới nhất theo khóa. Cách này đúng vì mỗi event chỉ có 1 trong 2 cột có giá trị: event trước khi đổi tên chỉ có cột cũ, event sau chỉ có cột mới. Nhờ vậy, khi nguồn cố ý set NULL sau khi đổi tên, silver không lấy nhầm giá trị cũ. **Không** dùng kiểu "lấy giá trị khác NULL gần nhất" qua nhiều event.
- **Đổi tên nhiều lần** (a → b → c, cùng attnum): `COALESCE(c, b, a)`. Mục 5 tự gộp đủ các tên cũ.

## 4. Rủi ro cần lưu ý

1. **Dòng cũ không được phát lại sau khi đổi tên.** Khách không bị sửa sau thay đổi chỉ có giá trị ở cột tên cũ. Nếu silver chỉ đọc cột mới thì sẽ mất dữ liệu, nên **bắt buộc** phải COALESCE.
2. **Đổi tên kèm đổi kiểu:** cột mới ở landing mang kiểu mới. Khi đó COALESCE cần `CAST` cột cũ. Sổ có đủ `old_data_type` và `new_data_type` để sinh biểu thức.
3. **Dùng lại tên đã xóa:** nếu xóa `gender` rồi sau này thêm lại một `gender` khác (như sau `98`), landing sẽ dùng lại **cùng cột** `gender`, vì sink khớp theo tên. Khi đó cột trộn 2 nghĩa. Nếu kiểu không tương thích, sink sẽ FAILED như case 04. Sổ phân biệt được 2 cột (attnum 9 và 12), nên silver có thể cắt theo `wal_lsn_num` nếu cần.
4. **Schema mới chỉ đến landing khi có DML.** Với bảng danh mục ít thay đổi, có thể nhiều ngày sau mới thấy cột mới. Đổi tên cũng chỉ hiện ở landing khi có dòng bị sửa. Đây là lý do silver nên đọc **sổ**, không suy ra schema từ landing.
5. **Dremio cache metadata:** chạy `ALTER TABLE hive.pvi_landing.ins_customer REFRESH METADATA` trước khi kiểm tra (đầu file `10`).
6. **`gen_volume.py --replace`** COPY vào `ins_customer` theo danh sách cột cố định (`gender`, `birth_year`), nên sẽ lỗi sau `07` và `08`. Hãy chạy `98` trước. `--reset` xóa mọi bảng `ins_*`, kể cả sổ, nên sau khi nạp lại phải chạy lại `05` để chụp mốc mới.
7. **Trả lại giá trị `gender` trong `98`** tạo ra khoảng 1,9 triệu UPDATE, tức khoảng 1,9 triệu event CDC vào landing. Vì vậy phần này để comment, chỉ chạy khi thật sự cần.

## Đưa sổ lên landing (tùy chọn)

Để silver đọc sổ ngay trong lakehouse, không phải kết nối PostgreSQL:

1. `ALTER PUBLICATION dbz_pvi_pub ADD TABLE bronze.ins_schema_change_log;` (cần quyền owner của publication).
2. Thêm `bronze.ins_schema_change_log` vào `table.include.list` của connector `pg-src-pvi`.
3. Tạo sink `iceberg-sink-pvi-ins-schema-change-log` theo mẫu của các sink `iceberg-sink-pvi-ins-*`, đích là `pvi_landing.ins_schema_change_log`.

Các bước 2 và 3 sửa cấu hình connector trên cluster nên chưa làm. Khi cần, hãy yêu cầu để làm tiếp.

## Đã kiểm chứng

- Chạy cả bộ trên PostgreSQL **16.2** local (pgserver), dữ liệu giả 5.000 khách, theo 2 cách: có và không có event trigger. Mỗi case chạy 2 lần, `98` chạy 2 lần. Sổ ghi đúng ADD / RENAME / DROP, không ghi trùng. View dùng `birth_year` vẫn chạy sau khi đổi tên.
- Chưa chạy trên `reportapi` (PostgreSQL 14). Cú pháp dùng trong script đều có từ PostgreSQL 11 trở xuống: `EXECUTE FUNCTION` trong event trigger, identity column, phép trừ `pg_lsn`.
- Hành vi của sink với đổi tên được suy ra từ mã sink, chưa test trên cluster.
