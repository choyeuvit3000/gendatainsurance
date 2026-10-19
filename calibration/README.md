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
| **[DATASET]** | Dataset công khai có dữ liệu thật, đúng lĩnh vực bảo hiểm |
| **[NGUỒN THAY THẾ]** | Dataset công khai có bình duyệt nhưng thuộc lĩnh vực lân cận, dùng thay khi không có dữ liệu bảo hiểm |
| **[QUY ƯỚC]** | Quy tắc cấu trúc (lịch làm việc, lịch năm học), không phải số liệu đo được |
| **[ƯỚC TÍNH]** | Giá trị dự án tự đặt, chưa có nguồn |

## Quy mô doanh thu (hiệu chỉnh lại 16/10/2026 — cơ cấu theo BCTC PVI như v2)

Bộ volume dùng **cùng cơ cấu doanh thu với v2** (tỷ trọng giữa các nhóm và trong từng nhóm), thu về kỳ tháng 8–9. Yêu cầu dự án là **> 50.000 giao dịch/ngày**; ở đúng quy mô PVI với giá niêm yết chỉ được khoảng 13–25 nghìn/ngày, nên mọi ngân sách nhóm được nhân **cùng một hệ số quy mô k ≈ 3,93** [QUY ƯỚC]. Cơ cấu giữ nguyên, đơn giá giữ nguyên, chỉ số hợp đồng và doanh thu tuyệt đối tăng k lần.

| Bước | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Mục tiêu năm theo nhóm sản phẩm | Tổng 10.377,9 tỷ: sức khỏe 2.410,1 · sinh mạng 482,0 · du lịch 160,7 · học sinh 160,7 · TNDS 437,4 · vật chất xe 1.385,3 · cháy nổ 3.451,2 · tài sản 1.890,6 | [CHÍNH THỨC] + tỷ lệ chia [ƯỚC TÍNH] | BCTC kiểm toán 2025 Bảo hiểm PVI, thuyết minh 21 (trang 45 của PDF); tỷ lệ chia như v2 (Con người 75/15/5/5, Xe 24/76 theo IAV, tài sản thuần 50%) |
| Tỷ trọng tháng 8, 9 | 5.592 / 88.054 = 6,35% · 8.002 / 88.054 = 9,09% | [CHÍNH THỨC] | Bộ Tài chính: phí gốc phi nhân thọ toàn thị trường 2025 theo tháng và cả năm (bản tin 01/2026). Giả định PVI có mùa vụ tháng giống thị trường [ƯỚC TÍNH] |
| Năm 2026 | Dùng quy mô 2025 | [QUY ƯỚC] | Chưa có BCTC 2026 |
| Ngân sách tháng 8 + 9 theo quy mô PVI | ≈ 1.602 tỷ (tháng 8 ≈ 659, tháng 9 ≈ 943) | — | = mục tiêu năm × tỷ trọng tháng |
| **Hệ số quy mô k** | **≈ 3,93** → ngân sách ≈ 6.300 tỷ cho 2 tháng | [QUY ƯỚC] | Chọn để ngày thấp nhất đạt 52.000 hợp đồng cấp mới / tái tục (yêu cầu > 50.000 giao dịch/ngày). Nhân đều mọi nhóm nên cơ cấu không đổi |
| Tỷ trọng doanh thu của sản phẩm trong nhóm | TNDS xe máy 65 / ô tô 35; VCX ô tô 80 / xe máy 20; học sinh tai nạn 60 / sức khỏe 40; du lịch nội địa 55 / quốc tế 45; sinh mạng CN 25 / người vay 35 / TN24 40; sức khỏe CN 30 / nhóm 60 / BHN 10; nhà 20 / MRR 50 / MRR CN 30; cháy nổ BB 70 / TN 30 | [ƯỚC TÍNH] | PVI không công bố |
| Số hợp đồng | = ngân sách × tỷ trọng ÷ phí bình quân của sản phẩm (đo bằng mô phỏng đơn giá) | — | Đơn giá theo biểu phí NĐ 67/2023 và giá niêm yết, như v2 |
| Hiệu chỉnh | Đơn bán lẻ giữ nguyên giá; co giãn đơn doanh nghiệp / nhóm / lô để doanh thu từng nhóm khớp ngân sách mỗi đợt 7 ngày | — | Cùng thuật toán với v2 |

**Hệ quả:** khoảng 53–66 nghìn giao dịch/ngày tháng 8 và 80–99 nghìn/ngày tháng 9 (khoảng 5 triệu giao dịch cả kỳ). Cơ cấu doanh thu (tài sản + cháy nổ ≈ 51%, con người ≈ 31%, xe ≈ 17%) khớp BCTC PVI; doanh thu tuyệt đối ≈ 3,9 lần quy mô PVI — doanh nghiệp giả lập lớn hơn PVI, không trình bày như số liệu của PVI.

**Khóa không dùng lại:** khi nạp lại bằng `--replace`, bộ sinh đọc khóa lớn nhất đang có **trước khi xóa** và bắt đầu sau đó (làm tròn lên): `policy_id`, `txn_id`, `coverage_id` từ bội số 10 triệu kế tiếp; số hợp đồng từ bội số 1 triệu kế tiếp theo từng đơn vị × sản phẩm; mã khách hàng từ bội số 100 triệu kế tiếp. CDC và Iceberg vẫn giữ lịch sử các khóa cũ, nên khóa mới không trùng.

## Tham số theo thời gian

| Tham số | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Doanh thu tháng 9 so với tháng 8 (mỗi ngày) | ×1,479 (nay là hệ quả của ngân sách tháng) | [CHÍNH THỨC] | Bộ Tài chính, bản tin thị trường bảo hiểm tháng 8, 9, 10/2025. Phí gốc phi nhân thọ lũy kế 2025: 7T 50.784 · 8T 56.376 · 9T 64.378 tỷ, suy ra tháng 8 = 5.592 tỷ, tháng 9 = 8.002 tỷ |
| Phân bố trong tháng | Đều; **không** có hệ số cuối tháng | — | Không có nguồn công khai về phân bố theo ngày, nên để trung tính |
| Kênh văn phòng (doanh nghiệp, đại lý, ngân hàng) cuối tuần / lễ | T7 ×0,25–0,6; CN ×0,05–0,3; lễ ×0,05–0,3 | [QUY ƯỚC] | Lịch làm việc hành chính; mức giảm là quy ước |
| Kênh số | Như nhau mọi ngày | [QUY ƯỚC] | — |
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

## Hệ quả cần biết

- Doanh thu du lịch được ghi nhận khi chuyến đi bắt đầu. Với độ trễ theo dataset (trung vị khoảng 70 ngày), phần doanh thu du lịch rơi sang tháng 10/2026 – 2028. Tỷ giá USD 2027–2028 lấy bằng tháng 12/2026 [ƯỚC TÍNH].
- Các tham số chưa thay đổi trong lần hiệu chỉnh này vẫn giữ căn cứ cũ, xem `../GENERATION_LOGIC.md`: đơn giá theo biểu phí (NĐ 67/2023, giá niêm yết), cơ cấu sản phẩm, đồng bảo hiểm, phân bổ, sửa đổi bổ sung.

## Nguồn

- Bộ Tài chính, *Bản tin thị trường bảo hiểm* tháng 8, 9 và 10/2025: mof.gov.vn › Quản lý giám sát bảo hiểm › Bản tin thị trường bảo hiểm
- N. Antonio, A. de Almeida, L. Nunes, *Hotel booking demand datasets*, Data in Brief 22 (2019) 41–49, doi:10.1016/j.dib.2018.11.126. Bản CSV dùng: TidyTuesday 2020-02-11 `hotels.csv`
- *Travel Insurance* dataset (~63 nghìn hợp đồng: Agency, Agency Type, Distribution Channel, Product Name, Claim, Duration, Destination, Net Sales, Commision, Gender, Age). Bản dùng: github.com/sohamthirty/Claim-Prediction › Data/travel_insurance.csv. Nguồn gốc gốc không được ghi chép đầy đủ, nên chỉ dùng cho thời hạn, kênh và hoa hồng.
- Đã xem nhưng **không dùng**:
  - `insurance_claims.csv` (Mendeley / Kaggle): 1.000 dòng, chỉ có `policy_bind_date`, thường được coi là dữ liệu tự tạo.
  - Các trang thống kê tổng hợp (worldmetrics, zipdo, wifitalents, dataintelo): không dẫn nguồn gốc kiểm chứng được.
