# Nguồn số liệu công khai dùng để hiệu chỉnh dữ liệu dummy

Số liệu tra cứu ngày 07/10/2026.
- **[suy ra]**: tính từ các số đã có trích dẫn.
- **[ƯỚC TÍNH]**: giả định, chưa có nguồn xác minh.

## 1. Quy mô thị trường phi nhân thọ (doanh thu phí bảo hiểm gốc)

| Kỳ | Tỷ VND | Tăng trưởng | Nguồn |
|---|---:|---:|---|
| 2024 | 79.348 | +11,7% | IAV: https://iav.vn/tong-quan,-so-lieu-thi-truong-bao-hiem/254773-254773-mot-so-hoat-dong-noi-bat-cua-thi-truong-bao-hiem-viet-nam-ca-nam-2024 |
| 2024 (số của Bộ Tài chính) | 78.291 | +10,21% | MOF: https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/thong-tin-thi-truong/mofucm346776 |
| 2025 | 88.054 | +10,95% | MOF Bản tin 01/2026: https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026 |

## 2. Cơ cấu theo nghiệp vụ

Nguồn: IAV 2024 và MOF 2025, cùng URL như mục 1.

| Nghiệp vụ | 2024 (tỷ) | % 2024 [suy ra] | 2025 (tỷ) | % 2025 |
|---|---:|---:|---:|---:|
| Sức khỏe (gồm tai nạn con người) | 28.744 | 36,2% | 31.676 | 35,97% |
| Xe cơ giới | 18.693 | 23,6% | 20.976 | 23,82% |
| – TNDS bắt buộc | 4.537 | 5,7% | | |
| – Xe tự nguyện | 14.155 | 17,8% | | |
| Cháy nổ (bắt buộc 9.923 + tự nguyện 6.714) | 16.637 | 21,0% | 13.544 | 15,38% |
| Tài sản | | | 8.559 | 9,72% |

**Cách áp vào dummy.** Số toàn thị trường **không** dùng làm cơ cấu. Cơ cấu và quy mô lấy theo BCTC PVI (mục 8). Từ số thị trường chỉ dùng:
- Trong Xe: TNDS bắt buộc ≈ **24%**, vật chất xe ≈ **76%** (theo tỷ lệ 4.537 / 18.693 năm 2024) **[suy ra]**.
- Để so sánh: thị trường có xe ≈ 28% trong 4 nghiệp vụ POC, còn PVI chỉ ≈ 18% vì thiên về khách hàng công nghiệp.

Trong Con người chưa có số public chia theo sản phẩm. Dự án chốt **[ƯỚC TÍNH]**: sức khỏe 75%, sinh mạng–tai nạn 15%, du lịch 5%, học sinh 5% (xem mục 8 và `docs/Logic_Sinh_Du_Lieu.html`, tham số P22).

## 3. Thị phần và quy mô doanh nghiệp

Top 5 năm 2025 (MOF Bản tin 01/2026):

| Doanh nghiệp | Thị phần |
|---|---:|
| PVI | 16,93% |
| Bảo Việt | 12,58% |
| Bảo Minh | 6,80% |
| MIC | 6,15% |
| BIC | 5,83% |

Nhóm hạng 6–10 có thị phần khoảng 4–5,5%.

**Cách áp vào dummy.** Doanh nghiệp giả lập "Tổng công ty Bảo hiểm DEMO" lấy **quy mô của PVI** (DN đứng đầu thị trường) trên 4 nghiệp vụ POC: khoảng 10.378 tỷ năm 2025 và 8.958 tỷ năm 2024 (mục 8).

**Mô hình tổ chức "Tổng công ty → công ty thành viên".** Đây là mô hình công khai của các DNBH lớn:
- Bảo hiểm Bảo Việt: 79 công ty thành viên (BVH Integrated Report 2024: https://static2.vietstock.vn/vietstock/2025/4/22/20250422_bvh_250422_integrated_report_2024.pdf, trang 127).
- PVI Insurance: 47 công ty thành viên (https://www.pvi.com.vn/vi/services/mang-luoi).

## 4. Kênh phân phối

| Chỉ số | Số liệu | Nguồn |
|---|---|---|
| Phí qua môi giới 2025 | 11.905 tỷ, ≈13,5% thị trường [suy ra] | MOF Bản tin 01/2026 |
| Bancassurance của một DNBH (MIC, 2023) | 32% doanh thu. Mục tiêu chung của ngành ≈30% | https://www.pjico.com.vn/bao-hiem-phi-nhan-tho-day-manh-ban-cheo-qua-ngan-hang.html |
| Kênh TMĐT/API của một DNBH lớn (2024) | ≈800 tỷ, ≈6% phí gốc [suy ra] | PVI Annual Report 2024: https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf (trang 29) |

**Cách áp vào dummy [ƯỚC TÍNH].** Trọng số kênh đặt theo định hướng của PVI, không theo số bình quân thị trường:
- điện tử ≈ 6% (2024) → ≈ 10% (2025);
- môi giới 15–20%, cao hơn mức 13,5% của thị trường;
- bancassurance 5–8%, thấp hơn mức 30% của MIC vì PVI mới mở rộng kênh này.

Kết quả đo xem `docs/Logic_Sinh_Du_Lieu.html` (tham số P33).

## 5. Phí niêm yết công khai, dùng làm mức phí dummy

| Sản phẩm | Mức phí | Nguồn |
|---|---|---|
| TNDS bắt buộc ô tô dưới 6 chỗ, không kinh doanh | 437.000 đ (chưa VAT), 480.700 đ (có VAT) | NĐ 67/2023/NĐ-CP; online.pvi.com.vn; baovietonline.com.vn |
| TNDS mô tô | 60.500–66.000 đ (có VAT) | online.pvi.com.vn/san-pham; baovietonline.com.vn |
| Vật chất xe ô tô | 0,5–3,5% giá trị xe/năm | https://online.pvi.com.vn/kien-thuc/bao-hiem-o-to-bao-nhieu-tien |
| Học sinh | Phổ biến 100.000 đ/học sinh/năm | https://cafef.vn/dau-nam-hoc-bo-100000-dong-mua-bao-hiem-than-the-cho-con-hang-trieu-phu-huynh-co-the-bo-qua-dieu-nay-188240923103450415.chn |
| Du lịch trong nước | từ 17.000 đ/chuyến | baovietonline.com.vn |
| Du lịch quốc tế | từ 100.000 đ/người | online.pvi.com.vn |
| Sức khỏe cá nhân | từ 1,4–1,5 triệu/năm; gói cao cấp ≈6,2 triệu | baovietonline.com.vn |
| Nhà tư nhân / căn hộ | từ 220.000–270.000 đ/năm | https://baovietonline.com.vn/; https://online.pvi.com.vn/san-pham |

## 6. Mùa vụ

| Mẫu hình | Số liệu | Nguồn / mức chắc chắn |
|---|---|---|
| Toàn thị trường 2024 theo quý | Q1 25,2% · Q2 24,0% · Q3 24,4% · Q4 26,3% | [suy ra] từ số lũy kế IAV. Doanh thu khá đều, Q4 và Q1 nhích nhẹ |
| Học sinh | Thu phí đầu năm học, đỉnh tháng 8–10 | CafeF 23/9/2024; https://huaf.edu.vn/bao-hiem-sinh-vien/ |
| Du lịch cao điểm hè/Tết; xe cuối năm; sức khỏe nhóm tái tục đầu năm | | **[ƯỚC TÍNH]** |

## 7. Tỷ giá hạch toán USD/VND năm 2025

Đây là tỷ giá hạch toán do Kho bạc Nhà nước công bố hằng tháng, mỗi tháng một thông báo (ví dụ tháng 01/2025: https://thuvienphapluat.vn/van-ban/Tien-te-Ngan-hang/Thong-bao-7727-TB-KBNN-2024-ty-gia-hach-toan-ngoai-te-thang-01-nam-2025-641872.aspx). Năm 2024: **[ƯỚC TÍNH]** nội suy theo tỷ giá trung tâm của NHNN.

| T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | T9 | T10 | T11 | T12 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 24.283 | 24.334 | 24.539 | 24.786 | 24.901 | 24.954 | 25.007 | 25.151 | 25.252 | 25.214 | 25.120 | 25.118 |

## 8. Bảo hiểm PVI — số liệu công khai (căn cứ hiệu chỉnh chính)

**Phí bảo hiểm gốc theo nghiệp vụ** (tỷ đồng). Nguồn: BCTC kiểm toán 2025 của Tổng công ty Bảo hiểm PVI, thuyết minh 21 — https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf (trang 45 của file PDF, bản scan)

| Nghiệp vụ | 2024 | 2025 |
|---|---:|---:|
| Tài sản & thiệt hại (gồm kỹ thuật, năng lượng) | 4.138,0 | 3.781,2 |
| Cháy nổ | 3.005,9 | 3.451,2 |
| Sức khỏe & tai nạn con người | 2.220,7 | 3.213,4 |
| Xe cơ giới | 1.662,2 | 1.822,7 |
| Thân tàu & P&I | 1.130,7 | 1.221,9 |
| Gián đoạn kinh doanh | 230,4 | 481,6 |
| Hàng hóa vận chuyển | 365,5 | 429,2 |
| Trách nhiệm | 324,6 | 394,8 |
| Hàng không | 434,2 | 388,5 |
| Tín dụng, nông nghiệp | 48,6 | 55,8 |
| Thuần sau giảm trừ | 13.368,2 | 14.908,3 |

**Phí gốc hợp nhất theo quý** (BCTC quý PVI Holdings, thuyết minh 21 — ví dụ quý 4/2025: https://pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/ce6f18e2-7a79-42f3-b6ab-2b79ea1e4077.pdf, trang 31): 2024 là 31,5 / 21,5 / 26,6 / 20,5%; 2025 là 29,7 / 24,1 / 24,8 / 21,4%.

**Kênh điện tử:** gần 800 tỷ năm 2024 (BCTN 2024). Quý I/2025 doanh thu kênh TMĐT tăng 1,8 lần so với cùng kỳ (https://pvn.vn/khoi-dau-vung-chac-bao-hiem-pvi-huong-toi-moc-doanh-thu-ty-do-la-my-nam-2025-28459); tỷ trọng ≈ 10% năm 2025 là **[suy ra]**. Đối tác API: Vietnam Airlines, MobiFone, Viettel, Thế Giới Di Động, Shopee.

**Bancassurance:** hợp tác với Nam A Bank (https://www.pvi.com.vn/vi/news/bao-hiem-pvi-va-nam-a-bank-khoi-dong-hop-tac-kinh-doanh-tai-khu-vuc-mien-tay). Không có số doanh thu.

**Mốc hợp đồng lớn (ngoài phạm vi POC):**

| Hợp đồng | Phí | Nguồn |
|---|---|---|
| Hàng không Vietnam Airlines | 540,2 tỷ (giá trúng thầu, liên danh Bảo Việt – PVI – Bảo Minh); gói mời thầu ≈ 600 tỷ | https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615; https://vietnambusinessinsider.vn/vietnam-airlines-mo-thau-goi-bao-hiem-lon-nhat-nam-voi-600-ty-dong-nhung-chi-co-mot-nha-thau-tham-gia-nop-ho-so-a49139.html |
| Công trình Nhiệt điện Quảng Trạch I | > 365 tỷ (STBH gần 28.000 tỷ) | https://www.tinnhanhchungkhoan.vn/bao-hiem-ban-buon-truoc-co-hoi-lon-post368348.html |
| Công trình nhà ga Long Thành (6 công ty) | 118,9 tỷ (trang chặn tải tự động, chưa kiểm lại được) | https://baodauthau.vn/lien-danh-6-thanh-vien-trung-goi-thau-bao-hiem-cang-hkqt-long-thanh-post136014.html |
| Đội tàu Vinalines | 76 tàu của 9 DN, STBH hơn 565 triệu USD | https://www.pvn.vn/bao-hiem-pvi-ky-thoa-thuan-khung-voi-vinalines-5860 |

**Mô tả định tính:** sức khỏe PVI chủ yếu là bảo hiểm nhóm doanh nghiệp (FPTS, báo cáo định giá PVI 04/2025: https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf, trang 14).

## 9. Đơn vị của Bảo hiểm PVI (danh mục `ref.company`)

Tra cứu 19/10/2026; nghiên cứu chéo bằng codex CLI (gpt-6.1-sol) và agy CLI (gemini-3.8-flash-high), mọi link đã kiểm lại bằng curl.

| Nội dung | Số liệu | Nguồn |
|---|---|---|
| Tổng Công ty Bảo hiểm PVI (PVI Insurance) là công ty con 100% của CTCP PVI (PVI Holdings, mã PVI – HNX) | 100% tại 31/12/2024 | BCTN PVI 2024, trang PDF 12 (in 22–23): https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf |
| Các công ty con khác của Holdings: Tái bảo hiểm Hà Nội (Hanoi Re, tên cũ PVI Re) 81,09%; Quản lý Quỹ PVI (PVIAM) 61,96% | Doanh thu 2024: Holdings hợp nhất 21.824 tỷ; PVI Insurance 20.405 tỷ (93,5%); Hanoi Re 3.017,3 tỷ; PVIAM 57,4 tỷ | BCTN 2024, trang PDF 12, 22, 29, 30, 31 (link trên); đổi tên: https://www.hanoire.com/vi/pvi-re-chinh-thuc-doi-ten-thanh-hanoi-re |
| Năm 2025: doanh thu hợp nhất Holdings 28.923 tỷ; Bảo hiểm PVI 27.258 tỷ (94,2%), trong đó phí bảo hiểm gốc 14.908 tỷ; Hanoi Re 3.690 tỷ; PVIAM 76,4 tỷ | 94,2% = 27.258 / 28.923 **[tính]** | BCTN PVI 2025, trang PDF 29, 32, 33, 34: https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf |
| PVI Sài Gòn tự công bố "có doanh thu đứng đầu trong hệ thống bán lẻ của Bảo hiểm PVI" | — | https://pvisg.net |
| 47 đơn vị của Bảo hiểm PVI (46 công ty thành viên + Bảo hiểm PVI Phía Nam), có địa chỉ trụ sở → tỉnh của đơn vị | 47 | https://www.pvi.com.vn/vi/network |
| Bảo hiểm PVI Digital là chi nhánh của Tổng Công ty | — | https://online.pvi.com.vn/lien-he |
| Đơn vị được vinh danh: Phía Nam (xuất sắc nhất 2024); Thủ Đô (6 tháng 2025); Duyên Hải (2025); Thủ Đô và Thăng Long hoàn thành sớm kế hoạch 2025 | — | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-mot-nam-vuot-song-chinh-phuc-nhung-cot-moc-moi-681b4f9737783 ; https://www.pvi.com.vn/en/news/bao-hiem-pvi-doi-moi-sang-tao-va-thanh-cong ; https://vnexpress.net/nhung-yeu-to-giup-doanh-thu-bao-hiem-pvi-vuot-1-ty-usd-5011267.html ; https://www.pvi.com.vn/vi/news/pvi-thu-do-va-pvi-thang-long-hai-don-vi-tiep-theo-duoc-vinh-danh-hoan-thanh-som-ke-hoach-kinh-doanh-nam-2025 |

**KHÔNG TÌM THẤY:** doanh thu từng đơn vị thành viên, tỷ trọng trụ sở chính so với đơn vị. → **[ƯỚC TÍNH]** trọng số khai thác của đơn vị theo quy mô kinh tế địa bàn, ×1,5 cho 5 đơn vị được vinh danh / tự công bố dẫn đầu (Phía Nam, Thủ Đô, Duyên Hải, Thăng Long, Sài Gòn) (`build_v2.COMPANIES`). Phạm vi POC là Tổng Công ty Bảo hiểm PVI; Hanoi Re (nhận tái bảo hiểm) và PVIAM (quản lý quỹ) không cấp hợp đồng bảo hiểm gốc nên không có trong `ref.company`.

## 10. Bảo hiểm vi mô / nhúng theo giao dịch của PVI (2024–2026)

| Sản phẩm | Phí | Nguồn |
|---|---|---|
| Green SM Care (Xanh SM Care) — tai nạn hành khách theo chuyến; PVI Digital là 1 trong 5 nhà bảo hiểm (PVI Digital, OPES, BIC, TCGI, MIC) | 1.000 đ/chuyến Bike, 2.000 đ/chuyến Taxi | https://www.greensm.com/vn-vi/bao-hiem-khach-hang ; https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Food Care — Green SM × Bảo hiểm PVI, theo đơn giao đồ ăn; tai nạn 150 triệu đ/đơn | 1.000 đ/đơn | https://www.greensm.com/vn-vi/bao-hiem-giao-do-an |
| DelayCare — PVI × ATADI, ra mắt 20/08/2026, đơn vị cung cấp PVI Thủ Đô; trễ ≥ 120 phút trả 500.000 đ/người | Phí: KHÔNG TÌM THẤY | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-ra-mat-delaycare-giai-phap-bao-hiem-tre-chuyen-bay-danh-cho-hanh-khach |
| Bảo hiểm thiết bị điện tử khi mua trên Shopee / Lazada (PVI qua Fuse, PasarPolis) | Ví dụ 38.102 đ/12 tháng (nguồn thứ cấp) | https://help.shopee.vn/portal/4/article/79225 ; https://magiamgia.com/bao-hiem-thiet-bi-dien-tu-lazada/ |
| Đối tác số của PVI Digital: MoMo, Viettel Money, Shopee, Lazada, FE Credit, Home Credit, Xanh SM, Grab, Trip.com, Thế Giới Di Động, Điện Máy Xanh — "hàng triệu khách hàng" | — | https://www.pvi.com.vn/vi/news/pvi-digital-doi-tac-bao-hiem-so-cua-cac-nen-tang-va-he-sinh-thai-so-hang-dau-viet-nam |
| Quy mô Green SM: vượt 1 triệu chuyến/ngày (2025, nguồn thứ cấp) | > 1.000.000 chuyến/ngày | https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam |
| Tham chiếu sản lượng vi mô ở Việt Nam: OPES phát hành 109,3 triệu hợp đồng năm 2023, cao điểm > 500.000 đơn/ngày | — | https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154 |
| TMĐT của Bảo hiểm PVI: gần 800 tỷ (2024, 30 kết nối API); 2025 gần gấp đôi 2024 | — | BCTN 2024 trang PDF 29 (link mục 9); https://pviholdings.com.vn/vi/news-details?id=6013 |

**Lưu ý về Grab, Be:** bảo hiểm chuyến đi của Grab (Ride Cover, 2.000 đ) do **Chubb** cung cấp, của Be do **OPES** — không phải PVI (bài tinnhanhchungkhoan ở trên). Hợp tác Grab × PVI năm 2026 là chương trình BHXH/BHYT tự nguyện cho tài xế (https://www.grab.com/vn/blog/driver/bhxh-bhyt-pvi/), không phải bảo hiểm theo cuốc. Vì vậy POC dùng **Green SM** làm đối tác bảo hiểm theo chuyến.

**KHÔNG TÌM THẤY:** số GCN vi mô PVI phát hành theo ngày / năm; tỷ lệ khách chọn mua Green SM Care; số đơn Food Care; phí DelayCare. → **[ƯỚC TÍNH]** trong `gen_volume.MICRO`: 40.000 GCN chuyến xe/ngày (1 triệu chuyến × 20% mua × 20% về PVI), 8.000 GCN Food Care/ngày, 300 GCN DelayCare/ngày (phí 35.000 đ/người ≈ 4% xác suất trễ ≥ 2 giờ × 500.000 đ ÷ tỷ lệ bồi thường 60%), 3.000 GCN thiết bị điện tử/ngày (phí 1,5–3,5% giá máy). Các số này là quy ước để đạt khối lượng giao dịch của POC, có kiểm tra độ hợp lý với quy mô Green SM và OPES.
