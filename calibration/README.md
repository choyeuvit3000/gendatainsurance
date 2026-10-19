# Căn cứ tham số của bộ sinh dữ liệu khối lượng lớn

`build_calibration.py` rút **thống kê tổng hợp** (phân vị, tỷ lệ) từ nguồn công khai ra file `calibration.json`. `gen_volume.py` đọc file này khi sinh dữ liệu. Thư mục này không lưu dữ liệu gốc của các dataset.

Chạy lại sau khi tải 2 file CSV về thư mục tạm:

```bash
python -I build_calibration.py <travel_insurance.csv> <hotels.csv> calibration.json
```

## Nhãn căn cứ

| Nhãn | Nghĩa |
|---|---|
| **[CHÍNH THỨC]** | Số liệu cơ quan nhà nước hoặc văn bản pháp luật công bố |
| **[NGUỒN]** | Thông tin công khai của doanh nghiệp / đối tác (BCTC, báo cáo thường niên, website, báo chí), có URL kiểm lại được |
| **[DATASET]** | Dataset công khai có dữ liệu thật, đúng lĩnh vực bảo hiểm |
| **[NGUỒN THAY THẾ]** | Dataset công khai có bình duyệt nhưng thuộc lĩnh vực lân cận, dùng thay khi không có dữ liệu bảo hiểm |
| **[QUY ƯỚC]** | Quy tắc cấu trúc (lịch làm việc, lịch năm học), không phải số liệu đo được |
| **[ƯỚC TÍNH]** | Giá trị dự án tự đặt, chưa có nguồn; luôn ghi kèm căn cứ |

## Quy mô doanh thu (hiệu chỉnh lại 19/10/2026 — đúng quy mô PVI, không còn hệ số k)

Bộ volume dùng **cùng cơ cấu doanh thu với v2** (tỷ trọng giữa các nhóm và trong từng nhóm), thu về kỳ tháng 8–9, và **đúng quy mô tuyệt đối của Bảo hiểm PVI**. Yêu cầu dự án là **> 50.000 giao dịch/ngày**; ở quy mô PVI với giá niêm yết, nghiệp vụ truyền thống chỉ được khoảng 15 nghìn hợp đồng/ngày, nên khối lượng còn lại đến từ **bảo hiểm vi mô theo chuyến / theo đơn** (phí 1.000–2.000 đ/GCN, xem mục "Bảo hiểm vi mô"). Mỗi GCN vi mô gần như không làm đổi doanh thu, nên không cần nhân ngân sách.

> Bản 16–18/10/2026 nhân mọi ngân sách nhóm với hệ số quy mô k ≈ 3,93 để đạt khối lượng, nên doanh thu ≈ 4 lần PVI. Bản đó cũng dùng tỷ trọng sản phẩm riêng, lệch v2 (tai nạn 24/24 0,40 thay vì 0,20; TNDS xe máy 0,65 thay vì 0,45; nhà tư nhân 0,20 thay vì 0,45…), khiến sinh mạng chiếm 49,9% số hợp đồng. Cả hai đã bỏ.

| Bước | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Mục tiêu năm theo nhóm sản phẩm | Tổng 10.377,9 tỷ: sức khỏe 2.410,1 · sinh mạng 482,0 · du lịch 160,7 · học sinh 160,7 · TNDS 437,4 · vật chất xe 1.385,3 · cháy nổ 3.451,2 · tài sản 1.890,6 | [CHÍNH THỨC] + tỷ lệ chia [ƯỚC TÍNH] | BCTC kiểm toán 2025 Bảo hiểm PVI, thuyết minh 21 (trang 45 của PDF); tỷ lệ chia như v2 (Con người 75/15/5/5, Xe 24/76 theo IAV, tài sản thuần 50%) |
| Tỷ trọng tháng 8, 9 | 5.592 / 88.054 = 6,35% · 8.002 / 88.054 = 9,09% | [CHÍNH THỨC] | Bộ Tài chính: phí gốc phi nhân thọ toàn thị trường 2025 theo tháng và cả năm (bản tin 01/2026). Giả định PVI có mùa vụ tháng giống thị trường [ƯỚC TÍNH] |
| Năm 2026 | Dùng quy mô 2025 | [QUY ƯỚC] | Chưa có BCTC 2026 |
| **Ngân sách tháng 8 + 9** | **≈ 1.602 tỷ** (tháng 8 ≈ 659, tháng 9 ≈ 943) — dùng nguyên, **không nhân hệ số** | — | = mục tiêu năm × tỷ trọng tháng (10.377,9 × 13.594 / 88.054) |
| Khối lượng > 50.000 giao dịch/ngày | ≈ 51.700 GCN vi mô/ngày + ≈ 15.200 hợp đồng truyền thống/ngày | [ƯỚC TÍNH] (số GCN vi mô) | Mục "Bảo hiểm vi mô" bên dưới |
| Tỷ trọng doanh thu của sản phẩm trong nhóm | **Lấy thẳng `build_v2.PRODUCT_MIX`** (một nguồn duy nhất): TNDS ô tô 55 / xe máy 45; VCX ô tô 85 / xe máy 15; học sinh tai nạn 60 / sức khỏe 40; du lịch nội địa 55 / quốc tế 45; sinh mạng CN 35 / người vay 45 / TN24 20; sức khỏe CN 45 / nhóm 45 / BHN 10; nhà 45 / MRR 35 / MRR CN 20; cháy nổ BB 70 / TN 30 | [ƯỚC TÍNH] | PVI không công bố |
| Số hợp đồng | = ngân sách × tỷ trọng ÷ phí bình quân của sản phẩm (đo bằng mô phỏng đơn giá). Riêng vi mô: số GCN theo ngày (mục dưới) | — | Đơn giá theo biểu phí NĐ 67/2023 và giá niêm yết, như v2 |
| Hiệu chỉnh | Đơn bán lẻ giữ nguyên giá; **dòng vi mô coi là cố định**; co giãn đơn doanh nghiệp / nhóm / lô để doanh thu từng nhóm khớp ngân sách mỗi đợt 7 ngày | — | Cùng thuật toán với v2 |

**Hệ quả (đo trên DB, `docs/db_snapshot.json`, 19/10/2026):**

| Nhóm | Ngân sách T8+T9 (tỷ) | Phí gốc khai thác trên DB (tỷ) | Lệch | Số hợp đồng |
|---|---:|---:|---:|---:|
| Sức khỏe | 372,1 | 372,0 | 0,0% | 44.924 |
| Sinh mạng – tai nạn (gồm vi mô) | 74,4 | 74,4 | 0,0% | 3.298.699 |
| Du lịch (gồm DelayCare) | 24,8 | 24,8 | +0,1% | 134.525 |
| Học sinh | 24,8 | 24,8 | 0,0% | 21.751 |
| TNDS bắt buộc | 67,5 | 67,5 | 0,0% | 216.322 |
| Vật chất xe | 213,9 | 212,3 | −0,7% | 42.346 |
| Cháy nổ | 532,8 | 532,8 | 0,0% | 5.542 |
| Tài sản (gồm thiết bị điện tử) | 291,9 | 291,9 | 0,0% | 318.528 |
| **Tổng** | **1.602,2** | **1.600,6** | **−0,1%** | **4.082.637** |

Phí gốc khai thác = phí cấp mới + tái tục đã duyệt, phần của công ty, theo ngày chứng từ (khóa `written_group`); ngân sách và cột "Lệch" là số tự tính. Cơ cấu tài sản + cháy nổ / con người / xe = 51,5 / 31,0 / 17,5% (đã tính), khớp BCTC PVI như v2. Giao dịch/ngày: tháng 8 57.722–69.201 (bình quân 63.923), tháng 9 62.635–77.822 (bình quân 70.559); tổng 4.098.401 giao dịch.

## Bảo hiểm vi mô (bổ sung 19/10/2026)

4 sản phẩm mới trong `ref.product`, thuộc các nhóm sẵn có, nên doanh thu của chúng nằm **trong** ngân sách nhóm (`gen_volume.MICRO`, `MICRO_ISSUER`, `MICRO_PARTNER`).

| Mã | Sản phẩm | Nhóm | Phí / GCN | Số GCN/ngày | Đơn vị cấp | Đối tác |
|---|---|---|---|---:|---|---|
| `MV_XSM_CARE` | BH tai nạn hành khách theo chuyến (Green SM Care) | Sinh mạng – tai nạn | 1.000 đ Bike / 2.000 đ Taxi **[NGUỒN]** greensm.com; tỷ lệ Bike/Taxi 60/40 [ƯỚC TÍNH] | 40.000 **[ƯỚC TÍNH]**: Green SM > 1 triệu chuyến/ngày × 20% chuyến mua bảo hiểm × 20% về PVI (PVI Digital là 1 trong 5 nhà bảo hiểm của chương trình) | DGT (PVI Digital) | `GREEN_SM` |
| `MV_FOOD_CARE` | BH đơn giao đồ ăn (Food Care) | Sinh mạng – tai nạn | 1.000 đ/đơn **[NGUỒN]** greensm.com | 8.000 **[ƯỚC TÍNH]**: Green SM không công bố số đơn giao đồ ăn; giá trị quy ước của POC | DGT | `GREEN_SM` |
| `MV_DELAYCARE` | BH trễ chuyến bay (DelayCare), từ 20/08/2026 | Du lịch | 35.000 đ/người **[ƯỚC TÍNH]**: ≈ 4% xác suất trễ ≥ 2 giờ × 500.000 đ ÷ tỷ lệ bồi thường 60% (phí không công bố; mức chi trả 500.000 đ là [NGUỒN] pvi.com.vn) | 300 **[ƯỚC TÍNH]**: số GCN không công bố; giá trị quy ước của POC, chỉ từ 20/08/2026 | TDO (PVI Thủ Đô — nguồn ghi là đơn vị cung cấp) | `ATADI` |
| `MV_TBDT_TMDT` | BH thiết bị điện tử mua trên sàn TMĐT | Tài sản | 1,5–3,5% giá máy **[ƯỚC TÍNH]**, neo ví dụ 38.102 đ/12 tháng (help.shopee.vn, nguồn thứ cấp) | 3.000; ×3 ngày 8/8, 9/9 **[ƯỚC TÍNH]**: số GCN không công bố; giá trị quy ước của POC (đối chiếu độ hợp lý với kênh TMĐT PVI gần 800 tỷ năm 2024, 2025 gần gấp đôi) | DGT | `FUSE` |

Các số GCN/ngày là quy ước để đạt khối lượng giao dịch của POC, đã kiểm tra độ hợp lý với quy mô Green SM (> 1 triệu chuyến/ngày) và OPES (109,3 triệu hợp đồng năm 2023, cao điểm > 500.000 đơn/ngày).

Quy tắc riêng của GCN vi mô:
- Kênh luôn là `DIEN_TU`, đối tác như bảng (cấp tự động qua API nên **không** thuộc nhóm ~0,5% thiếu kênh).
- Khách là người dùng app: kho riêng 1,5 triệu người, mã khách mang tiền tố 7 (ví dụ `KH67…` ở lần nạp này); 40% GCN đến từ nhóm 150 nghìn người dùng thường xuyên (đi làm, đặt đồ ăn hằng ngày) [ƯỚC TÍNH].
- Phân bổ 100% cho đơn vị cấp (`TU_KHAI_THAC`), không hợp tác / chuyển giao.
- GCN chuyến xe và đồ ăn hiệu lực trong ngày, không có SĐBS. DelayCare hủy 3% trước ngày bay; thiết bị điện tử hủy 2% khi trả hàng [ƯỚC TÍNH].
- Giờ tạo [ƯỚC TÍNH]: chuyến xe cao điểm 7–8h và 17–19h; đồ ăn 11–12h và 18–19h. Chuyến xe ít hơn vào chủ nhật; đồ ăn nhiều hơn cuối tuần và lễ.

**Vì sao Grab không phải đối tác:** bảo hiểm chuyến đi của Grab (Ride Cover) do **Chubb** cung cấp, của Be do **OPES** — không phải PVI. Hợp tác Grab × PVI năm 2026 là chương trình BHXH/BHYT tự nguyện cho tài xế, không phải bảo hiểm theo cuốc. Vì vậy POC dùng **Green SM**, nơi PVI Digital có tên trong danh sách nhà bảo hiểm.

## Phân phối và quy mô doanh thu khi có bảo hiểm vi mô

Số đo trên DB (`docs/db_snapshot.json`, khóa `product`, `written_group`, `policies_group`, `top_share`); tỷ lệ và phí bình quân là số tự tính. Doanh thu = doanh thu ghi nhận tháng 8–9 theo sản phẩm (tổng 1.577,9 tỷ).

| Phần | Số hợp đồng / GCN | % số HĐ | Doanh thu (tỷ) | % doanh thu | Phí bình quân |
|---|---:|---:|---:|---:|---:|
| `MV_XSM_CARE` | 2.431.497 | 59,6% | 3,36 | 0,21% | 1.383 đ |
| `MV_FOOD_CARE` | 516.750 | 12,7% | 0,51 | 0,03% | 988 đ |
| `MV_TBDT_TMDT` | 194.993 | 4,8% | 16,35 | 1,04% | 83.837 đ |
| `MV_DELAYCARE` (từ 20/8) | 12.749 | 0,3% | 0,62 | 0,04% | 48.739 đ/GCN (1–4 người × 35.000 đ) |
| **Vi mô** | **3.155.989** | **77,3%** | **20,84** | **1,32%** | ≈ 6.600 đ |
| **Truyền thống** | **926.648** | **22,7%** | **1.557,0** | **98,68%** | ≈ 1,68 triệu đ |
| **Tổng** | **4.082.637** | 100% | **1.577,9** | 100% | |

Số GCN vi mô/ngày trên DB (đã tính): chuyến xe ≈ 39.900, đồ ăn ≈ 8.500, thiết bị điện tử ≈ 3.200, DelayCare ≈ 300 (trên 42 ngày từ 20/8) — tổng ≈ 51.700/ngày.

**Vì sao tổng doanh thu không đổi khi thêm vi mô.** Doanh thu vi mô nằm **trong** ngân sách nhóm (sinh mạng, du lịch, tài sản). Bước hiệu chỉnh coi dòng vi mô là cố định và co giãn đơn doanh nghiệp / nhóm ở phần còn lại, nên tổng từng nhóm và cơ cấu tài sản + cháy nổ / con người / xe ≈ 51 / 31 / 17% giữ nguyên. Vi mô chiếm khoảng 5% doanh thu ghi nhận của nhóm sinh mạng và tài sản, 8% của nhóm du lịch (đã tính).

**Phân phối lệch hơn.** "Nhiều đơn nhỏ – ít đơn lớn" càng rõ: 10% hợp đồng lớn nhất chiếm **97,7%** doanh thu, 1% lớn nhất chiếm **80,1%** (lần nạp trước trên DB, chưa có vi mô: 93% / 74%; v2 năm 2025: 74% / 25%, xem `../GENERATION_LOGIC.md`). Nhóm sinh mạng có 3.298.699 hợp đồng (chủ yếu GCN vi mô) nhưng chỉ ≈ 74 tỷ phí gốc. Đây là đặc trưng thật của bảo hiểm nhúng (OPES phát hành 109,3 triệu hợp đồng năm 2023). Khi làm dashboard:
- tách "số giao dịch / số hợp đồng" và "doanh thu" thành hai thước đo riêng;
- lọc riêng sản phẩm `MV_*` khi tính phí bình quân, phân vị phí, tỷ trọng số đơn theo nhóm.

## Đơn vị và doanh nghiệp (`ref.company`)

| Nội dung | Giá trị | Nhãn | Căn cứ |
|---|---|---|---|
| Doanh nghiệp | Tổng Công ty Bảo hiểm PVI (`PVI`), công ty con 100% của CTCP PVI (PVI Holdings) | [NGUỒN] | BCTN 2024, trang PDF 12 |
| Đơn vị | Trụ sở chính – các Ban kinh doanh (`HO`), Bảo hiểm PVI Digital (`DGT`, TP.HCM) và 46 đơn vị theo trang mạng lưới (DGT + 46 = 47 đơn vị trên trang) (Đông Đô, Thăng Long, …, Phía Nam); tỉnh = địa chỉ trụ sở | [NGUỒN] | pvi.com.vn/vi/network; online.pvi.com.vn/lien-he |
| Trọng số khai thác của đơn vị | Theo quy mô kinh tế địa bàn (1–4); ×1,5 cho Phía Nam, Thủ Đô, Duyên Hải, Thăng Long, Sài Gòn | **[ƯỚC TÍNH]** | PVI không công bố doanh thu từng đơn vị (cả hai công cụ nghiên cứu đều KHÔNG TÌM THẤY). 5 đơn vị được nhân 1,5 vì được PVI vinh danh (xuất sắc nhất 2024; 6 tháng 2025; xuất sắc 2025; hoàn thành sớm kế hoạch 2025) hoặc tự công bố dẫn đầu bán lẻ (pvisg.net) |
| Tỉnh không có đơn vị | Gán đơn vị gần nhất (ví dụ Tuyên Quang, Lạng Sơn, Cao Bằng → Thái Nguyên; Lào Cai, Lai Châu → Vĩnh Phú; Điện Biên, Sơn La → Hà Nội) | [QUY ƯỚC] | `gen_volume._NO_UNIT` |
| Đối tác | Đối tác cũ vẫn ẩn danh (Ngân hàng A, OTA A…); 3 đối tác số thật mới: `GREEN_SM`, `ATADI`, `FUSE` (giao dịch là giả lập) | [NGUỒN] tên đối tác | Mục 10 của `../sources/market_data.md` |
| Không có trong `ref.company` | Hanoi Re (tên cũ PVI Re, Holdings sở hữu 81,09%) nhận tái bảo hiểm; PVIAM (61,96%) quản lý quỹ — không cấp hợp đồng bảo hiểm gốc | [NGUỒN] | BCTN 2024, 2025. Ngoài phạm vi doanh thu phí bảo hiểm gốc |

So với cả tập đoàn: năm 2025 doanh thu hợp nhất PVI Holdings 28.923 tỷ, Bảo hiểm PVI 27.258 tỷ (94,2%, trong đó phí bảo hiểm gốc 14.908 tỷ), Hanoi Re 3.690 tỷ, PVIAM 76,4 tỷ (BCTN 2025). POC chỉ mô phỏng 4 nghiệp vụ của Bảo hiểm PVI (10.377,9 tỷ năm 2025).

**Khóa không dùng lại** (áp dụng với `--replace`):
- Bộ sinh đọc khóa lớn nhất đang có **trước khi xóa** và bắt đầu sau đó (làm tròn lên): `policy_id`, `txn_id`, `coverage_id` từ bội số 10 triệu kế tiếp; số hợp đồng từ bội số 1 triệu kế tiếp theo từng đơn vị × sản phẩm; mã khách hàng từ bội số 100 triệu kế tiếp.
- Mốc khóa lớn nhất đã phát hành được lưu lâu dài trong bảng **`bronze.poc_key_watermark`** (`key_name`, `max_value`; ghi sau mỗi đợt nạp, không bao giờ bị DELETE). Dù bảng fact đang trống hoặc lần trước nạp dở, lần sau vẫn bắt đầu sau mọi khóa cũ.
- Lần nạp cuối (19/10/2026): `policy_id` 60.000.001–64.082.637, `txn_id` 60.000.001–64.098.401, `coverage_id` 60.000.001–64.127.680, mã khách `KH610000001`–`KH690000048`. Các dải 30 triệu (cũ), 40 và 50 triệu (2 lần nạp trung gian ngày 19/10) đều đã xóa; CDC và Iceberg vẫn giữ lịch sử các khóa cũ, nên khóa mới không trùng.
- `--replace` đồng bộ danh mục với `02_data.sql`: upsert theo khóa chính, xóa dòng không còn dùng (DEMO, HN1…), dòng không đổi giữ nguyên để CDC không phát sự kiện thừa.

## Tham số theo thời gian

| Tham số | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Doanh thu tháng 9 so với tháng 8 (mỗi ngày) | ×1,479 (nay là hệ quả của ngân sách tháng). Trên DB, doanh thu ghi nhận mỗi ngày tháng 9 / tháng 8 = 31,3 / 20,6 tỷ ≈ ×1,52 (đã tính). Số **giao dịch**/ngày chỉ ×1,10 vì phần lớn là GCN vi mô, không theo mùa vụ tháng | [CHÍNH THỨC] | Bộ Tài chính, bản tin thị trường bảo hiểm tháng 8, 9, 10/2025. Phí gốc phi nhân thọ lũy kế 2025: 7T 50.784 · 8T 56.376 · 9T 64.378 tỷ, suy ra tháng 8 = 5.592 tỷ, tháng 9 = 8.002 tỷ |
| Phân bố trong tháng | Đều; **không** có hệ số cuối tháng | — | Không có nguồn công khai về phân bố theo ngày, nên để trung tính |
| Kênh văn phòng (doanh nghiệp, đại lý, ngân hàng) cuối tuần / lễ | T7 ×0,25–0,6; CN ×0,05–0,3; lễ ×0,05–0,3 | [QUY ƯỚC] | Lịch làm việc hành chính; mức giảm là quy ước |
| Kênh số | Như nhau mọi ngày | [QUY ƯỚC] | — |
| Vi mô theo ngày | Chuyến xe: CN ×0,9, T6 ×1,05, lễ ×1,1. Đồ ăn: T6 ×1,05, T7–CN ×1,15, lễ ×1,2. Thiết bị điện tử: 8/8, 9/9 ×3 | [ƯỚC TÍNH] | Nhịp đi làm / đặt đồ ăn; ngày hội mua sắm "ngày đôi" của sàn TMĐT |
| Nghỉ Quốc khánh | 01–02/9/2026 | [QUY ƯỚC] | Bộ luật Lao động 2019 Điều 112 (nghỉ 2 ngày); ngày liền kề 01/9 là giả định |
| Học sinh tập trung quanh khai giảng | Đỉnh ~30/8, khai giảng 5/9 | Thời điểm [QUY ƯỚC], độ lớn [ƯỚC TÍNH] | Khung kế hoạch năm học của Bộ GD&ĐT |
| Đơn khác (xe, sức khỏe, tài sản, cháy nổ…) | Hiệu lực **ngay ngày cấp** | [QUY ƯỚC] | Không có nguồn về độ trễ, nên để trung tính |

## Du lịch

| Tham số | Giá trị (phân vị thực nghiệm) | Nhãn | Nguồn |
|---|---|---|---|
| Số ngày mua trước chuyến đi, trong nước | p25 = 12 · p50 = 72 · p75 = 181 ngày | [NGUỒN THAY THẾ] | Hotel booking demand, khách nội địa (`country = PRT`), 48.590 lượt đặt |
| Số ngày mua trước chuyến đi, quốc tế | p25 = 22 · p50 = 68 · p75 = 148 ngày | [NGUỒN THAY THẾ] | Hotel booking demand, khách quốc tế, 70.800 lượt |
| Thời hạn chuyến đi, trong nước | p50 = 3 · p90 = 7 ngày | [NGUỒN THAY THẾ] | Hotel booking demand: số đêm + 1, khách nội địa |
| Thời hạn chuyến đi, quốc tế | p25 = 9 · p50 = 22 · p90 = 96 ngày (lọc 1–365) | [DATASET] | Travel Insurance, 61.931/63.326 dòng hợp lệ |
| Kênh bán qua trung gian | Đại lý online 70,7% · hãng bay online 27,5% · đại lý offline 1,7% | [DATASET] | Travel Insurance (`Agency Type` × `Distribution Channel`) |
| Phần bán qua kênh công ty | 20% (web/app 12%, đại lý cá nhân 5%, trực tiếp 3%) | [ƯỚC TÍNH] | Dataset chỉ có hợp đồng bán qua trung gian |
| Hoa hồng / doanh số (qua trung gian) | 56,7% bằng 0; phần còn lại tới 0,35–0,65, **cắt ở trần 20%** | [DATASET] + [CHÍNH THỨC] | Travel Insurance; trần hoa hồng theo TT 67/2023 Điều 51 |
| DelayCare bay sau ngày mua | 1–45 ngày (phân phối hình học, trung bình ≈ 12 ngày) | [ƯỚC TÍNH] | Mua kèm vé máy bay |

## Hệ quả cần biết

- Doanh thu du lịch được ghi nhận khi chuyến đi bắt đầu. Với độ trễ theo dataset (trung vị khoảng 70 ngày), phần doanh thu du lịch rơi sang tháng 10/2026 – 2028: trên DB 16,7 tỷ ghi nhận sau 30/9; khoản giảm thu (giảm phí, hoàn phí, hủy) trong tháng 8–9 là −5,8 tỷ. Vì vậy doanh thu ghi nhận tháng 8–9 (1.577,9 tỷ) thấp hơn phí gốc khai thác (1.600,6 tỷ). Tỷ giá USD 2027–2028 lấy bằng tháng 12/2026 [ƯỚC TÍNH].
- Các tham số chưa thay đổi trong lần hiệu chỉnh này vẫn giữ căn cứ cũ, xem `../GENERATION_LOGIC.md`: đơn giá theo biểu phí (NĐ 67/2023, giá niêm yết), cơ cấu sản phẩm, đồng bảo hiểm, phân bổ, sửa đổi bổ sung.

## Nguồn

- Bộ Tài chính, *Bản tin thị trường bảo hiểm* tháng 8, 9 và 10/2025: mof.gov.vn › Quản lý giám sát bảo hiểm › Bản tin thị trường bảo hiểm
- N. Antonio, A. de Almeida, L. Nunes, *Hotel booking demand datasets*, Data in Brief 22 (2019) 41–49, doi:10.1016/j.dib.2018.11.126. Bản CSV dùng: TidyTuesday 2020-02-11 `hotels.csv`
- *Travel Insurance* dataset (~63 nghìn hợp đồng: Agency, Agency Type, Distribution Channel, Product Name, Claim, Duration, Destination, Net Sales, Commision, Gender, Age). Bản dùng: github.com/sohamthirty/Claim-Prediction › Data/travel_insurance.csv. Nguồn gốc gốc không được ghi chép đầy đủ, nên chỉ dùng cho thời hạn, kênh và hoa hồng.
- Đã xem nhưng **không dùng**:
  - `insurance_claims.csv` (Mendeley / Kaggle): 1.000 dòng, chỉ có `policy_bind_date`, thường được coi là dữ liệu tự tạo.
  - Các trang thống kê tổng hợp (worldmetrics, zipdo, wifitalents, dataintelo): không dẫn nguồn gốc kiểm chứng được.
  - Danh sách "7 đơn vị về đích sớm" (do agy CLI đưa ra): không kiểm chứng được, đã loại.

### Nguồn mới cho đơn vị PVI và bảo hiểm vi mô (19/10/2026)

**Phương pháp:** nghiên cứu chéo bằng codex CLI (gpt-6.1-sol) và agy CLI (gemini-3.8-flash-high) với cùng một đề bài, đối chiếu kết quả hai bên; mọi link dưới đây đã kiểm lại bằng curl ngày 19/10/2026. Bản gốc: `../sources/market_data.md` mục 9, 10.

| Nội dung dùng | Số liệu | Nhãn | URL (trang) |
|---|---|---|---|
| Tổng Công ty Bảo hiểm PVI là công ty con 100% của CTCP PVI (PVI Holdings) | 100% tại 31/12/2024 | [NGUỒN] | BCTN PVI 2024, trang PDF 12: https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf |
| Các công ty con khác của Holdings; doanh thu 2024 | Hanoi Re 81,09%, PVIAM 61,96%; Holdings 21.824 tỷ, PVI Insurance 20.405 tỷ, Hanoi Re 3.017,3 tỷ, PVIAM 57,4 tỷ | [NGUỒN] | BCTN PVI 2024, trang PDF 12, 22, 29, 30, 31 (link trên) |
| Hanoi Re là tên mới của PVI Re | — | [NGUỒN] | https://www.hanoire.com/vi/pvi-re-chinh-thuc-doi-ten-thanh-hanoi-re |
| Doanh thu 2025 của Holdings và các công ty con | Holdings 28.923 tỷ; Bảo hiểm PVI 27.258 tỷ (phí gốc 14.908 tỷ); Hanoi Re 3.690 tỷ; PVIAM 76,4 tỷ | [NGUỒN] (94,2% là số tự tính) | BCTN PVI 2025, trang PDF 29, 32, 33, 34: https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf |
| Danh sách đơn vị, địa chỉ trụ sở → tỉnh của đơn vị | 47 đơn vị: PVI Digital + 45 công ty thành viên + Phía Nam | [NGUỒN] | https://www.pvi.com.vn/vi/network |
| Bảo hiểm PVI Digital là chi nhánh của Tổng Công ty | — | [NGUỒN] | https://online.pvi.com.vn/lien-he |
| PVI Sài Gòn tự công bố doanh thu đứng đầu hệ thống bán lẻ | — | [NGUỒN] | https://pvisg.net |
| Đơn vị được vinh danh: Phía Nam (xuất sắc nhất 2024); Thủ Đô (6 tháng 2025); Duyên Hải (2025); Thủ Đô, Thăng Long hoàn thành sớm kế hoạch 2025 | → hệ số ×1,5 là **[ƯỚC TÍNH]** | [NGUỒN] | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-mot-nam-vuot-song-chinh-phuc-nhung-cot-moc-moi-681b4f9737783 ; https://www.pvi.com.vn/en/news/bao-hiem-pvi-doi-moi-sang-tao-va-thanh-cong ; https://vnexpress.net/nhung-yeu-to-giup-doanh-thu-bao-hiem-pvi-vuot-1-ty-usd-5011267.html ; https://www.pvi.com.vn/vi/news/pvi-thu-do-va-pvi-thang-long-hai-don-vi-tiep-theo-duoc-vinh-danh-hoan-thanh-som-ke-hoach-kinh-doanh-nam-2025 |
| Green SM Care: tai nạn hành khách theo chuyến; PVI Digital là 1 trong 5 nhà bảo hiểm (PVI Digital, OPES, BIC, TCGI, MIC) | 1.000 đ/chuyến Bike, 2.000 đ/chuyến Taxi | [NGUỒN] | https://www.greensm.com/vn-vi/bao-hiem-khach-hang ; https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Food Care: Green SM × Bảo hiểm PVI, theo đơn giao đồ ăn | 1.000 đ/đơn; tai nạn 150 triệu đ/đơn | [NGUỒN] | https://www.greensm.com/vn-vi/bao-hiem-giao-do-an |
| DelayCare: PVI × ATADI, ra mắt 20/08/2026, đơn vị cung cấp PVI Thủ Đô | Trễ ≥ 120 phút trả 500.000 đ/người; phí KHÔNG TÌM THẤY → 35.000 đ là [ƯỚC TÍNH] | [NGUỒN] | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-ra-mat-delaycare-giai-phap-bao-hiem-tre-chuyen-bay-danh-cho-hanh-khach |
| Bảo hiểm thiết bị điện tử khi mua trên Shopee / Lazada (PVI qua Fuse, PasarPolis) | Ví dụ 38.102 đ/12 tháng (nguồn thứ cấp) | [NGUỒN] | https://help.shopee.vn/portal/4/article/79225 ; https://magiamgia.com/bao-hiem-thiet-bi-dien-tu-lazada/ |
| Đối tác số của PVI Digital: MoMo, Viettel Money, Shopee, Lazada, FE Credit, Home Credit, Xanh SM, Grab, Trip.com, Thế Giới Di Động, Điện Máy Xanh | "hàng triệu khách hàng" | [NGUỒN] | https://www.pvi.com.vn/vi/news/pvi-digital-doi-tac-bao-hiem-so-cua-cac-nen-tang-va-he-sinh-thai-so-hang-dau-viet-nam |
| Quy mô Green SM | > 1 triệu chuyến/ngày (2025, nguồn thứ cấp) | [NGUỒN] | https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam |
| Tham chiếu sản lượng vi mô ở Việt Nam (OPES) | 109,3 triệu hợp đồng năm 2023; cao điểm > 500.000 đơn/ngày | [NGUỒN] | https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154 |
| TMĐT của Bảo hiểm PVI | Gần 800 tỷ năm 2024 (30 kết nối API); 2025 gần gấp đôi | [NGUỒN] | BCTN 2024 trang PDF 29 (link trên); https://pviholdings.com.vn/vi/news-details?id=6013 |
| Bảo hiểm chuyến đi của Grab do Chubb, của Be do OPES (không phải PVI) | — | [NGUỒN] | https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Grab × PVI 2026 là BHXH/BHYT tự nguyện cho tài xế | — | [NGUỒN] | https://www.grab.com/vn/blog/driver/bhxh-bhyt-pvi/ |

**KHÔNG TÌM THẤY → [ƯỚC TÍNH]** (giá trị trong `gen_volume.py` / `build_v2.py`, căn cứ ở các mục trên):
- số GCN vi mô/ngày: 40.000 chuyến xe, 8.000 đồ ăn, 300 DelayCare, 3.000 thiết bị điện tử; tỷ lệ mua 20% × 20% về PVI; Bike/Taxi 60/40;
- phí DelayCare 35.000 đ/người; phí thiết bị điện tử 1,5–3,5% giá máy;
- kho 1,5 triệu khách vi mô, 40% từ nhóm dùng thường xuyên; hủy DelayCare 3%, thiết bị điện tử 2%; giờ cao điểm; ×3 ngày 8/8, 9/9;
- doanh thu / trọng số khai thác của từng đơn vị, tỷ trọng trụ sở chính so với đơn vị.
