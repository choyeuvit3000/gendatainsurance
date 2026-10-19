# POC Doanh thu bảo hiểm: dữ liệu khối lượng lớn cho dashboard

Bộ sinh [gen_volume.py](gen_volume.py) dùng **nguyên mô hình v2** (danh mục, cột, quy tắc doanh thu: xem [DESIGN_RATIONALE.md](DESIGN_RATIONALE.md)). Điểm khác là sinh giao dịch ở **quy mô vận hành**:

- thời gian: **01/08/2026 – 30/09/2026** (61 ngày);
- mỗi ngày **> 50.000 giao dịch** (tháng 8: 57.722–69.201, bình quân 63.923; tháng 9: 62.635–77.822, bình quân 70.559), tổng 4.098.401 giao dịch;
- **doanh thu đúng quy mô Bảo hiểm PVI**, cơ cấu theo BCTC PVI (cùng tỷ trọng với v2): phí gốc khai thác tháng 8–9 là 1.600,6 tỷ so với ngân sách ≈ 1.602 tỷ. **Không còn hệ số quy mô k**;
- khối lượng > 50.000 giao dịch/ngày đến từ **bảo hiểm vi mô** theo chuyến / theo đơn (≈ 51.700 GCN/ngày, phí 1.000–2.000 đ/GCN), gần như không làm đổi doanh thu.

Số liệu chính xác sau mỗi lần nạp: xem phần "Kiểm tra sau khi nạp" trong log, `audit/run_audit.py` và [docs/db_snapshot.json](docs/db_snapshot.json) (đo bằng `measure_db.py`). Mọi con số "trên DB" trong tài liệu này lấy từ file đó; tỷ lệ là số tự tính.

Mọi tham số theo thời gian đều có nhãn căn cứ ([CHÍNH THỨC] / [NGUỒN] / [DATASET] / [NGUỒN THAY THẾ] / [QUY ƯỚC] / [ƯỚC TÍNH]), xem [calibration/README.md](calibration/README.md). Hiệu chỉnh lần gần nhất: 19/10/2026.

## Tài liệu

| File | Nội dung |
|---|---|
| [docs/POC_Doanh_thu_BH_volume.html](docs/POC_Doanh_thu_BH_volume.html) | Tài liệu tổng hợp trong 1 file: tổng quan, căn cứ tham số, căn cứ mô hình, data dictionary có ô lọc, quy tắc nghiệp vụ, mô phỏng thay đổi schema |
| [docs/Data_Dictionary_volume.xlsx](docs/Data_Dictionary_volume.xlsx) | Data dictionary Excel: mỗi bảng 1 sheet, có số dòng, % NULL, giá trị mẫu đo trên dữ liệu thật ở `reportapi` |
| [docs/db_snapshot.json](docs/db_snapshot.json) | Số đo trên DB sau lần nạp cuối (số dòng, giao dịch/ngày, doanh thu theo nhóm / kênh / phân khúc / đơn vị / sản phẩm) |
| [calibration/README.md](calibration/README.md) | Căn cứ từng tham số và nguồn |
| [audit/consistency_checks.sql](audit/consistency_checks.sql) | 41 quy tắc kiểm tra toàn vẹn nghiệp vụ |

Hai file `.html`, `.xlsx` trong `docs/` được sinh từ catalog thật của `bronze.ins_*`. Mô tả cột lấy từ `scripts/dictionary_meta.py`; các cột chỉ có ở bản này nằm trong `VOLUME_COLUMNS`. Sinh lại:

```bash
DOCS_TARGET=volume PG_URI=postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi python scripts/build_docs.py
```

## Nơi nạp

PostgreSQL `reportapi` tại `192.168.18.101:5432`, schema **`bronze`**. Mọi bảng mang tiền tố **`ins_`** để không lẫn với các bảng sẵn có (`customer_tiering`, `transaction`…).

| v2 | Trên `bronze` |
|---|---|
| `ref.<bảng>` (16 danh mục + khách hàng) | `bronze.ins_<bảng>` (ví dụ `bronze.ins_product`, `bronze.ins_customer`) |
| `core.policy`, `core.policy_transaction`, `core.transaction_coverage`, `core.coinsurance_share`, `core.revenue_allocation` | `bronze.ins_policy`, `bronze.ins_policy_transaction`, `bronze.ins_transaction_coverage`, `bronze.ins_coinsurance_share`, `bronze.ins_revenue_allocation` |
| (mới) view doanh thu | `bronze.v_ins_revenue_line`, `bronze.mv_ins_revenue_daily`, `bronze.mv_ins_txn_hourly` |
| (mới) mốc khóa đã phát hành | `bronze.poc_key_watermark` (xem "Khóa không lặp") |

Ngoài v2 có thêm 3 cột: `ins_customer.gender`, `ins_customer.birth_year`, `ins_policy.prev_policy_no`. Cột `prev_policy_no` là số hợp đồng năm trước được tái tục; hợp đồng đó nằm ngoài kỳ dữ liệu nên lưu dạng text.

Muốn đổi đích thì đặt biến `TARGET_SCHEMA` và `TABLE_PREFIX`.

## Doanh nghiệp, đơn vị, đối tác

- **Doanh nghiệp:** Tổng Công ty Bảo hiểm PVI (`PVI`, PVI Insurance), công ty con 100% của CTCP PVI (PVI Holdings) — BCTN 2024, trang PDF 12. Không còn doanh nghiệp giả lập "DEMO".
- **Đơn vị (`ins_company`):** Trụ sở chính – các Ban kinh doanh (`HO`), Bảo hiểm PVI Digital (`DGT`, TP.HCM) và 46 đơn vị thật theo trang mạng lưới (DGT + 46 = 47 đơn vị trên trang) pvi.com.vn (Đông Đô, Thăng Long, Hà Nội, …, Phía Nam). Tỉnh của đơn vị = địa chỉ trụ sở trên trang mạng lưới.
- **Trọng số khai thác của đơn vị là [ƯỚC TÍNH]:** PVI không công bố doanh thu từng đơn vị, nên trọng số theo quy mô kinh tế địa bàn, ×1,5 cho 5 đơn vị được PVI vinh danh hoặc tự công bố dẫn đầu: Phía Nam (xuất sắc nhất 2024), Thủ Đô (6 tháng 2025), Duyên Hải (xuất sắc nhất 2025), Thăng Long (hoàn thành sớm kế hoạch 2025), Sài Gòn (doanh thu đứng đầu hệ thống bán lẻ, pvisg.net). Doanh thu theo đơn vị trên DB vì vậy là số giả lập, không phải số của PVI.
- **Không có trong `ins_company`:** Hanoi Re (tên cũ PVI Re, nhận tái bảo hiểm) và PVIAM (quản lý quỹ) là công ty con khác của Holdings, không cấp hợp đồng bảo hiểm gốc nên ngoài phạm vi doanh thu phí gốc.
- **Đối tác:** đối tác cũ vẫn ẩn danh (Ngân hàng A, OTA A…). 3 đối tác số thật mới, có công bố hợp tác với PVI: `GREEN_SM` (nền tảng di chuyển), `ATADI` (OTA vé máy bay), `FUSE` (insurtech trên Shopee / Lazada); số giao dịch qua họ là giả lập.
- **Vì sao không có Grab:** bảo hiểm chuyến đi của Grab (Ride Cover) do **Chubb** cung cấp, của Be do **OPES**. Hợp tác Grab × PVI năm 2026 là BHXH/BHYT tự nguyện cho tài xế, không phải bảo hiểm theo cuốc. Vì vậy POC dùng Green SM.

## Quy ước NULL và tham chiếu danh mục

Lớp `bronze` mô phỏng **hệ thống nguồn**, nên giữ NULL đúng nghiệp vụ. Mọi mã khác NULL đều có khóa ngoại đã kiểm chứng.

| Cột | NULL khi | Bản chất |
|---|---|---|
| `ins_policy.partner_code` | Kênh không qua đối tác: trực tiếp, đại lý cá nhân, đấu thầu, web/app công ty (kênh điện tử không có đối tác) | Hợp lệ (không áp dụng) |
| `ins_policy.channel_code` | ~0,5% hợp đồng truyền thống nguồn không khai báo kênh (= 0,11% tổng hợp đồng). GCN vi mô cấp qua API đối tác luôn có kênh | Lỗi dữ liệu có chủ đích |
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

Kiểm tra toàn bộ ràng buộc nghiệp vụ (41 quy tắc: hợp đồng, khách hàng, giao dịch, dòng phí, đồng bảo hiểm, phân bổ, tham chiếu). Lần nạp cuối: **41 quy tắc, 0 vi phạm** (I01 chỉ là thông tin: 0,11% kênh NULL có chủ đích).

```bash
PG_URI=postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi python audit/run_audit.py
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

**Lưu ý với bảo hiểm vi mô:** GCN vi mô (`product_code LIKE 'MV_%'`) chiếm 77% số hợp đồng nhưng 1,3% doanh thu. Nên tách "số giao dịch" và "doanh thu" thành hai thước đo, và lọc riêng `MV_*` khi tính phí bình quân, phân vị phí hoặc tỷ trọng số đơn theo nhóm.

## Hình dạng dữ liệu (để biểu đồ có câu chuyện)

| Chiều | Đặc điểm |
|---|---|
| Thời gian | Doanh thu tháng 9 cao hơn tháng 8 khoảng 1,48 lần mỗi ngày theo ngân sách, theo phí gốc phi nhân thọ của Bộ Tài chính 2025 [CHÍNH THỨC]; trên DB doanh thu ghi nhận 639,2 tỷ (tháng 8) và 938,7 tỷ (tháng 9), ≈ ×1,52 mỗi ngày (đã tính). Số **giao dịch**/ngày chỉ chênh ≈ ×1,10 vì phần lớn là GCN vi mô. Trong tháng phân bố đều, **không** có hiệu ứng cuối tháng (không có nguồn). Kênh văn phòng giảm cuối tuần và lễ 01–02/9; kênh số chạy đều [QUY ƯỚC] |
| Mùa vụ | Học sinh đỉnh quanh khai giảng 5/9 (thời điểm [QUY ƯỚC], độ lớn [ƯỚC TÍNH]). Du lịch **không** có mùa vụ riêng trong kỳ (không có nguồn Việt Nam). Thiết bị điện tử ×3 vào 8/8, 9/9; DelayCare chỉ có từ 20/8 [ƯỚC TÍNH] |
| Giờ | Kênh điện tử đỉnh 20–22h; kênh văn phòng 9–11h và 14–16h. Vi mô: chuyến xe 7–8h và 17–19h; đồ ăn 11–12h và 18–19h [ƯỚC TÍNH] |
| Kênh | TNDS xe máy, du lịch, tai nạn 24/24 chủ yếu qua kênh điện tử (ví điện tử, nhà mạng, hãng bay, OTA). GCN vi mô 100% kênh điện tử qua Green SM, ATADI, Fuse. Người vay vốn và nhà tư nhân qua bancassurance. Rủi ro lớn qua trực tiếp và môi giới. Doanh thu: trực tiếp 30,4% · đại lý cá nhân 24,8% · môi giới 15,1% · bancassurance 12,5% · điện tử 8,0% · đại lý tổ chức 6,1% · đấu thầu 2,7% · thiếu kênh 0,4% |
| Số đơn vs doanh thu | GCN vi mô: 77,3% số hợp đồng, 1,3% doanh thu. Cháy nổ: 0,14% số hợp đồng nhưng 33,7% doanh thu; cháy nổ + tài sản ≈ 52%. 10% hợp đồng lớn nhất chiếm 97,7% doanh thu, 1% lớn nhất chiếm 80,1% |
| Phân khúc | Doanh nghiệp trong nước 38,7% doanh thu với 0,5% số hợp đồng; cá nhân 35,5% với 97,2%; FDI 11,3%; hộ gia đình 7,0%; cơ quan nhà nước 4,3%; cơ sở giáo dục 2,2%; khách lẻ theo bảng kê 1,1% |
| Đơn vị | Doanh thu phân bổ lớn nhất: Duyên Hải 127,3 tỷ (8,1%), Trụ sở chính 101,8 (6,5%), Thống Nhất 74,9, Hà Nội 56,3, PVI Digital 55,7 tỷ — số giả lập theo trọng số [ƯỚC TÍNH] |
| Trạng thái | 0,40% VOID; 0,85% PENDING, dồn vào 5 ngày cuối kỳ (chứng từ chưa kịp duyệt) |
| Ngày ghi nhận | Đơn không phải du lịch hiệu lực ngay ngày cấp [QUY ƯỚC]. Du lịch hiệu lực khi bắt đầu chuyến đi; số ngày mua trước lấy theo dataset Hotel booking (trung vị khoảng 70 ngày) [NGUỒN THAY THẾ], nên doanh thu du lịch rơi một phần sang tháng 10/2026 – 2028 (16,7 tỷ ghi nhận sau 30/9) |
| SĐBS | Tăng/giảm phí, hoàn phí, hủy; hủy chuyến du lịch trước ngày đi; hủy DelayCare trước ngày bay, hủy bảo hiểm thiết bị khi trả hàng. Ghi nhận theo max(ngày chứng từ, ngày hiệu lực) |

## Quy mô và phân phối doanh thu khi có bảo hiểm vi mô

**Quy mô (từ 19/10/2026).** Cơ cấu theo BCTC kiểm toán PVI 2025 như v2: mục tiêu năm 10.377,9 tỷ × tỷ trọng tháng 8, 9 của Bộ Tài chính (13.594 / 88.054) ≈ 1.602 tỷ. Ngân sách này dùng nguyên, không nhân hệ số. Trên DB, phí gốc khai thác (cấp mới + tái tục đã duyệt) là **1.600,6 tỷ**; cơ cấu tài sản + cháy nổ / con người / xe = 51,5 / 31,0 / 17,5% (đã tính). Doanh thu ghi nhận tháng 8–9 là 1.577,9 tỷ (16,7 tỷ du lịch ghi nhận sau 30/9; khoản giảm thu −5,8 tỷ).

Bản 16–18/10 nhân mọi nhóm với một hệ số quy mô để đạt > 50.000 giao dịch/ngày, nên doanh thu ≈ 4 lần PVI, và dùng tỷ trọng sản phẩm lệch v2 (tai nạn 24/24 0,40 thay vì 0,20…). Cả hai đã bỏ; tỷ trọng sản phẩm trong nhóm nay lấy thẳng `build_v2.PRODUCT_MIX`. Chi tiết: [calibration/README.md](calibration/README.md).

**Phân phối** (số đo khóa `product`, `policies_group`, `top_share`; tỷ lệ, phí bình quân là số tự tính; doanh thu = ghi nhận tháng 8–9):

| Phần | Số hợp đồng / GCN | % số HĐ | Doanh thu (tỷ) | % doanh thu | Phí bình quân |
|---|---:|---:|---:|---:|---:|
| `MV_XSM_CARE` (Green SM Care) | 2.431.497 | 59,6% | 3,36 | 0,21% | 1.383 đ |
| `MV_FOOD_CARE` (Food Care) | 516.750 | 12,7% | 0,51 | 0,03% | 988 đ |
| `MV_TBDT_TMDT` (thiết bị điện tử TMĐT) | 194.993 | 4,8% | 16,35 | 1,04% | 83.837 đ |
| `MV_DELAYCARE` (từ 20/8) | 12.749 | 0,3% | 0,62 | 0,04% | 48.739 đ/GCN (1–4 người × 35.000 đ) |
| **Vi mô** | **3.155.989** | **77,3%** | **20,84** | **1,32%** | |
| **Truyền thống** | **926.648** | **22,7%** | **1.557,0** | **98,68%** | ≈ 1,68 triệu đ |
| **Tổng** | **4.082.637** | 100% | **1.577,9** | 100% | |

Vì sao tổng doanh thu không đổi khi thêm vi mô: doanh thu vi mô nằm **trong** ngân sách nhóm (sinh mạng, du lịch, tài sản). Bước hiệu chỉnh coi dòng vi mô là cố định và co giãn đơn doanh nghiệp / nhóm ở phần còn lại, nên tổng từng nhóm và cơ cấu ≈ 51 / 31 / 17% giữ nguyên. Phân phối "nhiều đơn nhỏ – ít đơn lớn" vì vậy lệch hơn v2: 10% hợp đồng lớn nhất chiếm 97,7% doanh thu, 1% lớn nhất 80,1% (v2 năm 2025: 74% / 25%). Nhóm sinh mạng có 3.298.699 hợp đồng (chủ yếu vi mô) nhưng chỉ ≈ 74 tỷ phí gốc. Đây là đặc trưng thật của bảo hiểm nhúng (OPES phát hành 109,3 triệu hợp đồng năm 2023).

## Kết quả lần nạp cuối (19/10/2026)

| Chỉ số | Giá trị trên DB |
|---|---|
| Số dòng | `ins_policy` 4.082.637 · `ins_policy_transaction` 4.098.401 · `ins_transaction_coverage` 4.127.680 · `ins_coinsurance_share` 4.082.967 · `ins_revenue_allocation` 4.152.252 · `ins_customer` 1.696.375 |
| Dải khóa | `policy_id` 60.000.001–64.082.637, `txn_id` 60.000.001–64.098.401, `coverage_id` 60.000.001–64.127.680; mã khách `KH610000001`–`KH690000048` |
| Giao dịch/ngày | Tháng 8: 57.722–69.201 (bình quân 63.923); tháng 9: 62.635–77.822 (bình quân 70.559) |
| Loại giao dịch | Cấp mới 3.909.726 · tái tục 172.911 · hủy 7.259 · SĐBS không đổi phí 3.427 · tăng phí 2.597 · giảm phí 1.336 · hoàn phí 1.145 |
| Trạng thái | APPROVED 4.047.266 · PENDING 34.744 · VOID 16.391 |
| Phí gốc khai thác T8 + T9 | 1.600,6 tỷ (ngân sách ≈ 1.602 tỷ) |
| Doanh thu ghi nhận | Tháng 8: 639,2 tỷ · tháng 9: 938,7 tỷ · tổng 1.577,9 tỷ |
| Audit | 41 quy tắc, 0 vi phạm |

## Khóa không lặp

Dữ liệu có CDC (Debezium) và Iceberg phía sau, nên khóa đã xóa **không được dùng lại**:
- Với `--replace`, bộ sinh đọc khóa lớn nhất đang có **trước khi xóa** rồi bắt đầu sau đó (làm tròn lên): `policy_id`, `txn_id`, `coverage_id` từ bội số 10 triệu kế tiếp; số hợp đồng từ bội số 1 triệu kế tiếp theo từng đơn vị × sản phẩm; mã khách từ bội số 100 triệu kế tiếp.
- Bảng **`bronze.poc_key_watermark`** (`key_name`, `max_value`) lưu mốc khóa lớn nhất đã phát hành, ghi sau mỗi đợt nạp và không bao giờ bị DELETE. Dù bảng fact trống hoặc lần trước nạp dở, lần sau vẫn bắt đầu sau mọi khóa cũ.
- Lần nạp cuối: `policy_id` 60.000.001–64.082.637, `txn_id` 60.000.001–64.098.401, `coverage_id` 60.000.001–64.127.680, mã khách `KH610000001`–`KH690000048`. Các dải 30 triệu (cũ), 40 và 50 triệu (2 lần nạp trung gian ngày 19/10) đều đã xóa.
- `--replace` **đồng bộ danh mục** với `02_data.sql`: upsert theo khóa chính, xóa dòng không còn dùng (DEMO, HN1…), dòng không đổi giữ nguyên để CDC không phát sự kiện thừa.

## Cách chạy

Kết nối mặc định là **trực tiếp** tới DB, không cần pod hay port-forward:

```
postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi
```

```bash
pip install numpy pandas "psycopg[binary]"
# lần nạp đầu (tạo bảng)
PG_URI="postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi" python gen_volume.py --reset --chunk-days 7
# các lần sau (giữ bảng + publication CDC, khóa mới không trùng khóa cũ)
PG_URI="postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi" python gen_volume.py --replace --chunk-days 7
# đo lại số liệu cho tài liệu
PG_URI="postgresql://report:<mật khẩu>@192.168.18.101:5432/reportapi" python measure_db.py
```

DBeaver, Superset hoặc psql cũng kết nối thẳng `192.168.18.101:5432`, db `reportapi`, user `report`.

Dự phòng khi máy không tới thẳng được `192.168.18.101`: chạy trong cluster bằng [F:\Project\k8s\ins-datagen-pod.yaml](../../../k8s/ins-datagen-pod.yaml), hoặc mở tunnel bằng [F:\Project\k8s\pg-proxy-reportapi.yaml](../../../k8s/pg-proxy-reportapi.yaml) (`kubectl port-forward … 15432:5432`, khá chậm).

**Tùy chọn**

| Tùy chọn | Tác dụng |
|---|---|
| `--dry-run` | Chỉ sinh và in thống kê |
| `--local` | Nạp vào PostgreSQL nhúng (pgserver) để chạy thử |
| `--days N` | Chỉ sinh N ngày đầu |
| `--chunk-days N` | Sinh và nạp theo đợt N ngày (giới hạn RAM) |
| `--reset` | Xóa các đối tượng `ins_*`, `v_ins_*`, `mv_ins_*` trong schema đích rồi nạp lại. **Không** đụng bảng khác trong `bronze` (kể cả `poc_key_watermark`). Khóa bắt đầu lại từ đầu, nên chỉ dùng cho lần nạp đầu |
| `--replace` | Giữ bảng, publication CDC; DELETE dữ liệu fact + khách hàng, đồng bộ danh mục, nạp lại với khóa mới sau mốc trong `poc_key_watermark` |

Seed cố định (`SEED`), nên chạy lại cho ra cùng dữ liệu (khác nhau ở dải khóa).

## Nguồn mới (19/10/2026): đơn vị PVI và bảo hiểm vi mô

**Phương pháp:** nghiên cứu chéo bằng codex CLI (gpt-6.1-sol) và agy CLI (gemini-3.8-flash-high) với cùng một đề bài, đối chiếu kết quả hai bên; mọi link đã kiểm lại bằng curl ngày 19/10/2026. Mục bị loại: danh sách "7 đơn vị về đích sớm" (agy) không kiểm chứng được. Bản gốc: [sources/market_data.md](sources/market_data.md) mục 9, 10.

| Nội dung dùng | Số liệu | Nhãn | URL (trang) |
|---|---|---|---|
| Tổng Công ty Bảo hiểm PVI là công ty con 100% của CTCP PVI (PVI Holdings) | 100% tại 31/12/2024 | [NGUỒN] | BCTN PVI 2024, trang PDF 12: https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf |
| Các công ty con khác của Holdings; doanh thu 2024 | Hanoi Re 81,09%, PVIAM 61,96%; Holdings 21.824 tỷ, PVI Insurance 20.405 tỷ, Hanoi Re 3.017,3 tỷ, PVIAM 57,4 tỷ | [NGUỒN] | BCTN PVI 2024, trang PDF 12, 22, 29, 30, 31 (link trên) |
| Hanoi Re là tên mới của PVI Re | — | [NGUỒN] | https://www.hanoire.com/vi/pvi-re-chinh-thuc-doi-ten-thanh-hanoi-re |
| Doanh thu 2025 của Holdings và các công ty con | Holdings 28.923 tỷ; Bảo hiểm PVI 27.258 tỷ (phí gốc 14.908 tỷ); Hanoi Re 3.690 tỷ; PVIAM 76,4 tỷ | [NGUỒN] (tỷ lệ 94,2% là số tự tính) | BCTN PVI 2025, trang PDF 29, 32, 33, 34: https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf |
| Danh sách đơn vị, địa chỉ trụ sở → tỉnh của đơn vị | 47 đơn vị: PVI Digital + 45 công ty thành viên + Phía Nam | [NGUỒN] | https://www.pvi.com.vn/vi/network |
| Bảo hiểm PVI Digital là chi nhánh của Tổng Công ty | — | [NGUỒN] | https://online.pvi.com.vn/lien-he |
| PVI Sài Gòn tự công bố doanh thu đứng đầu hệ thống bán lẻ | — | [NGUỒN] | https://pvisg.net |
| Đơn vị được vinh danh: Phía Nam (xuất sắc nhất 2024); Thủ Đô (6 tháng 2025); Duyên Hải (2025); Thủ Đô, Thăng Long hoàn thành sớm kế hoạch 2025 | Hệ số ×1,5 suy ra từ đây là **[ƯỚC TÍNH]** | [NGUỒN] | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-mot-nam-vuot-song-chinh-phuc-nhung-cot-moc-moi-681b4f9737783 ; https://www.pvi.com.vn/en/news/bao-hiem-pvi-doi-moi-sang-tao-va-thanh-cong ; https://vnexpress.net/nhung-yeu-to-giup-doanh-thu-bao-hiem-pvi-vuot-1-ty-usd-5011267.html ; https://www.pvi.com.vn/vi/news/pvi-thu-do-va-pvi-thang-long-hai-don-vi-tiep-theo-duoc-vinh-danh-hoan-thanh-som-ke-hoach-kinh-doanh-nam-2025 |
| Green SM Care: tai nạn hành khách theo chuyến; PVI Digital là 1 trong 5 nhà bảo hiểm (PVI Digital, OPES, BIC, TCGI, MIC) | 1.000 đ/chuyến Bike, 2.000 đ/chuyến Taxi | [NGUỒN] | https://www.greensm.com/vn-vi/bao-hiem-khach-hang ; https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Food Care: Green SM × Bảo hiểm PVI, theo đơn giao đồ ăn | 1.000 đ/đơn; tai nạn 150 triệu đ/đơn | [NGUỒN] | https://www.greensm.com/vn-vi/bao-hiem-giao-do-an |
| DelayCare: PVI × ATADI, ra mắt 20/08/2026, đơn vị cung cấp PVI Thủ Đô | Trễ ≥ 120 phút trả 500.000 đ/người; phí KHÔNG TÌM THẤY → 35.000 đ là [ƯỚC TÍNH] | [NGUỒN] | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-ra-mat-delaycare-giai-phap-bao-hiem-tre-chuyen-bay-danh-cho-hanh-khach |
| Bảo hiểm thiết bị điện tử khi mua trên Shopee / Lazada (PVI qua Fuse, PasarPolis) | Ví dụ 38.102 đ/12 tháng (nguồn thứ cấp) | [NGUỒN] | https://help.shopee.vn/portal/4/article/79225 ; https://magiamgia.com/bao-hiem-thiet-bi-dien-tu-lazada/ |
| Đối tác số của PVI Digital (MoMo, Viettel Money, Shopee, Lazada, FE Credit, Home Credit, Xanh SM, Grab, Trip.com, Thế Giới Di Động, Điện Máy Xanh) | "hàng triệu khách hàng" | [NGUỒN] | https://www.pvi.com.vn/vi/news/pvi-digital-doi-tac-bao-hiem-so-cua-cac-nen-tang-va-he-sinh-thai-so-hang-dau-viet-nam |
| Quy mô Green SM | > 1 triệu chuyến/ngày (2025, nguồn thứ cấp) | [NGUỒN] | https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam |
| Tham chiếu sản lượng vi mô ở Việt Nam (OPES) | 109,3 triệu hợp đồng năm 2023; cao điểm > 500.000 đơn/ngày | [NGUỒN] | https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154 |
| TMĐT của Bảo hiểm PVI | Gần 800 tỷ năm 2024 (30 kết nối API); 2025 gần gấp đôi | [NGUỒN] | BCTN 2024 trang PDF 29 (link trên); https://pviholdings.com.vn/vi/news-details?id=6013 |
| Bảo hiểm chuyến đi của Grab do Chubb, của Be do OPES | — | [NGUỒN] | https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Grab × PVI 2026 là BHXH/BHYT tự nguyện cho tài xế | — | [NGUỒN] | https://www.grab.com/vn/blog/driver/bhxh-bhyt-pvi/ |

**[ƯỚC TÍNH]** (không có số công bố; căn cứ chi tiết ở [calibration/README.md](calibration/README.md)): số GCN vi mô/ngày (40.000 chuyến xe = 1 triệu chuyến × 20% mua × 20% về PVI; 8.000 đồ ăn; 300 DelayCare; 3.000 thiết bị điện tử), phí DelayCare 35.000 đ/người, phí thiết bị điện tử 1,5–3,5% giá máy, trọng số khai thác từng đơn vị.

## Lưu ý vận hành

DB có 2 replication slot Debezium **đang không hoạt động**: `dbz_customer_tiering_eks` và `dbz_transaction_eks`. Hai slot này giữ khoảng 7,7 GB WAL mỗi slot, và `max_slot_wal_keep_size = -1`. Việc nạp bộ dữ liệu này sinh thêm vài GB WAL, cũng sẽ bị giữ lại. Ổ đĩa còn hơn 200 GB nên chưa đáng lo. Tuy vậy, nếu không còn dùng hai slot này thì nên xóa, hoặc đặt giới hạn `max_slot_wal_keep_size`.
