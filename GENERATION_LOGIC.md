# Logic sinh dữ liệu: vì sao mỗi nghiệp vụ có bấy nhiêu đơn, bấy nhiêu tiền

Tài liệu này giải thích cách `build_v2.py` quyết định các tham số khi sinh dữ liệu:
- mỗi nhóm sản phẩm chiếm bao nhiêu % doanh thu;
- có bao nhiêu hợp đồng;
- mỗi hợp đồng bao nhiêu tiền;
- rơi vào tháng nào, qua kênh nào.

Mọi tham số đều **neo vào số liệu công khai**. Chỗ nào không có số công khai thì ghi rõ **[ƯỚC TÍNH]** kèm lý do. Kết quả ở các bảng là số **đo thật** trên dữ liệu đã sinh (năm 2025, chỉ giao dịch đã duyệt, phần của công ty). Mục 9 nói về bộ khối lượng lớn `gen_volume.py` (tháng 8–9/2026, có bảo hiểm vi mô); số ở đó đo trên DB (`docs/db_snapshot.json`).

> **Bản học đầy đủ:** [docs/Logic_Sinh_Du_Lieu.html](docs/Logic_Sinh_Du_Lieu.html) — sổ 74 tham số. Mỗi tham số có nhãn căn cứ (luật / số công bố / thông tin công khai / chuẩn ngành / dataset mẫu public / đề bài / suy ra / **giả định**), nguồn, vị trí code, và mức ảnh hưởng nếu giả định sai. Số liệu trong bản học được đo trực tiếp từ bộ sinh mỗi lần build. Sinh lại bằng lệnh `python scripts/build_learning.py`.

## 1. Nguyên tắc: doanh thu = tần suất × độ lớn

Mỗi nghiệp vụ bảo hiểm có một "dáng" riêng:

| Dáng | Ví dụ | Đặc điểm |
|---|---|---|
| **Rất nhiều đơn, mỗi đơn rất nhỏ** | TNDS xe máy 60.000 đ, du lịch nội địa từ 17.000 đ | Bán theo lô giấy chứng nhận qua đối tác |
| **Nhiều đơn, mỗi đơn vừa** | Vật chất ô tô 1,1–2% giá xe, sức khỏe cá nhân 1,5–15 triệu | Bán lẻ |
| **Ít đơn, mỗi đơn lớn** | Sức khỏe nhóm doanh nghiệp, cháy nổ nhà máy, mọi rủi ro tài sản | Vài trăm triệu đến hàng chục tỷ mỗi đơn |
| **Rất ít đơn, mỗi đơn cực lớn** (ngoài phạm vi POC) | Hàng không, năng lượng, công trình lớn | Hàng chục đến hàng trăm tỷ mỗi hợp đồng |

Vì vậy bộ sinh **không** chia đều tiền cho các đơn. Nó làm theo 3 bước:
1. Đặt doanh thu mục tiêu cho từng nhóm (bước 2).
2. Đặt "dáng" cho từng sản phẩm: cách tính phí, đơn lẻ / nhóm / lô (bước 3–4).
3. Co giãn quy mô các đơn nhóm/lô hoặc số tiền bảo hiểm để tổng doanh thu khớp mục tiêu (bước 5).

## 2. Bước 1: quy mô và cơ cấu doanh thu theo PVI

Nguồn: **báo cáo tài chính kiểm toán 2025 của Tổng công ty Bảo hiểm PVI, thuyết minh 21**, phí bảo hiểm gốc theo nghiệp vụ (https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf, trang 45 của file PDF).

| Nghiệp vụ (tỷ đồng) | 2024 | 2025 | % 2025 | Dáng | Trong POC? |
|---|---:|---:|---:|---|---|
| Tài sản & thiệt hại (gồm kỹ thuật, năng lượng) | 4.138,0 | 3.781,2 | 24,8% | Ít đơn, rất lớn | Một phần |
| Cháy nổ | 3.005,9 | 3.451,2 | 22,6% | Ít–vừa, lớn | ✅ |
| Sức khỏe & tai nạn con người | 2.220,7 | 3.213,4 | 21,1% | Nhiều (nhóm DN lớn) | ✅ |
| Xe cơ giới | 1.662,2 | 1.822,7 | 12,0% | Rất nhiều, nhỏ | ✅ |
| Thân tàu & P&I (hàng hải) | 1.130,7 | 1.221,9 | 8,0% | **Ít đơn, mỗi đơn rất nhiều tiền** | ✖ |
| Gián đoạn kinh doanh | 230,4 | 481,6 | 3,2% | Ít, lớn | ✖ |
| Hàng hóa vận chuyển | 365,5 | 429,2 | 2,8% | Nhiều giấy chứng nhận, nhỏ | ✖ |
| Trách nhiệm | 324,6 | 394,8 | 2,6% | Ít, vừa | ✖ |
| Hàng không | 434,2 | 388,5 | 2,5% | **Rất ít đơn, cực lớn** | ✖ |
| Tín dụng, nông nghiệp | 48,6 | 55,8 | 0,3% | — | ✖ |

**Mốc độ lớn của các nghiệp vụ ngoài phạm vi** (để so sánh, minh họa ví dụ hàng hải / hàng không):
- **Hàng không:** gói bảo hiểm đội bay Vietnam Airlines: liên danh Bảo Việt – PVI – Bảo Minh trúng thầu 540,2 tỷ, chỉ **1 hợp đồng** ([fireant.vn](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615); gói mời thầu khoảng 600 tỷ, [vietnambusinessinsider.vn](https://vietnambusinessinsider.vn/vietnam-airlines-mo-thau-goi-bao-hiem-lon-nhat-nam-voi-600-ty-dong-nhung-chi-co-mot-nha-thau-tham-gia-nop-ho-so-a49139.html)).
- **Công trình:** xây dựng Nhiệt điện Quảng Trạch I, phí trên 365 tỷ trên số tiền bảo hiểm khoảng 28.000 tỷ. Nhà ga Long Thành 118,9 tỷ, liên danh 6 công ty do PVI đứng đầu ([tinnhanhchungkhoan.vn](https://www.tinnhanhchungkhoan.vn/bao-hiem-ban-buon-truoc-co-hoi-lon-post368348.html); [baodauthau.vn](https://baodauthau.vn/lien-danh-6-thanh-vien-trung-goi-thau-bao-hiem-cang-hkqt-long-thanh-post136014.html) — trang này chặn tải tự động, chưa kiểm lại được số 118,9 tỷ).
- **Hàng hải:** đội tàu Vinalines 76 tàu, số tiền bảo hiểm 565 triệu USD. Phí **[ƯỚC TÍNH]** 0,3–0,8%/năm, tức khoảng 0,3–0,8 tỷ mỗi tàu ([pvn.vn](https://www.pvn.vn/bao-hiem-pvi-ky-thoa-thuan-khung-voi-vinalines-5860)).

### Mục tiêu doanh thu trong phạm vi POC

| Nhóm POC | Công thức | 2024 (tỷ) | 2025 (tỷ) |
|---|---|---:|---:|
| BH sức khỏe | Con người × **75%** | 1.665,5 | 2.410,1 |
| BH sinh mạng – tai nạn | Con người × **15%** | 333,1 | 482,0 |
| BH du lịch | Con người × **5%** | 111,0 | 160,7 |
| BH học sinh | Con người × **5%** | 111,0 | 160,7 |
| BH bắt buộc TNDS | Xe × **24%** | 398,9 | 437,4 |
| BH vật chất xe | Xe × **76%** | 1.263,3 | 1.385,3 |
| BH cháy nổ | = Cháy nổ | 3.005,9 | 3.451,2 |
| BH tài sản | Tài sản & thiệt hại × **50%** | 2.069,0 | 1.890,6 |
| **Tổng** | | **8.957,8** | **10.377,9** |

Căn cứ các tỷ lệ chia:
- **75 / 15 / 5 / 5 trong Con người — [ƯỚC TÍNH].** PVI không công bố số chia này. [Báo cáo định giá PVI của FPTS (04/2025), trang 14](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf) cho biết mảng sức khỏe của PVI chủ yếu là bảo hiểm nhóm doanh nghiệp, nên sức khỏe chiếm phần lớn. Du lịch và học sinh là sản phẩm bán lẻ phí nhỏ.
- **24 / 76 trong Xe.** Theo IAV 2024, TNDS bắt buộc là 4.537 trên tổng xe cơ giới 18.693 tỷ.
- **50% của Tài sản & thiệt hại — [ƯỚC TÍNH].** BCTC gộp tài sản với kỹ thuật và năng lượng. POC chỉ lấy phần tài sản thuần.

## 3. Bước 2: dáng của từng nhóm (kết quả năm 2025)

| Nhóm | Số đơn | % số đơn | % doanh thu | Phí trung vị / đơn | P90 / đơn | Lớn nhất | Người, xe bình quân / đơn | % đơn nhóm / lô | % đồng BH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TNDS bắt buộc | 2.493 | 16,0% | 4,3% | 1,7 tr | 495 tr | 3,1 tỷ | 891 | 48% | 0 |
| Vật chất xe | 3.785 | 24,3% | 13,4% | 20,5 tr | 915 tr | 14,4 tỷ | 33 | 21% | 0 |
| Học sinh | 344 | 2,2% | 1,6% | 356 tr | 1,2 tỷ | 2,0 tỷ | 2.134 | 86% | 0 |
| Du lịch | 1.546 | 9,9% | 1,6% | 1,5 tr | 190 tr | 3,9 tỷ | 525 | 42% | 0 |
| Sinh mạng – tai nạn | 1.494 | 9,6% | 4,7% | 1,8 tr | 694 tr | 16,3 tỷ | 138 | 26% | 0 |
| Sức khỏe | 2.553 | 16,4% | 23,3% | 13,8 tr | 3,0 tỷ | 7,7 tỷ | 209 | 46% | 2,9% |
| Tài sản | 1.193 | 7,7% | 18,4% | 86 tr | 3,9 tỷ | 40,5 tỷ | 1 | 0 | 10,2% |
| Cháy nổ | 2.179 | 14,0% | 33,3% | 299 tr | 4,1 tỷ | 59,1 tỷ | 1 | 0 | 7,2% |

Đọc bảng:
- **Cháy nổ và tài sản** chỉ chiếm 22% số đơn nhưng 52% doanh thu. Đây là dáng "ít đơn, nhiều tiền".
- **TNDS** chiếm 16% số đơn nhưng 4% doanh thu. Phí trung vị chỉ 1,7 triệu dù gần một nửa là đơn lô hàng trăm xe.
- **Toàn bộ dữ liệu:** 10% số hợp đồng lớn nhất chiếm **74%** doanh thu; 1% lớn nhất chiếm **25%**.

**Đơn nhóm / lô.** Đơn lẻ được định phí theo biểu phí hoặc giá niêm yết. Phần lớn doanh thu của TNDS, du lịch, học sinh và người vay vốn nằm ở **đơn lô hoặc đơn nhóm**: một hợp đồng gom nhiều giấy chứng nhận hoặc nhiều người được bảo hiểm. Ví dụ:
- bảng kê TNDS của trung tâm đăng kiểm;
- danh sách học sinh của một trường;
- bảng kê người vay của ngân hàng;
- danh sách khách bay của một OTA.

Đây là cách các hệ thống lõi bảo hiểm ghi nhận bán lẻ khối lượng lớn. Nhờ vậy số dòng dữ liệu vẫn vừa phải mà doanh thu vẫn đạt quy mô thật.

## 4. Bước 3: định phí từng sản phẩm

| Sản phẩm | Cách tính | Tham số | Căn cứ |
|---|---|---|---|
| TNDS bắt buộc ô tô | Biểu phí theo loại xe × số xe | 437.000 / 794.000 / 756.000 / 853.000 / 1.660.000 … (chưa VAT) | NĐ 67/2023 Phụ lục I |
| TNDS bắt buộc mô tô | Biểu phí × số xe | 55.000 / 60.000 / 290.000 (xe 3 bánh) | NĐ 67/2023 Phụ lục I |
| Vật chất xe ô tô | % × giá trị xe | Giá xe 0,4–3 tỷ (phân phối lệch phải); tỷ lệ 1,1–2,0% | PVI công bố 0,5–3,5% giá trị xe |
| Vật chất xe máy | % × giá trị xe | Giá xe 15–90 triệu; tỷ lệ 1,5–2,5% | [ƯỚC TÍNH] |
| Học sinh (tai nạn / sức khỏe) | Phí/người × số học sinh | 100–150 nghìn / 200–520 nghìn; mỗi trường 150–3.000 em | Báo chí: phổ biến 100.000 đ/em |
| Du lịch trong nước / quốc tế | Phí/người × số khách | 17–80 nghìn đ / 4–45 USD (70% hợp đồng tính bằng USD) | Giá niêm yết Bảo Việt, PVI Digital |
| Sinh mạng cá nhân, tai nạn 24/24 | % × số tiền bảo hiểm | STBH 20–500 triệu; tỷ lệ 0,1–0,5% | [ƯỚC TÍNH] |
| Người vay vốn | % × dư nợ; bảng kê 20–400 người vay | Dư nợ 0,1–3 tỷ; tỷ lệ 0,3–1% | Bán qua ngân hàng ([BIC bancassurance](https://bic.vn/vi/san-pham/bancassurance.html)); tính theo dư nợ và tỷ lệ [ƯỚC TÍNH] |
| Sức khỏe cá nhân | Phí/người | 1,45–15 triệu | Giá niêm yết (Bảo Việt An Gia từ 1,445 triệu; PVI Care) |
| Sức khỏe nhóm doanh nghiệp | Phí/người × 20–1.500 người | 2–8 triệu/người | [ƯỚC TÍNH], neo theo giá cá nhân |
| Nhà tư nhân | % × giá trị nhà | 0,3–5 tỷ; 0,05–0,1% | Giá niêm yết 220–270 nghìn/năm cho căn hộ / nhà |
| Mọi rủi ro tài sản / công nghiệp | % × STBH | STBH 10–5.000 tỷ (phân phối lệch phải); 0,05–0,2%; 20–40% tính bằng USD | [ƯỚC TÍNH] |
| Cháy nổ bắt buộc / tự nguyện | % tối thiểu theo nhóm cơ sở × STBH | 0,05% (chung cư) … 0,5% (chợ, gỗ); STBH 2–800 tỷ | NĐ 67/2023 Phụ lục II (bản 2023) |

## 5. Bước 4: hiệu chỉnh để khớp mục tiêu

Sau khi sinh hợp đồng theo các tham số trên, tổng doanh thu từng nhóm chưa khớp mục tiêu ở bước 1. Bộ sinh tính:

```
hệ số f = (mục tiêu − doanh thu đơn lẻ cố định) / doanh thu phần co giãn được
```

Sau đó nhân `f` vào:
- **số người / xe / giấy chứng nhận** của đơn nhóm và đơn lô;
- **số tiền bảo hiểm** của đơn tài sản và cháy nổ.

Đơn lẻ giữ nguyên biểu phí, nên TNDS vẫn đúng 437.000 đ/xe. Số đơn năm 2024 được co theo tăng trưởng doanh thu của từng nhóm.

Kết quả so với mục tiêu: 2025 đạt 10.237 / 10.378 tỷ (lệch 1,4%); 2024 đạt 8.845 / 8.958 tỷ (lệch 1,3%). Phần lệch còn lại đến từ 3 nguồn:
- SĐBS giảm phí, hoàn phí, hủy đơn;
- chứng từ PENDING / VOID bị loại;
- hợp đồng cấp cuối năm nhưng hiệu lực từ năm sau (doanh thu chuyển sang năm sau).

## 6. Bước 5: thời gian

**Theo quý.** PVI có quý 1 cao nhất vì các chương trình bảo hiểm doanh nghiệp tái tục đầu năm. Nguồn: phí gốc hợp nhất PVI theo quý trong BCTC quý PVI Holdings, thuyết minh 21 (ví dụ [quý 4/2025, trang 31](https://pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/ce6f18e2-7a79-42f3-b6ab-2b79ea1e4077.pdf)).

| Tỷ trọng theo quý | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| PVI 2025 (public) | 29,7% | 24,1% | 24,8% | 21,4% |
| Dữ liệu dummy 2025 | 28,3% | 23,0% | 26,4% | 22,3% |

**Theo tháng, trong từng nhóm:**
- Sức khỏe, tài sản, cháy nổ dồn vào tháng 1.
- Học sinh đỉnh tháng 8–10 (đầu năm học).
- Du lịch cao vào Tết (tháng 1–2) và hè (tháng 6–8).

**Ngày ghi nhận doanh thu** = max(ngày cấp, ngày bắt đầu hiệu lực), theo TT 67/2023 Điều 41. Độ trễ hiệu lực là 0–10 ngày; riêng du lịch 0–60 ngày (mua trước chuyến đi).

## 7. Bước 6: kênh, đơn vị, khách hàng

| Kênh (% doanh thu 2025) | Dummy | Mốc định hướng |
|---|---:|---|
| Bán trực tiếp | 37,0% | PVI thiên về khách hàng doanh nghiệp, công nghiệp: khoảng 67% doanh thu [suy ra từ BCTC] |
| Đại lý cá nhân | 18,5% | |
| Môi giới | 17,5% | Thị trường 13,5% (MOF 2025). PVI thiên DN lớn nên cao hơn [ƯỚC TÍNH 15–20%] |
| Giao dịch điện tử | 8,4% (2024: 5,7%) | PVI: kênh TMĐT khoảng 800 tỷ ≈ 6% năm 2024 ([BCTN 2024, trang 29](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf)); quý I/2025 tăng 1,8 lần ([pvn.vn](https://pvn.vn/khoi-dau-vung-chac-bao-hiem-pvi-huong-toi-moc-doanh-thu-ty-do-la-my-nam-2025-28459)) → ≈ 10% [suy ra] |
| Bancassurance | 8,0% | PVI mới mở rộng ([hợp tác Nam A Bank](https://www.pvi.com.vn/vi/news/bao-hiem-pvi-va-nam-a-bank-khoi-dong-hop-tac-kinh-doanh-tai-khu-vuc-mien-tay)) [ƯỚC TÍNH 5–8%] |
| Đại lý tổ chức | 7,8% | |
| Đấu thầu | 1,9% | Cơ quan nhà nước, dự án |
| Chưa khai báo | 0,9% | Dữ liệu bẩn có chủ đích |

**Đơn vị** (danh mục `ref.company`, cập nhật 19/10/2026; nguồn ở mục 9):
- Doanh nghiệp là **Tổng Công ty Bảo hiểm PVI** (PVI Insurance, công ty con 100% của CTCP PVI — BCTN 2024, trang PDF 12), không còn doanh nghiệp giả lập "DEMO".
- Đơn vị: **Trụ sở chính – các Ban kinh doanh** (`HO`), **Bảo hiểm PVI Digital** (`DGT`, TP.HCM) và 46 đơn vị thật theo trang mạng lưới (DGT + 46 = 47 đơn vị trên trang) pvi.com.vn (Đông Đô, Thăng Long, Hà Nội, …, Phía Nam). Tỉnh của đơn vị = địa chỉ trụ sở trên trang mạng lưới; tỉnh không có đơn vị được gán đơn vị gần nhất [QUY ƯỚC].
- Trọng số khai thác **[ƯỚC TÍNH]**: PVI không công bố doanh thu từng đơn vị. Trọng số theo quy mô kinh tế địa bàn (1–4), ×1,5 cho 5 đơn vị được PVI vinh danh hoặc tự công bố dẫn đầu: Phía Nam (xuất sắc nhất 2024), Thủ Đô (6 tháng 2025), Duyên Hải (xuất sắc nhất 2025), Thăng Long (hoàn thành sớm kế hoạch 2025), Sài Gòn (doanh thu đứng đầu hệ thống bán lẻ). Lớn nhất: Duyên Hải 6; Thăng Long, Thủ Đô, Sài Gòn, Phía Nam 4,5; Đông Nam Bộ 4. Gộp theo tỉnh, Hà Nội và TP.HCM vẫn lớn nhất vì có nhiều đơn vị.
- **Trụ sở chính** cấp 60% số rủi ro tài sản / cháy nổ có STBH ≥ 500 tỷ và 40% đơn sức khỏe nhóm trên 800 người.
- **Bảo hiểm PVI Digital** cấp 70% đơn kênh điện tử.
- Hanoi Re (tên cũ PVI Re, nhận tái bảo hiểm) và PVIAM (quản lý quỹ) là công ty con khác của PVI Holdings, không cấp hợp đồng bảo hiểm gốc nên **không** có trong `ref.company`.

**Đối tác:** đối tác cũ vẫn ẩn danh (Ngân hàng A, OTA A…). Ba đối tác số thật mới, có công bố hợp tác với PVI: Green SM, ATADI, Fuse (mục 9); giao dịch qua họ là giả lập.

**Khách hàng:**
- Theo nhóm: xe 80–85% cá nhân; sức khỏe nhóm là doanh nghiệp (25% FDI); cháy nổ 68% doanh nghiệp trong nước; nhà tư nhân là hộ gia đình.
- 20% đơn mới là khách hàng cũ quay lại.

## 8. Bước 7: các quy tắc khác

| Quy tắc | Tham số | Căn cứ |
|---|---|---|
| Đồng bảo hiểm | Tài sản / cháy nổ STBH ≥ 300 tỷ: 55% có đồng BH. Sức khỏe nhóm > 1.000 người: 30%. Đứng đầu (40%): công ty giữ 40–70%. Tham gia: 10–40% | Liên danh thực tế: [Vietnam Airlines 3 DN](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615), [Long Thành 6 DN](https://baodauthau.vn/lien-danh-6-thanh-vien-trung-goi-thau-bao-hiem-cang-hkqt-long-thanh-post136014.html) |
| Phân bổ doanh thu | Trụ sở chính: 60% hợp tác với đơn vị quản lý khách (Trụ sở giữ 50–70%). PVI Digital: 50% chuyển giao về đơn vị địa bàn. Đơn vị thành viên: 10% hợp tác (50–80%), 1% chuyển giao. GCN vi mô (bộ khối lượng lớn, mục 9): 100% cho đơn vị cấp | Thông lệ quản trị |
| SĐBS | 7% hợp đồng (trừ du lịch): tăng phí 30%, giảm phí 15%, hoàn phí 15%, hủy 25% (hoàn 90% phí thời gian còn lại), không đổi phí 15% | NĐ 46/2023 Điều 49 |
| Tái tục | 55% hợp đồng năm 2024 (sản phẩm năm, không phải đơn lô) được tái tục năm 2025, phí điều chỉnh 0,95–1,12 lần | [ƯỚC TÍNH] |
| Trạng thái | 98,5% APPROVED, 1% PENDING, 0,5% VOID | [ƯỚC TÍNH] |
| Ngoại tệ | Du lịch quốc tế 70% USD; mọi rủi ro tài sản 20%, công nghiệp 40% USD. Tỷ giá hạch toán KBNN theo tháng | [KBNN 2025](https://thuvienphapluat.vn/van-ban/Tien-te-Ngan-hang/Thong-bao-7727-TB-KBNN-2024-ty-gia-hach-toan-ngoai-te-thang-01-nam-2025-641872.aspx) |
| Hoa hồng | 50–100% trần theo nghiệp vụ, chỉ cho kênh trung gian | TT 67/2023 Điều 51 |
| VAT | 0% bảo hiểm con người; 10% xe, tài sản, cháy nổ | Luật GTGT 48/2024 |

## 9. Bộ khối lượng lớn: bảo hiểm vi mô, quy mô và phân phối doanh thu

Bộ khối lượng lớn (`gen_volume.py`, tháng 8–9/2026, nạp vào `bronze.ins_*`) dùng cùng mục tiêu nhóm ở bước 1 × tỷ trọng tháng của Bộ Tài chính, và cùng tỷ trọng sản phẩm trong nhóm (`build_v2.PRODUCT_MIX`, một nguồn duy nhất). Từ 19/10/2026 **không nhân hệ số quy mô**: doanh thu đúng quy mô PVI, còn yêu cầu > 50.000 giao dịch/ngày được đáp ứng bằng **bảo hiểm vi mô** theo chuyến / theo đơn. Tham số đầy đủ: [calibration/README.md](calibration/README.md).

### Sản phẩm vi mô

| Mã | Sản phẩm | Nhóm | Phí / GCN | Số GCN/ngày | Đơn vị cấp · đối tác |
|---|---|---|---|---:|---|
| `MV_XSM_CARE` | Tai nạn hành khách theo chuyến (Green SM Care) | Sinh mạng – tai nạn | 1.000 đ Bike / 2.000 đ Taxi **[NGUỒN]** greensm.com | 40.000 **[ƯỚC TÍNH]**: Green SM > 1 triệu chuyến/ngày × 20% chuyến mua bảo hiểm × 20% về PVI (1 trong 5 nhà bảo hiểm) | PVI Digital · Green SM |
| `MV_FOOD_CARE` | Bảo hiểm đơn giao đồ ăn (Food Care) | Sinh mạng – tai nạn | 1.000 đ/đơn **[NGUỒN]** greensm.com | 8.000 **[ƯỚC TÍNH]**: số đơn không công bố, giá trị quy ước của POC | PVI Digital · Green SM |
| `MV_DELAYCARE` | Trễ chuyến bay (DelayCare), từ 20/08/2026 | Du lịch | 35.000 đ/người **[ƯỚC TÍNH]**: ≈ 4% xác suất trễ ≥ 2 giờ × 500.000 đ ÷ tỷ lệ bồi thường 60% (mức chi trả 500.000 đ là [NGUỒN] pvi.com.vn) | 300 **[ƯỚC TÍNH]**: quy ước của POC | PVI Thủ Đô (nguồn ghi đơn vị cung cấp) · ATADI |
| `MV_TBDT_TMDT` | Thiết bị điện tử mua trên sàn TMĐT | Tài sản | 1,5–3,5% giá máy **[ƯỚC TÍNH]**, neo ví dụ 38.102 đ/12 tháng (help.shopee.vn) | 3.000, ×3 ngày 8/8, 9/9 **[ƯỚC TÍNH]** | PVI Digital · Fuse |

Kênh luôn là giao dịch điện tử qua đối tác; khách là người dùng app (kho riêng 1,5 triệu người); GCN chuyến xe, đồ ăn hiệu lực trong ngày. Grab **không** dùng làm đối tác: bảo hiểm chuyến đi của Grab do Chubb cung cấp, của Be do OPES; hợp tác Grab × PVI năm 2026 là BHXH/BHYT tự nguyện cho tài xế.

### Quy mô

Doanh thu vi mô nằm **trong** ngân sách nhóm (sinh mạng, du lịch, tài sản). Ở bước hiệu chỉnh (mục 5), dòng vi mô được coi là **cố định** giống đơn bán lẻ; phần đơn doanh nghiệp / nhóm còn lại được co giãn, nên tổng từng nhóm và cơ cấu tài sản + cháy nổ / con người / xe không đổi.

Số đo trên DB (`docs/db_snapshot.json`, 19/10/2026): phí gốc khai thác tháng 8–9 **1.600,6 tỷ** so với ngân sách 10.377,9 × 13.594 / 88.054 ≈ 1.602 tỷ; cơ cấu 51,5 / 31,0 / 17,5% (đã tính). Giao dịch/ngày tháng 8: 57.722–69.201 (bình quân 63.923); tháng 9: 62.635–77.822 (bình quân 70.559).

### Phân phối

Doanh thu = doanh thu ghi nhận tháng 8–9 theo sản phẩm (1.577,9 tỷ); tỷ lệ và phí bình quân là số tự tính.

| Phần | Số hợp đồng / GCN | % số HĐ | Doanh thu (tỷ) | % doanh thu | Phí bình quân |
|---|---:|---:|---:|---:|---:|
| `MV_XSM_CARE` | 2.431.497 | 59,6% | 3,36 | 0,21% | 1.383 đ |
| `MV_FOOD_CARE` | 516.750 | 12,7% | 0,51 | 0,03% | 988 đ |
| `MV_TBDT_TMDT` | 194.993 | 4,8% | 16,35 | 1,04% | 83.837 đ |
| `MV_DELAYCARE` | 12.749 | 0,3% | 0,62 | 0,04% | 48.739 đ/GCN (1–4 người × 35.000 đ) |
| **Vi mô** | **3.155.989** | **77,3%** | **20,84** | **1,32%** | |
| **Truyền thống** | **926.648** | **22,7%** | **1.557,0** | **98,68%** | ≈ 1,68 triệu đ |
| **Tổng** | **4.082.637** | 100% | **1.577,9** | 100% | |

Đọc bảng:
- Dáng "rất nhiều đơn, mỗi đơn rất nhỏ" (mục 1) nay có thêm một tầng cực đoan: 10% hợp đồng lớn nhất chiếm **97,7%** doanh thu, 1% lớn nhất **80,1%** (lần nạp trước trên DB, chưa có vi mô: 93% / 74%; v2 năm 2025 ở mục 3: 74% / 25%).
- Nhóm sinh mạng có 3.298.699 hợp đồng (chủ yếu GCN vi mô) nhưng chỉ ≈ 74 tỷ phí gốc. Đây là đặc trưng thật của bảo hiểm nhúng: OPES phát hành 109,3 triệu hợp đồng năm 2023.
- Dashboard nên tách "số giao dịch" và "doanh thu", và lọc riêng sản phẩm `MV_*` khi tính phí bình quân hoặc phân vị phí.

### Nguồn cho bảo hiểm vi mô và đơn vị

Nghiên cứu chéo bằng codex CLI (gpt-6.1-sol) và agy CLI (gemini-3.8-flash-high) với cùng một đề bài, đối chiếu kết quả hai bên; mọi link đã kiểm lại bằng curl ngày 19/10/2026. Mục bị loại: danh sách "7 đơn vị về đích sớm" (agy) không kiểm chứng được. Bản gốc: [sources/market_data.md](sources/market_data.md) mục 9, 10.

| Nội dung dùng | Số liệu | Nhãn | URL (trang) |
|---|---|---|---|
| Tổng Công ty Bảo hiểm PVI là công ty con 100% của CTCP PVI (PVI Holdings) | 100% tại 31/12/2024 | [NGUỒN] | BCTN PVI 2024, trang PDF 12: https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf |
| Các công ty con khác của Holdings; doanh thu 2024 | Hanoi Re 81,09%, PVIAM 61,96%; Holdings 21.824 tỷ, PVI Insurance 20.405 tỷ, Hanoi Re 3.017,3 tỷ, PVIAM 57,4 tỷ | [NGUỒN] | BCTN PVI 2024, trang PDF 12, 22, 29, 30, 31 (link trên) |
| Hanoi Re là tên mới của PVI Re | — | [NGUỒN] | https://www.hanoire.com/vi/pvi-re-chinh-thuc-doi-ten-thanh-hanoi-re |
| Doanh thu 2025 của Holdings và các công ty con | Holdings 28.923 tỷ; Bảo hiểm PVI 27.258 tỷ (phí gốc 14.908 tỷ); Hanoi Re 3.690 tỷ; PVIAM 76,4 tỷ | [NGUỒN] | BCTN PVI 2025, trang PDF 29, 32, 33, 34: https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf |
| Danh sách đơn vị, địa chỉ trụ sở → tỉnh | 47 đơn vị: PVI Digital + 45 công ty thành viên + Phía Nam | [NGUỒN] | https://www.pvi.com.vn/vi/network |
| Bảo hiểm PVI Digital là chi nhánh của Tổng Công ty | — | [NGUỒN] | https://online.pvi.com.vn/lien-he |
| PVI Sài Gòn tự công bố doanh thu đứng đầu hệ thống bán lẻ | — | [NGUỒN] | https://pvisg.net |
| Đơn vị được vinh danh (Phía Nam 2024; Thủ Đô 6T/2025; Duyên Hải 2025; Thủ Đô, Thăng Long hoàn thành sớm kế hoạch 2025) | Hệ số ×1,5 suy ra từ đây là **[ƯỚC TÍNH]** | [NGUỒN] | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-mot-nam-vuot-song-chinh-phuc-nhung-cot-moc-moi-681b4f9737783 ; https://www.pvi.com.vn/en/news/bao-hiem-pvi-doi-moi-sang-tao-va-thanh-cong ; https://vnexpress.net/nhung-yeu-to-giup-doanh-thu-bao-hiem-pvi-vuot-1-ty-usd-5011267.html ; https://www.pvi.com.vn/vi/news/pvi-thu-do-va-pvi-thang-long-hai-don-vi-tiep-theo-duoc-vinh-danh-hoan-thanh-som-ke-hoach-kinh-doanh-nam-2025 |
| Green SM Care; PVI Digital là 1 trong 5 nhà bảo hiểm (PVI Digital, OPES, BIC, TCGI, MIC) | 1.000 đ/chuyến Bike, 2.000 đ/chuyến Taxi | [NGUỒN] | https://www.greensm.com/vn-vi/bao-hiem-khach-hang ; https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Food Care (Green SM × Bảo hiểm PVI) | 1.000 đ/đơn; tai nạn 150 triệu đ/đơn | [NGUỒN] | https://www.greensm.com/vn-vi/bao-hiem-giao-do-an |
| DelayCare (PVI × ATADI, ra mắt 20/08/2026, đơn vị cung cấp PVI Thủ Đô) | Trễ ≥ 120 phút trả 500.000 đ/người; phí KHÔNG TÌM THẤY | [NGUỒN] | https://www.pvi.com.vn/vi/news/bao-hiem-pvi-ra-mat-delaycare-giai-phap-bao-hiem-tre-chuyen-bay-danh-cho-hanh-khach |
| Bảo hiểm thiết bị điện tử trên Shopee / Lazada (PVI qua Fuse, PasarPolis) | Ví dụ 38.102 đ/12 tháng (nguồn thứ cấp) | [NGUỒN] | https://help.shopee.vn/portal/4/article/79225 ; https://magiamgia.com/bao-hiem-thiet-bi-dien-tu-lazada/ |
| Đối tác số của PVI Digital (MoMo, Viettel Money, Shopee, Lazada, FE Credit, Home Credit, Xanh SM, Grab, Trip.com, Thế Giới Di Động, Điện Máy Xanh) | "hàng triệu khách hàng" | [NGUỒN] | https://www.pvi.com.vn/vi/news/pvi-digital-doi-tac-bao-hiem-so-cua-cac-nen-tang-va-he-sinh-thai-so-hang-dau-viet-nam |
| Quy mô Green SM | > 1 triệu chuyến/ngày (2025, nguồn thứ cấp) | [NGUỒN] | https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam |
| Sản lượng vi mô OPES | 109,3 triệu hợp đồng năm 2023; cao điểm > 500.000 đơn/ngày | [NGUỒN] | https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154 |
| TMĐT của Bảo hiểm PVI | Gần 800 tỷ năm 2024 (30 kết nối API); 2025 gần gấp đôi | [NGUỒN] | BCTN 2024 trang PDF 29 (link trên); https://pviholdings.com.vn/vi/news-details?id=6013 |
| Bảo hiểm chuyến đi của Grab do Chubb, của Be do OPES | — | [NGUỒN] | https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html |
| Grab × PVI 2026 là BHXH/BHYT tự nguyện cho tài xế | — | [NGUỒN] | https://www.grab.com/vn/blog/driver/bhxh-bhyt-pvi/ |

**[ƯỚC TÍNH]** (không có số công bố): số GCN vi mô/ngày, tỷ lệ mua 20% × 20% về PVI, phí DelayCare, phí thiết bị điện tử, trọng số khai thác từng đơn vị. Các số GCN/ngày là quy ước để đạt khối lượng giao dịch của POC, đã kiểm tra độ hợp lý với quy mô Green SM và OPES.

## 10. Quy ước chuẩn

- Các số **[ƯỚC TÍNH]** ở trên là **giá trị chuẩn** dự án đã chọn, với căn cứ ghi bên cạnh. Quan trọng nhất là cách chia trong nhóm Con người (75 / 15 / 5 / 5) và phần tài sản thuần (50%) trong "Tài sản & thiệt hại".
- Số hợp đồng của từng nhóm được chuẩn hóa theo nguyên tắc tần suất × độ lớn ở bước 2–3, vì PVI không công bố số hợp đồng. Tổng doanh thu khớp số công khai.
- Tỷ lệ phí cháy nổ bắt buộc lấy theo NĐ 67/2023 Phụ lục II làm chuẩn.
