# Hỏi đáp: Tại sao dữ liệu nguồn được thiết kế và sinh như vậy

Sinh tự động từ `scripts/why_meta.py` bởi `scripts/build_learning.py`. Nhãn: **[Nghiệp vụ]** có căn cứ; **[Giả định]** nêu cơ sở và lý do phạm vi POC; **[Ngẫu nhiên]** chỉ một câu. Mã nguồn (F1, P3…) tra ở bảng Nguồn cuối trang; trang PDF ghi kèm.

## Thiết kế bảng

**[Nghiệp vụ] Vì sao dữ liệu nguồn chia thành 5 bảng giao dịch: hợp đồng, giao dịch, dòng phí theo sản phẩm, đồng bảo hiểm, phân bổ doanh thu?**


Mỗi bảng ứng với một quy tắc nghiệp vụ mà doanh thu bắt buộc phải theo:

- Hợp đồng là đơn vị giao kết pháp lý (Luật KDBH 2022).
- Doanh thu phát sinh theo từng giao dịch (cấp mới, tái tục, sửa đổi, hoàn, hủy), mỗi loại một tài khoản (NĐ 46/2023 Điều 49; TT 232/2012) → bảng giao dịch.
- Doanh thu phải tách theo nghiệp vụ (TT 232 Điều 12; Mẫu 2-PNT của TT 67) → bảng dòng phí theo sản phẩm.
- Đồng bảo hiểm: mỗi DN chỉ ghi phần của mình (TT 232 Điều 19) → bảng tỷ lệ đồng bảo hiểm.
- Đề bài phân tích theo Công ty / Đơn vị, mà đơn vị cấp đơn chưa chắc là đơn vị được ghi doanh thu → bảng phân bổ.

Cấu trúc hợp đồng → giao dịch → dòng phí là cấu trúc chuẩn của ACORD, Microsoft CDM, OMG. Các dataset bảo hiểm public cũng tách tương tự: fremotor1prem0304 ghi phí theo từng quyền lợi trên một hợp đồng; Synthea tách bên bảo hiểm (payers), thời gian tham gia (payer_transitions) và giao dịch (claims_transactions); CAS Schedule P tách phí toàn bộ với phần giữ lại.


*Nguồn:* [S1](https://vbpl.vn/van-ban/chi-tiet/luat-kinh-doanh-bao-hiem-so-08-2022-qh15--163515); [S3](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441); [S11](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-232-2012-tt-btc-huong-dan-ke-toan-ap-dung-doi-voi-doanh-nghiep-bao-hiem-phi-nhan-tho-doanh-nghiep-tai-bao-hiem-va-chi-nhanh-doanh-nghiep-bao-hiem-phi-nhan-tho-nuoc-ngoai--30429); [S5](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-67-2023-tt-btc-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-nghi-dinh-so-46-2023-nd-cp-ngay-01-thang-7-nam-2023-cua-chinh-phu-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163439); [T1](https://modelviewers.pilotfishtechnology.com/modelviewers/ACORD-PCS/model/codelists/CycleBusinessPurpose.html); [T4](https://learn.microsoft.com/en-us/common-data-model/schema/core/industrycommon/financialservices/propertyandcasualtydatamodel/overview); [D1](https://github.com/dutangc/CASdatasets/blob/master/man-md/fremotor1prem0304a.md); [D6](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary); [D3](https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p)

**[Nghiệp vụ] Vì sao không gộp tất cả vào một bảng phẳng cho đơn giản?**


Một hợp đồng có nhiều giao dịch theo thời gian và nhiều sản phẩm. Bảng phẳng sẽ lặp thông tin hợp đồng trên mỗi dòng; khi có sửa đổi hay hoàn phí thì không cộng được doanh thu đúng kỳ.


Kimball đặt độ chi tiết của fact bảo hiểm ở mức giao dịch × coverage — đúng bằng bảng dòng phí theo sản phẩm. Lớp phân tích sẽ làm phẳng sau, từ dữ liệu nguồn này.


*Nguồn:* [T3](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/multiple-currencies/)

**[Nghiệp vụ] Vì sao đồng bảo hiểm là một bảng riêng, không chỉ là một cột tỷ lệ trên hợp đồng?**


Một hợp đồng lớn có thể có 3–6 doanh nghiệp, ví dụ liên danh 3 DN ở gói hàng không Vietnam Airlines và 6 DN ở nhà ga Long Thành. Mỗi DN có vai trò đứng đầu hoặc tham gia.


Bảng riêng giúp kiểm tra tổng = 100% và biết ai đứng đầu. Dòng của chính công ty (OWN) là căn cứ tính doanh thu. Mô hình OMG cũng tách 'Policy Amount' theo phần tham gia.


*Nguồn:* [P7](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615); [P12](https://baodauthau.vn/lien-danh-6-thanh-vien-trung-goi-thau-bao-hiem-cang-hkqt-long-thanh-post136014.html); [S11](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-232-2012-tt-btc-huong-dan-ke-toan-ap-dung-doi-voi-doanh-nghiep-bao-hiem-phi-nhan-tho-doanh-nghiep-tai-bao-hiem-va-chi-nhanh-doanh-nghiep-bao-hiem-phi-nhan-tho-nuoc-ngoai--30429); [T4](https://learn.microsoft.com/en-us/common-data-model/schema/core/industrycommon/financialservices/propertyandcasualtydatamodel/overview)

**[Giả định] Vì sao có bảng phân bổ doanh thu cho đơn vị? Luật đâu có bắt buộc?**


Đúng, luật không bắt buộc. Đây là thông lệ quản trị, được ghi là giả định.


Cơ sở: DNBH lớn tổ chức theo mô hình Tổng công ty → công ty thành viên (PVI 47 công ty, Bảo Việt 79 công ty). Khi đó đơn vị cấp đơn có thể khác đơn vị được ghi doanh thu, ví dụ trụ sở khai thác cùng công ty địa bàn, hoặc kênh số chuyển doanh thu về công ty quản lý khách.


Lý do phạm vi POC: đề bài có cấp Tổng công ty → Công ty. Nếu chỉ dùng đơn vị cấp đơn thì không thể hiện được tình huống 'doanh thu công ty X khác tổng phí các đơn X cấp' — câu hỏi hay gặp khi đối soát.


*Nguồn:* [P8](https://www.pvi.com.vn/vi/services/mang-luoi); [P14 · trang 127](https://static2.vietstock.vn/vietstock/2025/4/22/20250422_bvh_250422_integrated_report_2024.pdf); B1

**[Nghiệp vụ] Vì sao có 16 bảng danh mục?**


Mỗi chiều phân tích của đề bài cần danh mục riêng, và mã lấy từ văn bản pháp luật:

- Thời gian: tỷ giá theo tháng (KBNN).
- Kênh: kênh (Luật KDBH Điều 87) và đối tác.
- Nghiệp vụ: nghiệp vụ (NĐ 46) và dòng báo cáo (TT 67, Mẫu 2-PNT).
- Sản phẩm: nhóm sản phẩm và sản phẩm.
- Đơn vị: đơn vị, tỉnh (NQ 202/2025, 34 tỉnh), miền.
- Khách hàng: khách hàng và phân khúc.

Thêm 4 danh mục phục vụ công thức doanh thu: loại giao dịch (dấu, tài khoản TT 232), doanh nghiệp đồng bảo hiểm, loại phân bổ, tiền tệ.


*Nguồn:* [S1](https://vbpl.vn/van-ban/chi-tiet/luat-kinh-doanh-bao-hiem-so-08-2022-qh15--163515); [S3](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441); [S5](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-67-2023-tt-btc-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-nghi-dinh-so-46-2023-nd-cp-ngay-01-thang-7-nam-2023-cua-chinh-phu-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163439); [S12](https://vbpl.vn/van-ban/chi-tiet/nghi-quyet-so-202-2025-qh15-ve-viec-sap-xep-don-vi-hanh-chinh-cap-tinh--179501); [S11](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-232-2012-tt-btc-huong-dan-ke-toan-ap-dung-doi-voi-doanh-nghiep-bao-hiem-phi-nhan-tho-doanh-nghiep-tai-bao-hiem-va-chi-nhanh-doanh-nghiep-bao-hiem-phi-nhan-tho-nuoc-ngoai--30429); [F5](https://thuvienphapluat.vn/van-ban/Tien-te-Ngan-hang/Thong-bao-7727-TB-KBNN-2024-ty-gia-hach-toan-ngoai-te-thang-01-nam-2025-641872.aspx); B1

**[Nghiệp vụ] Vì sao cháy nổ vừa thuộc nhóm 'Tài sản' vừa có dòng báo cáo riêng?**


Đề bài gộp cháy nổ vào nhóm Tài sản, còn báo cáo gửi Bộ Tài chính tách cháy nổ thành dòng B.5 (NĐ 46 Điều 4; TT 67 Mẫu 2-PNT). Mô hình giữ cả hai cách phân loại: vừa phân tích theo đề bài, vừa đối chiếu được với báo cáo pháp định.


*Nguồn:* B1; [S3](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441); [S5](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-67-2023-tt-btc-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-nghi-dinh-so-46-2023-nd-cp-ngay-01-thang-7-nam-2023-cua-chinh-phu-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163439)

## Con số doanh thu

**[Giả định] Vì sao doanh thu tháng 8–9/2026 trên DB (reportapi) là khoảng 6.200 tỷ, lớn hơn quy mô PVI?**


Bước 1 — quy mô PVI: mục tiêu năm theo BCTC PVI 2025 (10.377,9 tỷ cho 4 nghiệp vụ) × tỷ trọng tháng 8 và 9 của toàn thị trường phi nhân thọ 2025 (Bộ Tài chính: 5.592 và 8.002 trên 88.054 tỷ, tức 15,44%) = khoảng 1.602 tỷ cho 2 tháng.


Bước 2 — hệ số quy mô k ≈ 3,93: yêu cầu dự án là trên 50.000 giao dịch mỗi ngày. Ở đúng quy mô PVI, với đơn giá theo biểu phí và giá niêm yết, chỉ được khoảng 13–25 nghìn giao dịch mỗi ngày. Vì vậy ngân sách của MỌI nhóm được nhân cùng một hệ số k để ngày thấp nhất đạt khoảng 53,6 nghìn giao dịch. Cơ cấu doanh thu giữ nguyên như PVI; đơn giá giữ nguyên; chỉ số hợp đồng và doanh thu tuyệt đối tăng.


Kết quả đo trên DB: phí gốc khai thác (cấp mới + tái tục đã duyệt) khoảng 6.300 tỷ = 1.602 × 3,93. Doanh thu ghi nhận trong tháng 8–9 khoảng 6.209 tỷ, vì khoảng 68 tỷ (chủ yếu du lịch mua trước chuyến đi) ghi nhận sau 30/9, và khoảng 22 tỷ là khoản giảm thu (sửa đổi giảm phí, hoàn phí, hủy).


Cơ cấu đo được: tài sản + cháy nổ 51,9% · con người 30,4% · xe 17,7%, so với BCTC PVI 51,5 / 31,0 / 17,6%.


Khi trình bày: doanh nghiệp giả lập lớn khoảng 3,9 lần PVI; chỉ cơ cấu và đơn giá là theo nguồn. Không trình bày số tuyệt đối như số liệu của PVI.


*Nguồn:* [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [S6](https://vbpl.vn/van-ban/chi-tiet/van-ban-hop-nhat-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-va-nghi-dinh-so-46-2023-nd-cp-so-44-2026-vbhn-tt-btc--035153a0-be3d-11f1-adb4-c9ac1aadd258); B1

**[Nghiệp vụ] Trong bộ v2 (mô hình năm 2024–2025), vì sao doanh thu 2025 là khoảng 10.237 tỷ?**


Mục tiêu 2025 = phí gốc 4 nghiệp vụ của PVI trong BCTC kiểm toán: con người 3.213,4; xe 1.822,7; cháy nổ 3.451,2; cộng 50% của dòng tài sản 3.781,2. Tổng là 10.377,9 tỷ.


Dữ liệu dummy đạt 10.237 tỷ (−1,4%). Phần chênh đến từ: sửa đổi giảm phí, hoàn phí, hủy (≈ −118 tỷ); đơn cấp cuối 2025 hiệu lực 2026, doanh thu chuyển sang năm sau (≈ 94 tỷ); chứng từ chưa duyệt không được tính.


*Nguồn:* [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [S6](https://vbpl.vn/van-ban/chi-tiet/van-ban-hop-nhat-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-va-nghi-dinh-so-46-2023-nd-cp-so-44-2026-vbhn-tt-btc--035153a0-be3d-11f1-adb4-c9ac1aadd258); [S3](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441)

**[Nghiệp vụ] Vì sao lấy quy mô của PVI mà không lấy bình quân thị trường?**


PVI đứng số 1 thị phần phi nhân thọ (16,93% năm 2025 theo Bộ Tài chính; BCTN PVI cũng khẳng định vị trí số 1). BCTC kiểm toán của PVI là nguồn công khai đáng tin nhất có tách phí theo từng nghiệp vụ.


Lý do phạm vi POC: doanh nghiệp giả lập 'DEMO' mang quy mô của DN dẫn đầu để POC chịu được tải dữ liệu thực tế. Số bình quân thị trường không ứng với doanh nghiệp cụ thể nào.


*Nguồn:* [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [P1 · trang 6](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf); [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf)

**[Nghiệp vụ] Vì sao cháy nổ chiếm khoảng 1/3 doanh thu, còn xe chỉ khoảng 18%?**


Đây là cơ cấu thật của PVI trong BCTC kiểm toán 2025: cháy nổ 3.451 tỷ, xe 1.823 tỷ. PVI thiên về khách hàng doanh nghiệp, công nghiệp (FPTS: hợp đồng lớn đến từ khách doanh nghiệp). Bình quân toàn thị trường thì xe chiếm khoảng 24%.


*Nguồn:* [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [P3 · trang 15](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026)

**[Giả định] Vì sao 'tài sản thuần' lấy 50% của dòng Tài sản trong BCTC?**


Cơ sở: dòng 'Property insurance' (3.781 tỷ) trong BCTC không tách riêng kỹ thuật và năng lượng. Nhưng PVI có nghiệp vụ năng lượng — BCTN 2024 nêu riêng cách trích dự phòng cho 'energy insurance' — và FPTS cho biết phần nhượng tái tập trung ở tài sản, kỹ thuật, thân tàu. Vậy dòng Property gồm cả tài sản thuần lẫn kỹ thuật, năng lượng.


Lý do phạm vi POC: đề bài chỉ có tài sản và cháy nổ, không có kỹ thuật hay năng lượng. Không có số tách, nên chọn 50% làm điểm giữa.


Ảnh hưởng: khoảng 1.891 tỷ, tức 18% doanh thu mục tiêu. Muốn đổi thì sửa 1 tham số rồi chạy lại.


*Nguồn:* [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [P1 · trang 57](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf); [P3 · trang 13](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf); B1

**[Giả định] Vì sao nhóm Con người chia sức khỏe 75 / sinh mạng–tai nạn 15 / du lịch 5 / học sinh 5?**


Cơ sở: FPTS cho biết bảo hiểm con người của PVI tập trung vào khách hàng doanh nghiệp, tức sức khỏe nhóm cho nhân viên với quyền lợi cao. Vì vậy sức khỏe phải chiếm phần lớn.


Du lịch và học sinh là bán lẻ phí rất nhỏ: du lịch từ 17.000 đ/chuyến, học sinh phổ biến 100.000 đ/em. Sinh mạng – tai nạn nằm ở giữa.


PVI không công bố tỷ lệ tách. Tổng Con người vẫn đúng số BCTC; chỉ cách tách bên trong là quy ước của dự án.


*Nguồn:* [P3 · trang 14](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf); [P5](https://online.pvi.com.vn/san-pham); [P6](https://cafef.vn/dau-nam-hoc-bo-100000-dong-mua-bao-hiem-than-the-cho-con-hang-trieu-phu-huynh-co-the-bo-qua-dieu-nay-188240923103450415.chn); [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf)

**[Nghiệp vụ] Vì sao trong nhóm Xe, TNDS bắt buộc chiếm 24% và vật chất xe 76%?**


Tính từ số toàn thị trường của IAV năm 2024: TNDS bắt buộc 4.537 tỷ trên tổng xe cơ giới 18.693 tỷ. PVI không công bố tỷ lệ riêng, nên dùng tỷ lệ thị trường (suy ra).


*Nguồn:* [F3](https://iav.vn/tong-quan,-so-lieu-thi-truong-bao-hiem/254773-254773-mot-so-hoat-dong-noi-bat-cua-thi-truong-bao-hiem-viet-nam-ca-nam-2024)

**[Nghiệp vụ] Vì sao có doanh thu tháng 01/2026, và vì sao có giao dịch mang số âm?**


Doanh thu ghi nhận khi phát sinh trách nhiệm bảo hiểm (TT 67 Điều 41): đơn cấp cuối tháng 12/2025 nhưng hiệu lực từ tháng 01/2026 thì doanh thu thuộc năm 2026.


Hoàn phí, giảm phí, hủy là khoản giảm thu (NĐ 46 Điều 49 khoản 3), hạch toán TK 5311 / 5321 (TT 232), nên mang số âm và ghi vào kỳ phát sinh.


*Nguồn:* [S6](https://vbpl.vn/van-ban/chi-tiet/van-ban-hop-nhat-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-va-nghi-dinh-so-46-2023-nd-cp-so-44-2026-vbhn-tt-btc--035153a0-be3d-11f1-adb4-c9ac1aadd258); [S3](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441); [S11](https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-232-2012-tt-btc-huong-dan-ke-toan-ap-dung-doi-voi-doanh-nghiep-bao-hiem-phi-nhan-tho-doanh-nghiep-tai-bao-hiem-va-chi-nhanh-doanh-nghiep-bao-hiem-phi-nhan-tho-nuoc-ngoai--30429)

## Phân phối

**[Giả định] Vì sao khách hàng cá nhân chiếm nhiều hợp đồng nhưng ít doanh thu?**


Nhiều hợp đồng: mỗi cá nhân tự mua cho mình — TNDS bắt buộc theo từng xe (NĐ 67), du lịch theo từng chuyến, sức khỏe theo từng người. Một doanh nghiệp thì gom hàng trăm nhân viên, hàng chục xe hoặc cả nhà máy vào một hợp đồng. Danh mục public cho thấy bán lẻ có số hợp đồng rất lớn: riêng freMTPL2 có 677.991 hợp đồng TNDS.


Ít doanh thu: phí mỗi đơn cá nhân nhỏ theo luật và giá niêm yết — TNDS ô tô 437.000 đ, xe máy 60.000 đ, du lịch từ 17.000 đ, sức khỏe cá nhân từ 1,45 triệu. Ngược lại, một đơn cháy nổ nhà máy có STBH hàng trăm tỷ × tỷ lệ tối thiểu 0,05–0,5% (NĐ 67 Phụ lục II), tức hàng trăm triệu đến hàng tỷ mỗi đơn.


Đặc thù PVI: FPTS cho biết mảng con người của PVI tập trung khách doanh nghiệp, khác các DN khác vốn tập trung khách cá nhân.


Phần giả định: tỷ lệ % cá nhân / tổ chức trong từng nhóm, vì không có số công bố theo loại khách hàng.


Trên DB: cá nhân chiếm khoảng 94% số hợp đồng nhưng khoảng 30% doanh thu; doanh nghiệp trong nước khoảng 2% số hợp đồng nhưng khoảng 43% doanh thu. (Bộ v2 có mức chênh rõ hơn thực tế — xem mục Giới hạn.)


*Nguồn:* [S8](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-67-2023-nd-cp-quy-dinh-ve-bao-hiem-bat-buoc-trach-nhiem-dan-su-cua-chu-xe-co-gioi-bao-hiem-chay-no-bat-buoc-bao-hiem-bat-buoc-trong-hoat-dong-dau-tu-xay-dung--163442); [P5](https://online.pvi.com.vn/san-pham); [D4](https://dutangc.github.io/CASdatasets/reference/freMTPL.html); [P3 · trang 14](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf)

**[Giả định] Vì sao sức khỏe nhóm chia DN trong nước 65 / FDI 25 / cơ quan nhà nước 10?**


Giả định theo thứ tự quy mô khối doanh nghiệp: DN trong nước nhiều nhất; sau đó là FDI (nhiều lao động, hay có phúc lợi bảo hiểm sức khỏe); cơ quan nhà nước ít nhất. Không có số công bố. Tỷ lệ này chỉ ảnh hưởng chiều Khách hàng, không ảnh hưởng tổng doanh thu.


*Nguồn:* không có số công bố — giả định của dự án

**[Giả định] Vì sao kênh trực tiếp và môi giới chiếm nhiều doanh thu nhất (trên DB: trực tiếp 33,7%, đại lý cá nhân 21,5%, môi giới 18,5%, bancassurance 9,5%, điện tử 6,2%)?**


Trực tiếp và môi giới cao vì PVI thiên về khách doanh nghiệp lớn (FPTS), mà hợp đồng doanh nghiệp thường khai thác trực tiếp hoặc qua môi giới. Môi giới toàn thị trường là 13,5% (Bộ Tài chính); với PVI dự án chọn cao hơn, khoảng 15–20%.


Điện tử: gần 800 tỷ năm 2024, khoảng 6% (BCTN PVI). Quý I/2025 kênh này tăng 1,8 lần (pvn.vn), nên khoảng 10% năm 2025.


Bancassurance: PVI mới mở rộng (hợp tác Nam A Bank); BCTN đặt định hướng phát triển môi giới và bancas. Dự án chọn 5–8%.


Phần giả định: trọng số từng kênh trong từng sản phẩm. Kênh không được hiệu chỉnh nên kết quả chỉ gần định hướng. Trên DB, kênh điện tử chiếm nhiều giao dịch (TNDS xe máy, tai nạn 24/24, du lịch) nhưng chỉ khoảng 6% doanh thu vì phí mỗi đơn nhỏ — thấp hơn mức khoảng 10% của PVI.


*Nguồn:* [P3 · trang 15](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [P1 · trang 29](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf); [P2](https://pvn.vn/khoi-dau-vung-chac-bao-hiem-pvi-huong-toi-moc-doanh-thu-ty-do-la-my-nam-2025-28459); [P9](https://www.pvi.com.vn/vi/news/bao-hiem-pvi-va-nam-a-bank-khoi-dong-hop-tac-kinh-doanh-tai-khu-vuc-mien-tay)

**[Nghiệp vụ] Trên DB, vì sao doanh thu và số giao dịch tháng 9 cao hơn tháng 8 khoảng 1,5 lần?**


Theo Bộ Tài chính, phí gốc phi nhân thọ toàn thị trường năm 2025 tháng 8 là 5.592 tỷ, tháng 9 là 8.002 tỷ, tức mỗi ngày tháng 9 cao hơn khoảng 1,48 lần. Ngân sách tháng của dữ liệu lấy theo tỷ trọng này; giả định PVI có mùa vụ giống thị trường.


Trên DB: tháng 8 khoảng 53,6–66,9 nghìn giao dịch/ngày, tháng 9 khoảng 80,4–100 nghìn. Học sinh còn tập trung quanh khai giảng 5/9; kênh văn phòng giảm cuối tuần và nghỉ lễ 01–02/9.


*Nguồn:* [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [S1](https://vbpl.vn/van-ban/chi-tiet/luat-kinh-doanh-bao-hiem-so-08-2022-qh15--163515)

**[Nghiệp vụ] Trong bộ v2, vì sao doanh thu quý 1 cao nhất?**


BCTC quý PVI Holdings: phí gốc 2025 theo quý là 29,7 / 24,1 / 24,8 / 21,4%. Lý do là các chương trình bảo hiểm doanh nghiệp (sức khỏe nhóm, tài sản, cháy nổ) thường tái tục đầu năm.


Học sinh đỉnh tháng 8–10 vì thu phí đầu năm học (CafeF). Hệ số theo tháng do dự án tự tinh chỉnh để khớp tỷ trọng theo quý.


*Nguồn:* [F2](https://pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/ce6f18e2-7a79-42f3-b6ab-2b79ea1e4077.pdf); [P6](https://cafef.vn/dau-nam-hoc-bo-100000-dong-mua-bao-hiem-than-the-cho-con-hang-trieu-phu-huynh-co-the-bo-qua-dieu-nay-188240923103450415.chn)

**[Giả định] Vì sao trên DB có khoảng 4,67 triệu hợp đồng trong 2 tháng, và tai nạn 24/24 chiếm khoảng một nửa?**


Số hợp đồng là hệ quả: ngân sách từng sản phẩm ÷ phí bình quân một hợp đồng (theo biểu phí, giá niêm yết). Ngân sách đã nhân hệ số k để đạt trên 50.000 giao dịch mỗi ngày.


Sản phẩm phí thấp nhất có nhiều hợp đồng nhất: tai nạn 24/24 (phí bình quân khoảng 56 nghìn đồng) chiếm khoảng 50% số hợp đồng, TNDS (xe máy 60 nghìn đồng) khoảng 25%, du lịch khoảng 10%. Ngược lại, cháy nổ chỉ 0,5% số hợp đồng nhưng khoảng 34% doanh thu. Tỷ trọng doanh thu của từng sản phẩm trong nhóm là giả định.


Bộ v2 (2 năm, khoảng 29 nghìn hợp đồng) gom bán lẻ thành đơn lô / nhóm nên ít hợp đồng hơn. Cả hai bộ đều không dùng để nói về số hợp đồng thật của PVI (PVI không công bố).


*Nguồn:* [P1 · trang 29](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf); [P6](https://cafef.vn/dau-nam-hoc-bo-100000-dong-mua-bao-hiem-than-the-cho-con-hang-trieu-phu-huynh-co-the-bo-qua-dieu-nay-188240923103450415.chn); [D4](https://dutangc.github.io/CASdatasets/reference/freMTPL.html)

**[Giả định] Vì sao doanh thu tập trung vào ít hợp đồng lớn (trên DB: 10% hợp đồng chiếm khoảng 93% doanh thu)?**


Doanh thu phi nhân thọ tập trung ở ít hợp đồng lớn, ví dụ gói hàng không Vietnam Airlines 540 tỷ, công trình Quảng Trạch I phí hơn 365 tỷ. Dự án mô phỏng bằng phân phối lệch phải của STBH; mức tập trung cụ thể là kết quả của giả định này.


Trên DB mức tập trung cao hơn bộ v2 (khoảng 75%) vì có hàng triệu hợp đồng bán lẻ phí rất nhỏ: 1% hợp đồng lớn nhất chiếm khoảng 74% doanh thu.


*Nguồn:* [P7](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615); [P11](https://www.tinnhanhchungkhoan.vn/bao-hiem-ban-buon-truoc-co-hoi-lon-post368348.html)

**[Giả định] Vì sao đồng bảo hiểm chỉ xảy ra với rủi ro từ 300 tỷ trở lên?**


Các hợp đồng đồng bảo hiểm được công bố đều là rủi ro rất lớn: hàng không Vietnam Airlines, nhà ga Long Thành, đội tàu Vinalines (STBH hơn 565 triệu USD). Ngưỡng 300 tỷ và tỷ lệ 55% là giả định để đồng bảo hiểm chỉ rơi vào nhóm rủi ro lớn.


*Nguồn:* [P7](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615); [P12](https://baodauthau.vn/lien-danh-6-thanh-vien-trung-goi-thau-bao-hiem-cang-hkqt-long-thanh-post136014.html); [P13](https://www.pvn.vn/bao-hiem-pvi-ky-thoa-thuan-khung-voi-vinalines-5860)

**[Giả định] Vì sao Hà Nội và TP.HCM có doanh thu lớn nhất?**


Đây là hai trung tâm kinh tế lớn nhất, tập trung trụ sở doanh nghiệp. Trọng số theo đơn vị là giả định.


*Nguồn:* không có số công bố — giả định của dự án

## Tham số ngẫu nhiên

| Tham số | Giải thích |
|---|---|
| Ngày cấp đơn trong tháng | Ngẫu nhiên đều trong tháng. |
| Giá xe, dư nợ, STBH, cỡ nhóm / lô | Ngẫu nhiên lệch phải trong khoảng hợp lý; tổng đã hiệu chỉnh về mục tiêu nên không đổi doanh thu nhóm. |
| Tỷ lệ phí trong khoảng (vd VCX 1,1–2,0%) | Ngẫu nhiên đều trong khoảng công bố hoặc khoảng hợp lý. |
| Trọng số loại xe, mức phí học sinh, tỷ lệ đơn USD | Chọn có trọng số; mức phí lấy từ biểu phí / giá niêm yết, còn trọng số là giả định. |
| Hệ số phí tái tục 0,95–1,12; biên độ sửa đổi 5–30% | Ngẫu nhiên đều quanh mức phí cũ. |
| Hoa hồng 50–100% trần | Ngẫu nhiên, luôn dưới trần luật định. |
| Tên khách hàng, mã số thuế, người tạo, giờ tạo | Sinh ngẫu nhiên, không trùng dữ liệu thật. |

## Nguồn và số trang

| Mã | Nguồn | Trang trong PDF |
|---|---|---|
| F1 | [BCTC kiểm toán 2025 Tổng công ty Bảo hiểm PVI — thuyết minh 21 (phí gốc theo nghiệp vụ 2024, 2025)](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf) | trang 45 — thuyết minh 21 'Insurance premium' (bản scan) |
| F2 | [BCTC hợp nhất quý PVI Holdings — thuyết minh 21, phí gốc theo quý (link: quý 4/2025)](https://pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/ce6f18e2-7a79-42f3-b6ab-2b79ea1e4077.pdf) | trang 31 — thuyết minh 21 'Tổng doanh thu' của BCTC hợp nhất quý 4/2025 (bản scan): phí gốc quý 4/2025 là 3.195,3 tỷ trên cả năm 14.908,2 tỷ = 21,4%. Quý 1–3 lấy ở cùng thuyết minh trong BCTC các quý tương ứng |
| P1 | [PVI Annual Report 2024](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf) | trang 6 (số 1 thị phần); trang 29 (kênh TMĐT gần 800 tỷ, 30 chương trình API, định hướng bán lẻ, môi giới, bancas); trang 57 (dự phòng riêng cho 'energy insurance') |
| P3 | [FPTS — báo cáo định giá lần đầu PVI (14/04/2025)](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf) | trang 7 (sức khỏe, xe là nghiệp vụ bán lẻ lớn nhất thị trường); trang 13 (nhượng tái tập trung ở tài sản, kỹ thuật, thân tàu); trang 14 (con người PVI tập trung khách doanh nghiệp); trang 15 (hợp đồng lớn từ khách doanh nghiệp) |
| P14 | [Bảo Việt Holdings — Integrated Report 2024](https://static2.vietstock.vn/vietstock/2025/4/22/20250422_bvh_250422_integrated_report_2024.pdf) | trang 127 (79 công ty thành viên) |
