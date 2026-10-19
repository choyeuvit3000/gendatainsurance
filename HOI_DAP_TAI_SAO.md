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


*Nguồn:* [P8](https://www.pvi.com.vn/vi/network); [P14 · trang 127](https://static2.vietstock.vn/vietstock/2025/4/22/20250422_bvh_250422_integrated_report_2024.pdf); B1

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

**[Giả định] Vì sao nạp lại dữ liệu không dùng lại khóa cũ (policy_id, txn_id, mã khách)?**


Dữ liệu trên reportapi được hệ thống phía sau đọc qua CDC và lưu lịch sử (lakehouse). Nếu lần nạp sau dùng lại policy_id hoặc txn_id cũ, một khóa sẽ trỏ tới hai hợp đồng khác nhau trong lịch sử — đối soát và gộp dữ liệu sẽ sai.


Vì vậy bộ sinh ghi bảng bronze.poc_key_watermark: mốc lớn nhất đã phát hành cho policy_id, txn_id, coverage_id, mã khách và số hợp đồng. Bảng này không bị DELETE khi nạp lại, nên dù bảng fact trống hay lần nạp trước bị dở, lần sau vẫn bắt đầu sau mọi khóa cũ.


Lần nạp cuối: khóa 60.000.001–64.082.637 (sau các dải đã dùng trước đó), mã khách KH610000001–KH690000048. Nạp lại với --replace còn đồng bộ danh mục theo khóa chính: dòng không đổi giữ nguyên để CDC không phát sự kiện thừa, dòng không còn dùng (đơn vị giả lập cũ) bị xóa.


*Nguồn:* không có số công bố — giả định của dự án

## Con số doanh thu

**[Nghiệp vụ] Vì sao doanh thu tháng 8–9/2026 trên DB (reportapi) là khoảng 1.578 tỷ?**


Ngân sách = đúng quy mô PVI: mục tiêu năm theo BCTC PVI 2025 (10.377,9 tỷ cho 4 nghiệp vụ) × tỷ trọng tháng 8 và 9 của toàn thị trường phi nhân thọ 2025 (Bộ Tài chính: 5.592 và 8.002 trên 88.054 tỷ, tức 15,44%) = khoảng 1.602 tỷ cho 2 tháng. Không nhân hệ số quy mô nào (bản trước có hệ số k ≈ 3,93, nay đã bỏ).


Kết quả đo trên DB: phí gốc khai thác (cấp mới + tái tục đã duyệt) 1.600,6 tỷ, lệch −0,1% so với ngân sách. Doanh thu ghi nhận trong tháng 8–9 là 1.577,9 tỷ, vì khoảng 16,7 tỷ (chủ yếu du lịch, DelayCare mua trước chuyến đi) ghi nhận sau 30/9, và khoảng 5,8 tỷ là khoản giảm thu (sửa đổi giảm phí, hoàn phí, hủy).


Cơ cấu đo được: tài sản + cháy nổ 52,0% · con người 30,4% · xe 17,6%, so với BCTC PVI 51,5 / 31,0 / 17,6%.


Trên 50.000 giao dịch mỗi ngày đến từ bảo hiểm vi mô (phí 1.000–2.000 đ/GCN cho chuyến xe, đồ ăn), chỉ chiếm khoảng 1,3% doanh thu — xem mục Bảo hiểm vi mô và đơn vị PVI.


*Nguồn:* [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [S6](https://vbpl.vn/van-ban/chi-tiet/van-ban-hop-nhat-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-va-nghi-dinh-so-46-2023-nd-cp-so-44-2026-vbhn-tt-btc--035153a0-be3d-11f1-adb4-c9ac1aadd258); B1

**[Nghiệp vụ] Trong bộ v2 (mô hình năm 2024–2025), vì sao doanh thu 2025 là khoảng 10.237 tỷ?**


Mục tiêu 2025 = phí gốc 4 nghiệp vụ của PVI trong BCTC kiểm toán: con người 3.213,4; xe 1.822,7; cháy nổ 3.451,2; cộng 50% của dòng tài sản 3.781,2. Tổng là 10.377,9 tỷ.


Dữ liệu dummy đạt 10.237 tỷ (−1,4%). Phần chênh đến từ: sửa đổi giảm phí, hoàn phí, hủy (≈ −118 tỷ); đơn cấp cuối 2025 hiệu lực 2026, doanh thu chuyển sang năm sau (≈ 94 tỷ); chứng từ chưa duyệt không được tính.


*Nguồn:* [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [S6](https://vbpl.vn/van-ban/chi-tiet/van-ban-hop-nhat-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-va-nghi-dinh-so-46-2023-nd-cp-so-44-2026-vbhn-tt-btc--035153a0-be3d-11f1-adb4-c9ac1aadd258); [S3](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441)

**[Nghiệp vụ] Vì sao lấy quy mô của PVI mà không lấy bình quân thị trường?**


PVI đứng số 1 thị phần phi nhân thọ (16,93% năm 2025 theo Bộ Tài chính; BCTN PVI cũng khẳng định vị trí số 1). BCTC kiểm toán của PVI là nguồn công khai đáng tin nhất có tách phí theo từng nghiệp vụ.


Lý do phạm vi POC: doanh nghiệp của POC là chính Tổng Công ty Bảo hiểm PVI với 47 đơn vị thật (trang mạng lưới PVI), nên quy mô phải là quy mô PVI. Số bình quân thị trường không ứng với doanh nghiệp cụ thể nào. Số liệu giao dịch vẫn là giả lập; chỉ tổng theo nghiệp vụ neo vào BCTC.


*Nguồn:* [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [P1 · trang 6](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf); [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [P8](https://www.pvi.com.vn/vi/network)

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


Trên DB: cá nhân chiếm 97,2% số hợp đồng nhưng 35,5% doanh thu (gồm toàn bộ GCN vi mô — người dùng app Green SM, sàn TMĐT, ATADI); doanh nghiệp trong nước 0,5% số hợp đồng nhưng 38,7% doanh thu. (Bộ v2 có mức chênh rõ hơn thực tế — xem mục Giới hạn.)


*Nguồn:* [S8](https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-67-2023-nd-cp-quy-dinh-ve-bao-hiem-bat-buoc-trach-nhiem-dan-su-cua-chu-xe-co-gioi-bao-hiem-chay-no-bat-buoc-bao-hiem-bat-buoc-trong-hoat-dong-dau-tu-xay-dung--163442); [P5](https://online.pvi.com.vn/san-pham); [D4](https://dutangc.github.io/CASdatasets/reference/freMTPL.html); [P3 · trang 14](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf)

**[Giả định] Vì sao sức khỏe nhóm chia DN trong nước 65 / FDI 25 / cơ quan nhà nước 10?**


Giả định theo thứ tự quy mô khối doanh nghiệp: DN trong nước nhiều nhất; sau đó là FDI (nhiều lao động, hay có phúc lợi bảo hiểm sức khỏe); cơ quan nhà nước ít nhất. Không có số công bố. Tỷ lệ này chỉ ảnh hưởng chiều Khách hàng, không ảnh hưởng tổng doanh thu.


*Nguồn:* không có số công bố — giả định của dự án

**[Giả định] Vì sao kênh trực tiếp và môi giới chiếm nhiều doanh thu nhất (trên DB: trực tiếp 30,4%, đại lý cá nhân 24,8%, môi giới 15,1%, bancassurance 12,5%, điện tử 8,0%)?**


Trực tiếp và môi giới cao vì PVI thiên về khách doanh nghiệp lớn (FPTS), mà hợp đồng doanh nghiệp thường khai thác trực tiếp hoặc qua môi giới. Môi giới toàn thị trường là 13,5% (Bộ Tài chính); với PVI dự án chọn cao hơn, khoảng 15–20%.


Điện tử: gần 800 tỷ năm 2024, khoảng 6% (BCTN PVI). Quý I/2025 kênh này tăng 1,8 lần (pvn.vn), nên khoảng 10% năm 2025.


Bancassurance: PVI mới mở rộng (hợp tác Nam A Bank); BCTN đặt định hướng phát triển môi giới và bancas. Dự án chọn 5–8%.


Phần giả định: trọng số từng kênh trong từng sản phẩm. Kênh không được hiệu chỉnh nên kết quả chỉ gần định hướng. Trên DB, kênh điện tử chiếm phần lớn giao dịch (toàn bộ GCN vi mô qua Green SM, ATADI, Fuse; TNDS xe máy, tai nạn 24/24, du lịch) nhưng chỉ khoảng 8% doanh thu vì phí mỗi đơn nhỏ — thấp hơn mức khoảng 10% của PVI.


*Nguồn:* [P3 · trang 15](https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [P1 · trang 29](https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf); [P2](https://pvn.vn/khoi-dau-vung-chac-bao-hiem-pvi-huong-toi-moc-doanh-thu-ty-do-la-my-nam-2025-28459); [P9](https://www.pvi.com.vn/vi/news/bao-hiem-pvi-va-nam-a-bank-khoi-dong-hop-tac-kinh-doanh-tai-khu-vuc-mien-tay); [M7](https://www.pvi.com.vn/vi/news/pvi-digital-doi-tac-bao-hiem-so-cua-cac-nen-tang-va-he-sinh-thai-so-hang-dau-viet-nam); [M10](https://pviholdings.com.vn/vi/news-details?id=6013)

**[Nghiệp vụ] Trên DB, vì sao doanh thu tháng 9 cao hơn tháng 8 khoảng 1,5 lần, còn số giao dịch chỉ tăng khoảng 10%?**


Theo Bộ Tài chính, phí gốc phi nhân thọ toàn thị trường năm 2025 tháng 8 là 5.592 tỷ, tháng 9 là 8.002 tỷ, tức mỗi ngày tháng 9 cao hơn khoảng 1,48 lần. Ngân sách tháng của dữ liệu lấy theo tỷ trọng này; giả định PVI có mùa vụ giống thị trường. Trên DB: T8 639,2 tỷ, T9 938,7 tỷ.


Số giao dịch thì phần lớn là GCN vi mô, sinh theo số GCN mỗi ngày (chuyến xe, đồ ăn) chứ không theo ngân sách tháng, nên gần như đều giữa hai tháng: T8 57.722–69.201 giao dịch/ngày (TB 63.923), T9 62.635–77.822 (TB 70.559). Học sinh còn tập trung quanh khai giảng 5/9; kênh văn phòng giảm cuối tuần và nghỉ lễ 01–02/9; thiết bị điện tử gấp 3 vào ngày hội 8/8, 9/9.


*Nguồn:* [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026); [S1](https://vbpl.vn/van-ban/chi-tiet/luat-kinh-doanh-bao-hiem-so-08-2022-qh15--163515)

**[Nghiệp vụ] Trong bộ v2, vì sao doanh thu quý 1 cao nhất?**


BCTC quý PVI Holdings: phí gốc 2025 theo quý là 29,7 / 24,1 / 24,8 / 21,4%. Lý do là các chương trình bảo hiểm doanh nghiệp (sức khỏe nhóm, tài sản, cháy nổ) thường tái tục đầu năm.


Học sinh đỉnh tháng 8–10 vì thu phí đầu năm học (CafeF). Hệ số theo tháng do dự án tự tinh chỉnh để khớp tỷ trọng theo quý.


*Nguồn:* [F2](https://pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/ce6f18e2-7a79-42f3-b6ab-2b79ea1e4077.pdf); [P6](https://cafef.vn/dau-nam-hoc-bo-100000-dong-mua-bao-hiem-than-the-cho-con-hang-trieu-phu-huynh-co-the-bo-qua-dieu-nay-188240923103450415.chn)

**[Giả định] Vì sao trên DB có khoảng 4,08 triệu hợp đồng trong 2 tháng, và Sinh mạng chiếm khoảng 81% số hợp đồng nhưng chỉ khoảng 4,7% doanh thu?**


Số hợp đồng truyền thống là hệ quả: ngân sách từng sản phẩm ÷ phí bình quân một hợp đồng (biểu phí, giá niêm yết) — 926.648 hợp đồng, 1.557,0 tỷ, phí bình quân khoảng 1,68 triệu đ.


Phần còn lại là GCN vi mô: 3.155.989 GCN (77,3% số hợp đồng) nhưng chỉ 20,8 tỷ (1,32% doanh thu). Hai sản phẩm vi mô lớn nhất thuộc nhóm Sinh mạng: Green SM Care 2.431.497 GCN, 3,36 tỷ, phí bình quân khoảng 1.383 đ; Food Care 516.750 GCN, 0,51 tỷ, khoảng 988 đ. Vì vậy Sinh mạng có 3.298.699 hợp đồng (80,8%) nhưng chỉ khoảng 74 tỷ (4,7% doanh thu) — vi mô chiếm khoảng 89% số hợp đồng của nhóm nhưng chỉ khoảng 5% doanh thu nhóm.


Hai sản phẩm vi mô còn lại: thiết bị điện tử trên sàn TMĐT 194.993 GCN, 16,35 tỷ (khoảng 83.837 đ/GCN, nhóm Tài sản); DelayCare 12.749 GCN, 0,62 tỷ (khoảng 48.739 đ/GCN, nhóm Du lịch).


Tỷ trọng doanh thu của sản phẩm truyền thống trong nhóm lấy đúng bảng của v2 (tai nạn 24/24 là 20% doanh thu Sinh mạng), nên tai nạn 24/24 không còn chiếm gần một nửa số hợp đồng như bản trước. Cả hai bộ đều không dùng để nói về số hợp đồng thật của PVI (PVI không công bố).


*Nguồn:* [M1](https://www.greensm.com/vn-vi/bao-hiem-khach-hang); [M3](https://www.greensm.com/vn-vi/bao-hiem-giao-do-an); [M8](https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam); [M9](https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154); [D4](https://dutangc.github.io/CASdatasets/reference/freMTPL.html)

**[Giả định] Vì sao doanh thu tập trung vào ít hợp đồng lớn (trên DB: 10% hợp đồng chiếm 97,7% doanh thu)?**


Doanh thu phi nhân thọ tập trung ở ít hợp đồng lớn, ví dụ gói hàng không Vietnam Airlines 540 tỷ, công trình Quảng Trạch I phí hơn 365 tỷ. Dự án mô phỏng bằng phân phối lệch phải của STBH; mức tập trung cụ thể là kết quả của giả định này.


Trên DB mức tập trung cao hơn bộ v2 (khoảng 75%) vì có hơn 3 triệu GCN vi mô phí 1.000–2.000 đ và hàng trăm nghìn hợp đồng bán lẻ phí nhỏ: 10% hợp đồng lớn nhất chiếm 97,7% doanh thu, 1% lớn nhất chiếm 80,1%.


*Nguồn:* [P7](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615); [P11](https://www.tinnhanhchungkhoan.vn/bao-hiem-ban-buon-truoc-co-hoi-lon-post368348.html)

**[Giả định] Vì sao đồng bảo hiểm chỉ xảy ra với rủi ro từ 300 tỷ trở lên?**


Các hợp đồng đồng bảo hiểm được công bố đều là rủi ro rất lớn: hàng không Vietnam Airlines, nhà ga Long Thành, đội tàu Vinalines (STBH hơn 565 triệu USD). Ngưỡng 300 tỷ và tỷ lệ 55% là giả định để đồng bảo hiểm chỉ rơi vào nhóm rủi ro lớn.


*Nguồn:* [P7](https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615); [P12](https://baodauthau.vn/lien-danh-6-thanh-vien-trung-goi-thau-bao-hiem-cang-hkqt-long-thanh-post136014.html); [P13](https://www.pvn.vn/bao-hiem-pvi-ky-thoa-thuan-khung-voi-vinalines-5860)

## Bảo hiểm vi mô và đơn vị PVI

**[Giả định] Bỏ hệ số k rồi, vì sao vẫn đạt trên 50.000 giao dịch mỗi ngày?**


Ở đúng quy mô PVI, sản phẩm truyền thống chỉ cho khoảng 12–18 nghìn hợp đồng mỗi ngày (trên DB: 926.648 hợp đồng truyền thống trong 61 ngày ≈ 15,2 nghìn/ngày). Bản trước nhân mọi ngân sách với k ≈ 3,93 nên doanh thu gấp khoảng 4 lần PVI.


Nay khối lượng đến từ bảo hiểm vi mô / nhúng theo giao dịch mà PVI thực sự bán: Green SM Care (40.000 GCN/ngày), Food Care (8.000), thiết bị điện tử trên sàn TMĐT (3.000, gấp 3 ngày 8/8, 9/9), DelayCare (300 từ 20/8) — khoảng 51.000 GCN mỗi ngày. Phí chỉ 1.000–2.000 đ cho chuyến xe, đồ ăn nên gần như không làm đổi doanh thu.


Kết quả trên DB: T8 57.722–69.201 giao dịch/ngày, T9 62.635–77.822 — ngày thấp nhất vẫn trên 50.000; doanh thu đúng quy mô PVI (phí gốc khai thác 1.600,6 tỷ so với ngân sách 1.602 tỷ).


Lý do phạm vi POC: yêu cầu > 50.000 giao dịch/ngày là để thử tải dashboard; dùng vi mô thì vừa đủ tải vừa giữ doanh thu và cơ cấu đúng PVI. Số GCN mỗi ngày là [ƯỚC TÍNH] (xem câu về 40.000 GCN).


*Nguồn:* [M1](https://www.greensm.com/vn-vi/bao-hiem-khach-hang); [M3](https://www.greensm.com/vn-vi/bao-hiem-giao-do-an); [M4](https://www.pvi.com.vn/vi/news/bao-hiem-pvi-ra-mat-delaycare-giai-phap-bao-hiem-tre-chuyen-bay-danh-cho-hanh-khach); [M5](https://help.shopee.vn/portal/4/article/79225); [M6](https://magiamgia.com/bao-hiem-thiet-bi-dien-tu-lazada/); [M8](https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam); [M9](https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154); [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026)

**[Giả định] Thêm bảo hiểm vi mô thì phân phối và quy mô doanh thu thay đổi thế nào?**


Quy mô: không đổi. Doanh thu vi mô nằm trong ngân sách của nhóm (Sinh mạng, Du lịch, Tài sản); bước hiệu chỉnh coi nó là dòng cố định và chỉ co giãn phần đơn doanh nghiệp / nhóm. Tổng phí gốc khai thác 1.600,6 tỷ ≈ ngân sách PVI tháng 8–9 (10.377,9 × 13.594 / 88.054 ≈ 1.602 tỷ); doanh thu ghi nhận 1.577,9 tỷ. Cơ cấu tài sản / con người / xe 52,0 / 30,4 / 17,6% — khớp BCTC 51,5 / 31,0 / 17,6%.


Số hợp đồng: thay đổi mạnh. Tổng 4.082.637 hợp đồng; vi mô 3.155.989 (77,3%) nhưng chỉ 20,8 tỷ = 1,32% doanh thu. Truyền thống 926.648 hợp đồng, 1.557,0 tỷ, phí bình quân khoảng 1,68 triệu đ.


Từng sản phẩm vi mô: Green SM Care 2.431.497 GCN / 3,36 tỷ (khoảng 1.383 đ/GCN); Food Care 516.750 / 0,51 tỷ (988 đ); thiết bị điện tử 194.993 / 16,35 tỷ (83.837 đ); DelayCare 12.749 / 0,62 tỷ (48.739 đ).


Phân phối: lệch hơn. 10% hợp đồng lớn nhất chiếm 97,7% doanh thu, 1% lớn nhất chiếm 80,1% (bản trước: 93% / 74%). Sinh mạng có 3.298.699 hợp đồng nhưng chỉ khoảng 74 tỷ. Kênh điện tử và phân khúc cá nhân chiếm gần hết số hợp đồng nhưng ít doanh thu (cá nhân 97,2% hợp đồng, 35,5% doanh thu).


Đây là đặc trưng thật của bảo hiểm nhúng: OPES phát hành 109,3 triệu hợp đồng năm 2023, cao điểm > 500.000 đơn/ngày. Khi làm dashboard cần tách chỉ số 'số giao dịch' và 'doanh thu', và có bộ lọc truyền thống / vi mô.


*Nguồn:* [M9](https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154); [M1](https://www.greensm.com/vn-vi/bao-hiem-khach-hang); [M3](https://www.greensm.com/vn-vi/bao-hiem-giao-do-an); [F1 · trang 45](https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf); [F4](https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026)

**[Nghiệp vụ] Vì sao bảo hiểm theo chuyến xe dùng Green SM chứ không phải Grab?**


Green SM Care (bảo hiểm tai nạn hành khách theo chuyến, 1.000 đ Bike / 2.000 đ Taxi) có PVI Digital là 1 trong 5 nhà bảo hiểm (PVI Digital, OPES, BIC, TCGI, MIC) — greensm.com và tinnhanhchungkhoan.vn. Food Care trên Green SM cũng là sản phẩm của Bảo hiểm PVI.


Grab có trong danh sách đối tác số của PVI Digital, nhưng bảo hiểm chuyến đi của Grab (Ride Cover, 2.000 đ) do Chubb cung cấp, còn của Be do OPES. Hợp tác Grab × PVI năm 2026 là chương trình BHXH / BHYT tự nguyện cho tài xế — không phải bảo hiểm theo cuốc. Dùng Grab sẽ là gán sai sản phẩm cho PVI.


*Nguồn:* [M1](https://www.greensm.com/vn-vi/bao-hiem-khach-hang); [M2](https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html); [M3](https://www.greensm.com/vn-vi/bao-hiem-giao-do-an); [M7](https://www.pvi.com.vn/vi/news/pvi-digital-doi-tac-bao-hiem-so-cua-cac-nen-tang-va-he-sinh-thai-so-hang-dau-viet-nam); [M11](https://www.grab.com/vn/blog/driver/bhxh-bhyt-pvi/)

**[Giả định] Vì sao 40.000 GCN chuyến xe mỗi ngày?**


Căn cứ: Green SM vượt 1 triệu chuyến/ngày năm 2025 (fhsc.com.vn, nguồn thứ cấp); Green SM Care có 5 nhà bảo hiểm, PVI Digital là một (greensm.com). [ƯỚC TÍNH] 20% chuyến có mua bảo hiểm × 20% phần về PVI (1/5 nhà bảo hiểm) → 1.000.000 × 20% × 20% = 40.000 GCN/ngày.


Kiểm tra độ hợp lý: OPES — một nhà bảo hiểm số — phát hành 109,3 triệu hợp đồng năm 2023, cao điểm hơn 500.000 đơn/ngày; 40.000/ngày của PVI trên Green SM nằm trong khoảng đó.


KHÔNG TÌM THẤY: số GCN vi mô PVI phát hành theo ngày / năm, tỷ lệ khách chọn mua Green SM Care.


Lý do phạm vi POC: cần đủ giao dịch (> 50.000/ngày) mà không làm sai doanh thu. 40.000 GCN × khoảng 1.400 đ chỉ khoảng 56 triệu đ/ngày. Đổi con số này chỉ đổi số giao dịch, không đổi tổng doanh thu nhóm.


*Nguồn:* [M8](https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam); [M1](https://www.greensm.com/vn-vi/bao-hiem-khach-hang); [M2](https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html); [M9](https://opes.com.vn/posts/business/opes-va-hanh-trinh-chuyen-minh-nho-so-hoa-1716806154)

**[Giả định] Trọng số doanh thu của từng đơn vị PVI dựa vào đâu, và đơn vị / công ty con so với PVI thế nào?**


47 đơn vị và địa chỉ trụ sở là thật (pvi.com.vn/vi/network). Doanh thu từng đơn vị thì PVI KHÔNG công bố (đã nghiên cứu chéo bằng codex CLI và agy CLI, kiểm link bằng curl 19/10/2026). Vì vậy trọng số khai thác là [ƯỚC TÍNH] theo quy mô kinh tế địa bàn của trụ sở, nhân 1,5 cho 5 đơn vị được PVI vinh danh / tự công bố dẫn đầu: Phía Nam (xuất sắc nhất 2024), Thủ Đô (6 tháng 2025), Duyên Hải (2025), Thăng Long (hoàn thành sớm kế hoạch 2025), Sài Gòn (tự công bố doanh thu đứng đầu bán lẻ, pvisg.net).


Trên DB (T8–T9/2026): Duyên Hải 127,3 tỷ, Trụ sở chính 101,8 tỷ, Thống Nhất 74,9 tỷ, Hà Nội 56,3 tỷ, PVI Digital 55,7 tỷ (gồm GCN vi mô). Một đơn vị có thể vượt trọng số khi vài hợp đồng doanh nghiệp rất lớn rơi vào (phân phối lệch phải). Đây là số giả lập, không phải doanh thu thật của đơn vị.


So với PVI Holdings (BCTN 2025, trang PDF 29, 32, 33, 34): doanh thu hợp nhất 28.923 tỷ; Bảo hiểm PVI 27.258 tỷ (94,2%), trong đó phí bảo hiểm gốc 14.908 tỷ; Tái bảo hiểm Hà Nội (Hanoi Re, tên cũ PVI Re, sở hữu 81,09%) 3.690 tỷ; Quản lý Quỹ PVI (PVIAM, 61,96%) 76,4 tỷ. Năm 2024: 21.824 / 20.405 / 3.017,3 / 57,4 tỷ (BCTN 2024).


Phạm vi POC là doanh thu phí bảo hiểm gốc, nên chỉ có Tổng Công ty Bảo hiểm PVI (công ty con 100% của PVI Holdings, BCTN 2024 trang PDF 12) và 47 đơn vị của nó. Hanoi Re (nhận tái) và PVIAM (quản lý quỹ) không cấp hợp đồng gốc nên không có trong danh mục đơn vị. Mục tiêu 4 nghiệp vụ của POC (10.377,9 tỷ/năm) là một phần của 14.908 tỷ phí gốc.


*Nguồn:* [P8](https://www.pvi.com.vn/vi/network); [U4](https://online.pvi.com.vn/lien-he); [U5](https://pvisg.net); [U6](https://www.pvi.com.vn/vi/news/bao-hiem-pvi-mot-nam-vuot-song-chinh-phuc-nhung-cot-moc-moi-681b4f9737783); [U7](https://www.pvi.com.vn/en/news/bao-hiem-pvi-doi-moi-sang-tao-va-thanh-cong); [U8](https://vnexpress.net/nhung-yeu-to-giup-doanh-thu-bao-hiem-pvi-vuot-1-ty-usd-5011267.html); [U9](https://www.pvi.com.vn/vi/news/pvi-thu-do-va-pvi-thang-long-hai-don-vi-tiep-theo-duoc-vinh-danh-hoan-thanh-som-ke-hoach-kinh-doanh-nam-2025); [U2 · trang 29, 32, 33, 34](https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf); [U1 · trang 12](https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf); [U3](https://www.hanoire.com/vi/pvi-re-chinh-thuc-doi-ten-thanh-hanoi-re)

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
| U1 | [BCTN PVI 2024 (bản tiếng Việt, PVI Holdings)](https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf) | trang 12 (Bảo hiểm PVI là công ty con 100% của CTCP PVI; Hanoi Re 81,09%, PVIAM 61,96%); trang 22, 29, 30, 31 (doanh thu 2024: hợp nhất 21.824 tỷ, Bảo hiểm PVI 20.405 tỷ, Hanoi Re 3.017,3 tỷ, PVIAM 57,4 tỷ); trang 29 (TMĐT gần 800 tỷ, 30 kết nối API) |
| U2 | [BCTN PVI 2025 (PVI Holdings)](https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf) | trang 29, 32, 33, 34 (doanh thu 2025: hợp nhất 28.923 tỷ; Bảo hiểm PVI 27.258 tỷ, trong đó phí bảo hiểm gốc 14.908 tỷ; Hanoi Re 3.690 tỷ; PVIAM 76,4 tỷ) |
