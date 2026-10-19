# Nguồn pháp lý: văn bản và điều khoản dùng trong mô hình

Tất cả điều khoản dưới đây được đọc từ toàn văn trên vbpl.vn, cập nhật đến 10/2026. Mọi URL đều có tiền tố `https://vbpl.vn/van-ban/chi-tiet/`.

| Mã | Văn bản | URL (phần sau tiền tố) |
|---|---|---|
| S1 | Luật Kinh doanh bảo hiểm 08/2022/QH15 | `luat-kinh-doanh-bao-hiem-so-08-2022-qh15--163515` |
| S2 | Luật sửa đổi 139/2025/QH15 (hiệu lực 01/01/2026) | `luat-sua-doi-bo-sung-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-so-139-2025-qh15--187047` |
| S3 | NĐ 46/2023/NĐ-CP | `nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441` |
| S5 | TT 67/2023/TT-BTC (có Phụ lục VI các mẫu báo cáo) | `thong-tu-so-67-2023-tt-btc-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-nghi-dinh-so-46-2023-nd-cp-ngay-01-thang-7-nam-2023-cua-chinh-phu-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163439` |
| S6 | VBHN 44/2026/VBHN-TT-BTC (hợp nhất TT 67 và TT 96/2026) | `van-ban-hop-nhat-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-va-nghi-dinh-so-46-2023-nd-cp-so-44-2026-vbhn-tt-btc--035153a0-be3d-11f1-adb4-c9ac1aadd258` |
| S8 | NĐ 67/2023/NĐ-CP | `nghi-dinh-so-67-2023-nd-cp-quy-dinh-ve-bao-hiem-bat-buoc-trach-nhiem-dan-su-cua-chu-xe-co-gioi-bao-hiem-chay-no-bat-buoc-bao-hiem-bat-buoc-trong-hoat-dong-dau-tu-xay-dung--163442` |
| S9 | NĐ 105/2025/NĐ-CP (PCCC; thay Phụ lục II của NĐ 67) | `nghi-dinh-so-105-2025-nd-cp-quy-dinh-chi-tiet-mot-so-dieu-va-bien-phap-thi-hanh-luat-phong-chay-chua-chay-va-cuu-nan-cuu-ho--177733` |
| S11 | TT 232/2012/TT-BTC (kế toán DNBH phi nhân thọ) | `thong-tu-so-232-2012-tt-btc-huong-dan-ke-toan-ap-dung-doi-voi-doanh-nghiep-bao-hiem-phi-nhan-tho-doanh-nghiep-tai-bao-hiem-va-chi-nhanh-doanh-nghiep-bao-hiem-phi-nhan-tho-nuoc-ngoai--30429` |
| S12 | NQ 202/2025/QH15 (sắp xếp ĐVHC cấp tỉnh) | `nghi-quyet-so-202-2025-qh15-ve-viec-sap-xep-don-vi-hanh-chinh-cap-tinh--179501` |
| S14 | VBHN 12/VBHN-VPQH 2026 (hợp nhất Luật Thuế GTGT 48/2024/QH15) | `van-ban-hop-nhat-so-12-vbhn-vpqh-2026-hop-nhat-luat-thue-gia-tri-gia-tang-so-48-2024-qh15--8ca5f9c0-9625-11f1-9b37-1f0c0efba979` |

## Điều khoản và nơi sử dụng trong mô hình

| Điều khoản | Nội dung | Dùng ở |
|---|---|---|
| S1 Điều 4 khoản 14, 15 | Định nghĩa bảo hiểm phi nhân thọ và bảo hiểm sức khỏe | `line_of_business.legal_category` |
| S1 Điều 4 khoản 29 | Đồng bảo hiểm: nhiều DNBH trên một hợp đồng, nhận phí theo tỷ lệ | `core.coinsurance_share` |
| S1 Điều 7 khoản 1 | 3 loại hình: nhân thọ, sức khỏe, phi nhân thọ | `ref.line_of_business` |
| S1 Điều 87 khoản 4 | Hình thức cung cấp sản phẩm: a) trực tiếp; b) qua đại lý/môi giới; c) đấu thầu; d) giao dịch điện tử; đ) khác | `ref.channel` |
| S1 Điều 124, 125 khoản 2 | Đại lý bảo hiểm; tổ chức tín dụng làm đại lý | `ref.channel` (BANCA) |
| S3 Điều 4, 5 | 11 nghiệp vụ phi nhân thọ; nghiệp vụ sức khỏe (sức khỏe, thân thể / chi phí y tế) | `ref.line_of_business`, `ref.regulatory_line` |
| S3 Điều 49 (sửa bởi NĐ 97/2026) | Doanh thu = khoản phải thu (phí gốc…) trừ khoản giảm thu (hoàn phí, giảm phí…) | `ref.transaction_type` |
| S3 Điều 62; S6 Điều 53 | Điều kiện bancassurance; đối chiếu hằng tháng với DNBH | `ref.channel` (BANCA) |
| S6 Điều 4–5 | Bán bảo hiểm trên môi trường mạng: sản phẩm được phép, kênh website/app/sàn TMĐT | `ref.channel` (DIEN_TU); kênh này chỉ dùng cho sức khỏe, xe, du lịch, nhà tư nhân |
| S6 Điều 41 khoản 1, 2 | Ghi nhận phí gốc khi phát sinh trách nhiệm; phân bổ theo tỷ lệ đồng bảo hiểm | `accounting_date`; công thức doanh thu |
| S6 Điều 51 khoản 3 | Trần hoa hồng: tài sản 5%; xe trừ TNDS 10%; cháy nổ 10% (bắt buộc 5%); sức khỏe 20%; TNDS bắt buộc ô tô 5%, xe máy 20% | `ref.product.max_commission_pct` |
| S5 Phụ lục VI, Mẫu 1/2/3-PNT | Dòng báo cáo theo nghiệp vụ; 3 nhóm kênh (qua TCTD / qua môi trường mạng / khác) | `ref.regulatory_line`, `ref.channel.report_channel_group` |
| S8 Phụ lục I | Biểu phí TNDS bắt buộc theo loại xe | Đơn giá `XE_TNDS_*` |
| S8 Phụ lục II; S9 Điều 44 | Tỷ lệ phí cháy nổ bắt buộc. Bản 2023 bị thay từ 01/7/2025 bằng Phụ lục VI NĐ 105/2025 (chỉ có bản scan); **dự án dùng bản 2023 làm chuẩn** | Tỷ lệ phí `CHN_BB` |
| S11 Điều 2, 12, 19 | TK 5111 / 531 / 532 / 533 / 005; TK 511 chi tiết theo nghiệp vụ; hạch toán đồng bảo hiểm chỉ phần của mình | `ref.transaction_type.gl_account`; công thức doanh thu |
| S12 | 34 tỉnh/thành từ 01/7/2025 | `ref.province` |
| S14 Điều 5 khoản 8 | Không chịu thuế GTGT: bảo hiểm sức khỏe, người học, các dịch vụ bảo hiểm liên quan đến con người | `ref.product.vat_rate` |
