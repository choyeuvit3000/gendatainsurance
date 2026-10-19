# POC Doanh thu bảo hiểm: dữ liệu khối lượng lớn cho dashboard

Bộ sinh [gen_volume.py](gen_volume.py) dùng **nguyên mô hình v2** (danh mục, cột, quy tắc doanh thu: xem [DESIGN_RATIONALE.md](DESIGN_RATIONALE.md)). Điểm khác là sinh giao dịch ở **quy mô vận hành**:

- thời gian: **01/08/2026 – 30/09/2026** (61 ngày);
- mỗi ngày **> 50.000 giao dịch** (tháng 8 khoảng 53–66 nghìn, tháng 9 khoảng 80–99 nghìn), tổng khoảng 5 triệu;
- **cơ cấu doanh thu theo BCTC PVI** (cùng tỷ trọng với v2); doanh thu tuyệt đối = quy mô PVI tháng 8–9 × hệ số k ≈ 3,93 (khoảng 6.300 tỷ cho 2 tháng).

Số liệu chính xác sau mỗi lần nạp: xem phần "Kiểm tra sau khi nạp" trong log và `audit/run_audit.py`.

Mọi tham số theo thời gian đều có nhãn căn cứ ([CHÍNH THỨC] / [DATASET] / [NGUỒN THAY THẾ] / [QUY ƯỚC] / [ƯỚC TÍNH]), xem [calibration/README.md](calibration/README.md). Hiệu chỉnh lần gần nhất: 14/10/2026.

## Tài liệu

| File | Nội dung |
|---|---|
| [docs/POC_Doanh_thu_BH_volume.html](docs/POC_Doanh_thu_BH_volume.html) | Tài liệu tổng hợp trong 1 file: tổng quan, căn cứ tham số, căn cứ mô hình, data dictionary có ô lọc, quy tắc nghiệp vụ, mô phỏng thay đổi schema |
| [docs/Data_Dictionary_volume.xlsx](docs/Data_Dictionary_volume.xlsx) | Data dictionary Excel: mỗi bảng 1 sheet, có số dòng, % NULL, giá trị mẫu đo trên dữ liệu thật ở `reportapi` |
| [calibration/README.md](calibration/README.md) | Căn cứ từng tham số và nguồn |
| [audit/consistency_checks.sql](audit/consistency_checks.sql) | 41 quy tắc kiểm tra toàn vẹn nghiệp vụ |

Hai file trong `docs/` được sinh từ catalog thật của `bronze.ins_*`. Mô tả cột lấy từ `scripts/dictionary_meta.py`; các cột chỉ có ở bản này nằm trong `VOLUME_COLUMNS`. Sinh lại khi tunnel đang mở:

```bash
DOCS_TARGET=volume PG_URI=postgresql://report:<mật khẩu>@127.0.0.1:15432/reportapi python scripts/build_docs.py
```

## Nơi nạp

PostgreSQL `reportapi` tại `192.168.18.101:5432`, schema **`bronze`**. Mọi bảng mang tiền tố **`ins_`** để không lẫn với các bảng sẵn có (`customer_tiering`, `transaction`…).

| v2 | Trên `bronze` |
|---|---|
| `ref.<bảng>` (16 danh mục + khách hàng) | `bronze.ins_<bảng>` (ví dụ `bronze.ins_product`, `bronze.ins_customer`) |
| `core.policy`, `core.policy_transaction`, `core.transaction_coverage`, `core.coinsurance_share`, `core.revenue_allocation` | `bronze.ins_policy`, `bronze.ins_policy_transaction`, `bronze.ins_transaction_coverage`, `bronze.ins_coinsurance_share`, `bronze.ins_revenue_allocation` |
| (mới) view doanh thu | `bronze.v_ins_revenue_line`, `bronze.mv_ins_revenue_daily`, `bronze.mv_ins_txn_hourly` |

Ngoài v2 có thêm 3 cột: `ins_customer.gender`, `ins_customer.birth_year`, `ins_policy.prev_policy_no`. Cột `prev_policy_no` là số hợp đồng năm trước được tái tục; hợp đồng đó nằm ngoài kỳ dữ liệu nên lưu dạng text.

Muốn đổi đích thì đặt biến `TARGET_SCHEMA` và `TABLE_PREFIX`.

## Quy ước NULL và tham chiếu danh mục

Lớp `bronze` mô phỏng **hệ thống nguồn**, nên giữ NULL đúng nghiệp vụ. Mọi mã khác NULL đều có khóa ngoại đã kiểm chứng.

| Cột | NULL khi | Bản chất |
|---|---|---|
| `ins_policy.partner_code` | Kênh không qua đối tác: trực tiếp, đại lý cá nhân, đấu thầu, web/app công ty (kênh điện tử không có đối tác) | Hợp lệ (không áp dụng) |
| `ins_policy.channel_code` | ~0,5% hợp đồng nguồn không khai báo kênh | Lỗi dữ liệu có chủ đích |
| `prev_policy_no`, `renewal_of_policy_id` | Hợp đồng cấp mới | Hợp lệ |
| `premium_rate_pct` | Sản phẩm tính theo biểu phí cố định hoặc theo đầu người | Hợp lệ |
| `ins_customer.tax_code` / `gender`, `birth_year` | Khách cá nhân / khách tổ chức | Hợp lệ |

Quy tắc "dòng fact luôn tham chiếu danh mục" áp dụng ở **lớp phân tích**. View `v_ins_revenue_line` và các `mv_ins_*` gán:

| Giá trị NULL ở `bronze` | Gán thành |
|---|---|
| Kênh NULL | `CHUA_XD` |
| Đối tác NULL, kênh điện tử | `WEB_APP` |
| Đối tác NULL, kênh khác | `KHONG_QUA_DT` |
| Đối tác NULL, kênh NULL | `CHUA_XD` |

Kiểm tra toàn bộ ràng buộc nghiệp vụ (41 quy tắc: hợp đồng, khách hàng, giao dịch, dòng phí, đồng bảo hiểm, phân bổ, tham chiếu):

```bash
PG_URI=postgresql://report:<mật khẩu>@127.0.0.1:15432/reportapi python audit/run_audit.py
```

Lịch sử sửa dữ liệu đã nạp nằm trong `audit/`:
- `fix_in_place_2026-10-13.sql`: đối tác TNDS xe máy, SĐBS trên hợp đồng chưa duyệt, tỷ lệ phí.
- `revert_na_members_2026-10-13.sql`: trả NULL về `bronze`.

## Dùng cho dashboard

Công thức doanh thu không đổi so với v2:

```
doanh thu = premium_vnd × share_pct(OWN) / 100 × allocation_pct / 100
```

Chỉ tính chứng từ `APPROVED`, theo `accounting_date`.

| Đối tượng | Grain | Dùng cho |
|---|---|---|
| `bronze.v_ins_revenue_line` | 1 dòng phí × đơn vị được phân bổ | Drill-down chi tiết; đã join đủ 6 chiều và tên danh mục |
| `bronze.mv_ins_revenue_daily` | ngày ghi nhận × đơn vị × kênh × đối tác × sản phẩm × phân khúc × vùng khách × loại giao dịch | Biểu đồ doanh thu (nhanh). Join thêm `ins_product`, `ins_product_group`, `ins_line_of_business`, `ins_company`, `ins_channel` để lấy tên |
| `bronze.mv_ins_txn_hourly` | ngày chứng từ × giờ × kênh × đơn vị cấp × loại × trạng thái (mọi trạng thái) | Vận hành: số giao dịch/ngày, heatmap theo giờ, tỷ lệ PENDING/VOID |

Sau khi nạp lại dữ liệu bằng cách khác, nhớ chạy:

```sql
REFRESH MATERIALIZED VIEW bronze.mv_ins_revenue_daily;
REFRESH MATERIALIZED VIEW bronze.mv_ins_txn_hourly;
```

Ví dụ: doanh thu theo tuần và nhóm sản phẩm.

```sql
SELECT date_trunc('week', m.accounting_date) AS tuan, pg.product_group_name, sum(m.revenue_vnd) / 1e9 AS ty_dong
FROM bronze.mv_ins_revenue_daily m
JOIN bronze.ins_product p USING (product_code)
JOIN bronze.ins_product_group pg USING (product_group_code)
GROUP BY 1, 2 ORDER BY 1, 3 DESC;
```

## Hình dạng dữ liệu (để biểu đồ có câu chuyện)

| Chiều | Đặc điểm |
|---|---|
| Thời gian | Tháng 9 cao hơn tháng 8 khoảng 1,48 lần mỗi ngày, theo phí gốc phi nhân thọ của Bộ Tài chính 2025 [CHÍNH THỨC]. Trong tháng phân bố đều, **không** có hiệu ứng cuối tháng (không có nguồn). Kênh văn phòng giảm cuối tuần và lễ 01–02/9; kênh số chạy đều [QUY ƯỚC] |
| Mùa vụ | Học sinh đỉnh quanh khai giảng 5/9 (thời điểm [QUY ƯỚC], độ lớn [ƯỚC TÍNH]). Du lịch **không** có mùa vụ riêng trong kỳ (không có nguồn Việt Nam) |
| Giờ | Kênh điện tử đỉnh 20–22h; kênh văn phòng 9–11h và 14–16h |
| Kênh | TNDS xe máy, du lịch, tai nạn 24/24 chủ yếu qua kênh điện tử (ví điện tử, nhà mạng, hãng bay, OTA). Người vay vốn và nhà tư nhân qua bancassurance. Rủi ro lớn qua trực tiếp và môi giới. ~0,5% thiếu kênh (dữ liệu bẩn có chủ đích) |
| Số đơn vs doanh thu | TNDS và du lịch chiếm phần lớn **số giao dịch** nhưng ít **doanh thu**. Cháy nổ và tài sản ít đơn nhưng chiếm khoảng 40% doanh thu |
| Trạng thái | 0,4% VOID. PENDING dồn vào 5 ngày cuối kỳ (chứng từ chưa kịp duyệt) |
| Ngày ghi nhận | Đơn không phải du lịch hiệu lực ngay ngày cấp [QUY ƯỚC]. Du lịch hiệu lực khi bắt đầu chuyến đi; số ngày mua trước lấy theo dataset Hotel booking (trung vị khoảng 70 ngày) [NGUỒN THAY THẾ], nên doanh thu du lịch rơi một phần sang tháng 10/2026 – 2028 |
| SĐBS | Tăng/giảm phí, hoàn phí, hủy; hủy chuyến du lịch trước ngày đi. Ghi nhận theo max(ngày chứng từ, ngày hiệu lực) |

**Quy mô doanh thu (từ 16/10/2026).** Cơ cấu theo BCTC kiểm toán PVI 2025 như v2: mục tiêu năm 10.377,9 tỷ × tỷ trọng tháng 8, 9 của Bộ Tài chính = khoảng 1.602 tỷ ở quy mô PVI. Để đạt > 50.000 giao dịch/ngày với đơn giá niêm yết, mọi nhóm được nhân cùng hệ số k ≈ 3,93, nên doanh thu tuyệt đối khoảng 6.300 tỷ nhưng **cơ cấu** tài sản + cháy nổ / con người / xe vẫn ≈ 51 / 31 / 17%. Bản trước (09–15/10) có cơ cấu lệch (35–40 / 38–42 / 22–24%) và doanh thu ≈ 8 lần PVI; đã thay. Chi tiết: [calibration/README.md](calibration/README.md).

## Cách chạy

Máy local không tới thẳng được `192.168.18.101`, còn các node k8s thì tới được. Có 2 cách.

**Cách 1 (nhanh): chạy trong cluster.** Pod nằm cùng mạng LAN với DB nên nạp hết khoảng 15–20 phút. Manifest ở [F:\Project\k8s\ins-datagen-pod.yaml](../../../k8s/ins-datagen-pod.yaml). Copy vào `/work` các file `gen_volume.py`, `v2/01_ddl.sql`, `v2/01b_column_comments.sql` và phần danh mục của `v2/02_data.sql`. Sau đó chạy:

```bash
pip install numpy pandas "psycopg[binary]"
PG_URI="postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi" V2_DIR=/work/v2 python gen_volume.py --reset --chunk-days 7
```

**Cách 2: qua tunnel `kubectl port-forward`.** Chậm, khoảng 0,4 MB/s, nên phù hợp để truy vấn hơn là nạp. Manifest ở [F:\Project\k8s\pg-proxy-reportapi.yaml](../../../k8s/pg-proxy-reportapi.yaml) (socat → 192.168.18.101:5432).

```bash
kubectl --kubeconfig F:/Project/k8s/kube_config.yaml -n cdc-test port-forward deploy/pg-proxy-reportapi 15432:5432
```

Sau đó kết nối DBeaver, Superset hoặc psql tới `127.0.0.1:15432`, db `reportapi`, user `report`.

**Tùy chọn**

| Tùy chọn | Tác dụng |
|---|---|
| `--dry-run` | Chỉ sinh và in thống kê |
| `--days N` | Chỉ sinh N ngày đầu |
| `--chunk-days N` | Sinh và nạp theo đợt N ngày (giới hạn RAM) |
| `--reset` | Xóa các đối tượng `ins_*`, `v_ins_*`, `mv_ins_*` trong schema đích rồi nạp lại. **Không** đụng bảng khác trong `bronze` |

Seed cố định (`SEED`), nên chạy lại cho ra cùng dữ liệu.

## Lưu ý vận hành

DB có 2 replication slot Debezium **đang không hoạt động**: `dbz_customer_tiering_eks` và `dbz_transaction_eks`. Hai slot này giữ khoảng 7,7 GB WAL mỗi slot, và `max_slot_wal_keep_size = -1`. Việc nạp bộ dữ liệu này sinh thêm vài GB WAL, cũng sẽ bị giữ lại. Ổ đĩa còn hơn 200 GB nên chưa đáng lo. Tuy vậy, nếu không còn dùng hai slot này thì nên xóa, hoặc đặt giới hạn `max_slot_wal_keep_size`.
