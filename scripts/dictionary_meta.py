"""Mô tả nghiệp vụ cho từng bảng / cột của mô hình v2 — nguồn duy nhất cho Data Dictionary (Excel, HTML, COMMENT ON)."""

LAW = "Luật KDBH 2022"
TT67 = "TT 67/2023/TT-BTC"
TT232 = "TT 232/2012/TT-BTC"
ND46 = "NĐ 46/2023/NĐ-CP"
ND67 = "NĐ 67/2023/NĐ-CP"

# (schema.table) -> (lớp, mô tả, grain, căn cứ)
TABLES = {
    "ref.region": ("Danh mục", "Vùng miền dùng để nhóm tỉnh/thành", "1 dòng / vùng", "Đề xuất của dự án (không có văn bản pháp lý chia 3 miền)"),
    "ref.province": ("Danh mục", "Tỉnh/thành phố theo đơn vị hành chính hiện hành (34 đơn vị)", "1 dòng / tỉnh-thành", "NQ 202/2025/QH15"),
    "ref.company": ("Danh mục", "Cơ cấu tổ chức: Tổng công ty → khối trụ sở, công ty thành viên, đơn vị kinh doanh số", "1 dòng / đơn vị", "Mô hình Tổng công ty – công ty thành viên công khai của các DNBH (BCTN Bảo Việt, PVI)"),
    "ref.line_of_business": ("Danh mục", "Nghiệp vụ bảo hiểm + nhóm phân tích POC (Xe / Con người / Tài sản)", "1 dòng / nghiệp vụ", f"{LAW} Điều 7; {ND46} Điều 4–5"),
    "ref.regulatory_line": ("Danh mục", "Dòng báo cáo nghiệp vụ theo mẫu báo cáo Bộ Tài chính (cây cha–con)", "1 dòng / dòng báo cáo", f"{TT67} Phụ lục VI – Mẫu 1-PNT/2-PNT"),
    "ref.product_group": ("Danh mục", "Nhóm sản phẩm — cấp giữa Nghiệp vụ và Sản phẩm, đúng 8 nhóm của đề bài", "1 dòng / nhóm SP", "Phạm vi đề bài POC"),
    "ref.product": ("Danh mục", "Sản phẩm bảo hiểm (phạm vi POC)", "1 dòng / sản phẩm", f"{ND67}; Luật GTGT 48/2024; {TT67} Điều 51"),
    "ref.channel": ("Danh mục", "Kênh phân phối theo hình thức cung cấp sản phẩm bảo hiểm", "1 dòng / kênh", f"{LAW} Điều 87 khoản 4; {TT67} Mẫu 3-PNT"),
    "ref.partner": ("Danh mục", "Đối tác phân phối — ngân hàng, đăng kiểm, OTA, ví điện tử... (ẩn danh); 3 đối tác số tên thật có công bố hợp tác với PVI: Green SM, ATADI, Fuse", "1 dòng / đối tác", "Loại đối tác theo thực tế thị trường; đối tác truyền thống ẩn danh, đối tác bảo hiểm vi mô theo nguồn công khai (sources/market_data.md mục 10)"),
    "ref.customer_segment": ("Danh mục", "Phân khúc khách hàng", "1 dòng / phân khúc", "Phân loại phổ biến (cá nhân / hộ gia đình / doanh nghiệp / cơ quan NN / cơ sở giáo dục)"),
    "ref.customer": ("Danh mục", "Khách hàng — bên mua bảo hiểm (dữ liệu giả)", "1 dòng / khách hàng", "Dữ liệu sinh ngẫu nhiên"),
    "ref.currency": ("Danh mục", "Tiền tệ", "1 dòng / loại tiền", "ISO 4217"),
    "ref.fx_rate": ("Danh mục", "Tỷ giá hạch toán theo tháng", "1 dòng / loại tiền × tháng", "Tỷ giá hạch toán KBNN 2025; 2024 ước tính"),
    "ref.transaction_type": ("Danh mục", "Loại giao dịch phí: cấp mới, tái tục, SĐBS, hoàn phí, hủy", "1 dòng / loại giao dịch", f"{ND46} Điều 49; {TT232}; ACORD BusinessPurposeTypeCd"),
    "ref.insurer": ("Danh mục", "Doanh nghiệp bảo hiểm tham gia đồng bảo hiểm (ẩn danh); OWN = chính công ty", "1 dòng / DNBH", f"{LAW} Điều 4 khoản 29"),
    "ref.allocation_type": ("Danh mục", "Loại phân bổ doanh thu giữa các đơn vị", "1 dòng / loại", "Thông lệ quản trị nội bộ"),
    "core.policy": ("Giao dịch", "Hợp đồng / đơn bảo hiểm", "1 dòng / hợp đồng", f"{LAW}; ACORD Policy; IBM IIW Agreement"),
    "core.policy_transaction": ("Giao dịch", "Giao dịch phát sinh phí của hợp đồng (cấp mới, tái tục, SĐBS, hoàn phí, hủy)", "1 dòng / giao dịch", f"{ND46} Điều 49; {TT232} TK 5111/5311/5321; Microsoft CDM PolicyTransaction"),
    "core.transaction_coverage": ("Giao dịch", "Phí 100% hợp đồng theo từng sản phẩm của giao dịch", "1 dòng / giao dịch × sản phẩm", f"{TT232} Điều 12 (DT chi tiết theo nghiệp vụ); ACORD Coverage NetChangeAmt"),
    "core.coinsurance_share": ("Giao dịch", "Tỷ lệ tham gia đồng bảo hiểm của từng DNBH trên hợp đồng (tổng = 100%)", "1 dòng / hợp đồng × DNBH", f"{LAW} Điều 4 k29; {TT232} Điều 19; {TT67} Điều 41 k2"),
    "core.revenue_allocation": ("Giao dịch", "Phân bổ doanh thu phần của công ty cho các đơn vị (tổng = 100%)", "1 dòng / hợp đồng × đơn vị", "Thông lệ quản trị Tổng công ty – công ty thành viên"),
}

# (schema.table, column) -> (mô tả, căn cứ / nguồn giá trị)
COLUMNS = {
    # ---------------- ref.region / province
    ("ref.region", "region_code"): ("Mã vùng: BAC / TRUNG / NAM", ""),
    ("ref.region", "region_name"): ("Tên vùng", ""),
    ("ref.province", "province_code"): ("Mã tỉnh/thành (mã do dự án đặt, 3 ký tự)", ""),
    ("ref.province", "province_name"): ("Tên tỉnh/thành phố", "NQ 202/2025/QH15"),
    ("ref.province", "region_code"): ("Vùng của tỉnh → ref.region", "Đề xuất của dự án"),
    # ---------------- ref.company
    ("ref.company", "company_code"): ("Mã đơn vị", ""),
    ("ref.company", "company_name"): ("Tên đơn vị (giả lập, đặt theo địa bàn)", ""),
    ("ref.company", "company_type"): ("Loại đơn vị: CORPORATION (Tổng công ty) / HEAD_OFFICE (khối trụ sở khai thác trực tiếp) / MEMBER (công ty thành viên) / DIGITAL (đơn vị kinh doanh số)", ""),
    ("ref.company", "parent_company_code"): ("Đơn vị cấp trên → ref.company (NULL = Tổng công ty)", ""),
    ("ref.company", "province_code"): ("Tỉnh/thành đặt trụ sở → ref.province (NULL = đơn vị không gắn địa bàn)", ""),
    ("ref.company", "established_date"): ("Ngày thành lập (giả lập)", ""),
    # ---------------- ref.line_of_business / regulatory_line / product_group
    ("ref.line_of_business", "lob_code"): ("Mã nghiệp vụ: SUC_KHOE / XE_CO_GIOI / CHAY_NO / TAI_SAN", ""),
    ("ref.line_of_business", "lob_name"): ("Tên nghiệp vụ", f"{ND46} Điều 4–5"),
    ("ref.line_of_business", "legal_category"): ("Loại hình bảo hiểm: Bảo hiểm sức khỏe / Bảo hiểm phi nhân thọ", f"{LAW} Điều 7 khoản 1"),
    ("ref.line_of_business", "poc_group_code"): ("Nhóm phân tích POC: XE / CON_NGUOI / TAI_SAN", "Đề bài POC"),
    ("ref.line_of_business", "poc_group_name"): ("Tên nhóm phân tích POC", "Đề bài POC"),
    ("ref.line_of_business", "legal_basis"): ("Căn cứ pháp lý của nghiệp vụ", ""),
    ("ref.regulatory_line", "report_line_code"): ("Mã dòng báo cáo (A.1, A.2, B.4a.1 …) — mã do dự án đặt theo thứ tự dòng trong mẫu", f"{TT67} Phụ lục VI"),
    ("ref.regulatory_line", "report_line_name"): ("Tên dòng báo cáo nghiệp vụ", f"{TT67} Phụ lục VI"),
    ("ref.regulatory_line", "parent_line_code"): ("Dòng cha → ref.regulatory_line", ""),
    ("ref.regulatory_line", "legal_basis"): ("Căn cứ", ""),
    ("ref.product_group", "product_group_code"): ("Mã nhóm SP: TNDS_BB, VCX, HOC_SINH, DU_LICH, SINH_MANG, SUC_KHOE, TAI_SAN, CHAY_NO", "Đề bài POC"),
    ("ref.product_group", "product_group_name"): ("Tên nhóm sản phẩm", ""),
    ("ref.product_group", "lob_code"): ("Nghiệp vụ → ref.line_of_business", ""),
    ("ref.product_group", "sort_order"): ("Thứ tự hiển thị", ""),
    # ---------------- ref.product
    ("ref.product", "product_code"): ("Mã sản phẩm (tiền tố XE_ / NG_ / TS_ / CHN_)", ""),
    ("ref.product", "product_name"): ("Tên sản phẩm theo cách gọi phổ biến của thị trường", "Website các DNBH"),
    ("ref.product", "product_group_code"): ("Nhóm sản phẩm → ref.product_group", ""),
    ("ref.product", "report_line_code"): ("Dòng báo cáo Mẫu 2-PNT → ref.regulatory_line", f"{TT67} Phụ lục VI"),
    ("ref.product", "is_compulsory"): ("TRUE = bảo hiểm bắt buộc", ND67),
    ("ref.product", "pricing_basis"): ("Cách tính phí: TARIFF (biểu phí cố định) / RATE_ON_SI (% số tiền BH) / PER_PERSON (theo đầu người)", ""),
    ("ref.product", "vat_rate"): ("Thuế suất GTGT %: 0 = không chịu thuế (BH con người), 10 = còn lại", "Luật GTGT 48/2024/QH15 Điều 5 khoản 8, Điều 9"),
    ("ref.product", "max_commission_pct"): ("Trần tỷ lệ hoa hồng đại lý %", f"{TT67} Điều 51 khoản 3"),
    ("ref.product", "legal_basis"): ("Căn cứ pháp lý riêng của sản phẩm (nếu có)", ""),
    ("ref.product", "solvency2_lob"): ("Đối chiếu quốc tế: Solvency II LoB; (*) = suy luận theo bản chất rủi ro", "Delegated Reg. (EU) 2015/35 Annex I"),
    # ---------------- ref.channel / partner
    ("ref.channel", "channel_code"): ("Mã kênh: TRUC_TIEP, DAI_LY_CN, DAI_LY_TC, BANCA, MOI_GIOI, DAU_THAU, DIEN_TU", ""),
    ("ref.channel", "channel_name"): ("Tên kênh", f"{LAW} Điều 87 khoản 4"),
    ("ref.channel", "report_channel_group"): ("Nhóm kênh báo cáo: Qua tổ chức tín dụng / Qua môi trường mạng / Qua kênh phân phối khác", f"{TT67} Mẫu 3-PNT"),
    ("ref.channel", "legal_basis"): ("Căn cứ pháp lý của kênh", ""),
    ("ref.channel", "sort_order"): ("Thứ tự hiển thị", ""),
    ("ref.partner", "partner_code"): ("Mã đối tác", ""),
    ("ref.partner", "partner_name"): ("Tên đối tác (ẩn danh: Ngân hàng TMCP A, Ví điện tử B …; tên thật cho Green SM, ATADI, Fuse)", ""),
    ("ref.partner", "partner_type"): ("Loại đối tác: NGAN_HANG, CTY_TAI_CHINH, DANG_KIEM, SHOWROOM_OTO, GARAGE, OTA_DU_LICH, CTY_LU_HANH, CTY_MOI_GIOI, VI_DIEN_TU, SAN_TMDT, HANG_HANG_KHONG, VIEN_THONG", ""),
    ("ref.partner", "channel_code"): ("Kênh của đối tác → ref.channel", ""),
    # ---------------- customer
    ("ref.customer_segment", "segment_code"): ("Mã phân khúc", ""),
    ("ref.customer_segment", "segment_name"): ("Tên phân khúc", ""),
    ("ref.customer_segment", "is_organization"): ("TRUE = tổ chức, FALSE = cá nhân / hộ gia đình", ""),
    ("ref.customer", "customer_code"): ("Mã khách hàng (KHnnnnnnn)", ""),
    ("ref.customer", "customer_name"): ("Tên khách hàng (giả)", "Dữ liệu sinh ngẫu nhiên"),
    ("ref.customer", "segment_code"): ("Phân khúc → ref.customer_segment", ""),
    ("ref.customer", "tax_code"): ("Mã số thuế (chỉ tổ chức; giả)", ""),
    ("ref.customer", "province_code"): ("Tỉnh/thành → ref.province", ""),
    ("ref.customer", "home_company_code"): ("Đơn vị quản lý khách hàng → ref.company", ""),
    ("ref.customer", "is_aggregated_retail"): ("TRUE = 'Khách lẻ theo bảng kê' — bên mua gộp của đơn lô giấy chứng nhận bán qua đối tác", ""),
    ("ref.customer", "created_date"): ("Ngày tạo khách hàng", ""),
    # ---------------- currency / fx
    ("ref.currency", "currency_code"): ("Mã tiền tệ ISO 4217", ""),
    ("ref.currency", "currency_name"): ("Tên tiền tệ", ""),
    ("ref.fx_rate", "currency_code"): ("Tiền tệ → ref.currency", ""),
    ("ref.fx_rate", "rate_month"): ("Tháng áp dụng (ngày đầu tháng)", ""),
    ("ref.fx_rate", "rate_to_vnd"): ("Tỷ giá quy đổi ra VND", "Tỷ giá hạch toán KBNN"),
    ("ref.fx_rate", "source_note"): ("Ghi chú nguồn tỷ giá", ""),
    # ---------------- txn type / insurer / allocation type
    ("ref.transaction_type", "txn_type_code"): ("Mã loại giao dịch: NEW, RENEW, END_INC, END_DEC, REFUND, CANCEL, END_NOCHG", ""),
    ("ref.transaction_type", "txn_type_name"): ("Tên loại giao dịch", ""),
    ("ref.transaction_type", "premium_sign"): ("Dấu của phí: +1 / -1 / 0", ""),
    ("ref.transaction_type", "is_revenue_deduction"): ("TRUE = khoản giảm thu (hoàn phí, giảm phí)", f"{ND46} Điều 49 khoản 3"),
    ("ref.transaction_type", "gl_account"): ("Tài khoản kế toán: 5111 phí gốc / 5311 hoàn phí gốc / 5321 giảm phí gốc", f"{TT232} Điều 2"),
    ("ref.transaction_type", "acord_business_purpose_cd"): ("Đối chiếu quốc tế ACORD: NBS / RWL / PCH / XLC", "ACORD P&C BusinessPurposeTypeCd"),
    ("ref.transaction_type", "note"): ("Ghi chú", ""),
    ("ref.insurer", "insurer_code"): ("Mã DNBH; 'OWN' = chính công ty", ""),
    ("ref.insurer", "insurer_name"): ("Tên DNBH (ẩn danh)", ""),
    ("ref.insurer", "is_own_company"): ("TRUE = chính công ty", ""),
    ("ref.allocation_type", "allocation_type_code"): ("TU_KHAI_THAC / HO_TRO_CHEO / CHUYEN_GIAO", ""),
    ("ref.allocation_type", "allocation_type_name"): ("Tên loại phân bổ", ""),
    ("ref.allocation_type", "note"): ("Diễn giải", ""),
    # ---------------- core.policy
    ("core.policy", "policy_id"): ("Khóa hợp đồng", ""),
    ("core.policy", "policy_no"): ("Số hợp đồng: <năm>-<đơn vị>-<nhóm SP>-<số thứ tự>", ""),
    ("core.policy", "issuing_company_code"): ("Đơn vị cấp đơn → ref.company", ""),
    ("core.policy", "customer_code"): ("Bên mua bảo hiểm → ref.customer", ""),
    ("core.policy", "channel_code"): ("Kênh bán → ref.channel. Bắt buộc theo nghiệp vụ; NULL = nguồn không khai báo (~0,5%, dữ liệu bẩn có chủ đích) — lớp phân tích gán 'CHUA_XD'", f"{TT67} Mẫu 3-PNT (báo cáo theo kênh)"),
    ("core.policy", "partner_code"): ("Đối tác phân phối → ref.partner. Không bắt buộc: NULL = không qua đối tác (bán trực tiếp, đại lý cá nhân, đấu thầu, website/app công ty) — hợp lệ; lớp phân tích gán 'WEB_APP' (kênh điện tử) / 'KHONG_QUA_DT' (kênh khác)", "Quy ước dự án 13/10/2026"),
    ("core.policy", "currency_code"): ("Loại tiền của hợp đồng → ref.currency", ""),
    ("core.policy", "issue_date"): ("Ngày cấp đơn / giao kết hợp đồng", ""),
    ("core.policy", "effective_date"): ("Ngày bắt đầu thời hạn bảo hiểm", ""),
    ("core.policy", "expiry_date"): ("Ngày kết thúc thời hạn bảo hiểm", ""),
    ("core.policy", "is_group_policy"): ("TRUE = đơn nhóm / đơn lô giấy chứng nhận", ""),
    ("core.policy", "renewal_of_policy_id"): ("Hợp đồng được tái tục → core.policy (NULL = đơn mới)", ""),
    # ---------------- core.policy_transaction
    ("core.policy_transaction", "txn_id"): ("Khóa giao dịch", ""),
    ("core.policy_transaction", "policy_id"): ("Hợp đồng → core.policy", ""),
    ("core.policy_transaction", "txn_no"): ("Số chứng từ: <số hợp đồng>/<thứ tự giao dịch>", ""),
    ("core.policy_transaction", "txn_type_code"): ("Loại giao dịch → ref.transaction_type", ""),
    ("core.policy_transaction", "txn_date"): ("Ngày chứng từ (ngày phát sinh giao dịch)", ""),
    ("core.policy_transaction", "accounting_date"): ("Ngày ghi nhận doanh thu = ngày phát sinh trách nhiệm bảo hiểm (cấp mới/tái tục: max(ngày cấp, ngày hiệu lực); SĐBS: ngày chứng từ)", f"{TT67} Điều 41 khoản 1"),
    ("core.policy_transaction", "status"): ("Trạng thái: APPROVED (tính doanh thu) / PENDING / VOID", ""),
    ("core.policy_transaction", "fx_rate"): ("Tỷ giá hạch toán tại tháng ghi nhận (VND = 1)", "ref.fx_rate"),
    ("core.policy_transaction", "created_by"): ("Người tạo chứng từ (giả)", ""),
    ("core.policy_transaction", "created_at"): ("Thời điểm tạo chứng từ", ""),
    # ---------------- core.transaction_coverage
    ("core.transaction_coverage", "coverage_id"): ("Khóa dòng phí", ""),
    ("core.transaction_coverage", "txn_id"): ("Giao dịch → core.policy_transaction", ""),
    ("core.transaction_coverage", "product_code"): ("Sản phẩm → ref.product", ""),
    ("core.transaction_coverage", "sum_insured"): ("Số tiền bảo hiểm (nguyên tệ; tổng cho cả lô / nhóm)", ""),
    ("core.transaction_coverage", "premium_rate_pct"): ("Tỷ lệ phí % (chỉ sản phẩm tính theo % STBH)", f"{ND67} PL II (cháy nổ bắt buộc)"),
    ("core.transaction_coverage", "insured_count"): ("Số người / xe / giấy chứng nhận được bảo hiểm", ""),
    ("core.transaction_coverage", "premium_orig"): ("Phí 100% hợp đồng, nguyên tệ, chưa VAT; là phần THAY ĐỔI phí của giao dịch (âm với giảm/hoàn/hủy)", "ACORD Coverage NetChangeAmt"),
    ("core.transaction_coverage", "premium_vnd"): ("Phí quy đổi VND, bằng premium_orig × fx_rate", ""),
    ("core.transaction_coverage", "vat_vnd"): ("Thuế GTGT (VND) = premium_vnd × vat_rate", "Luật GTGT 48/2024"),
    ("core.transaction_coverage", "commission_rate_pct"): ("Tỷ lệ hoa hồng % (0 với bán trực tiếp, đấu thầu); ≤ ref.product.max_commission_pct", f"{TT67} Điều 51"),
    # ---------------- core.coinsurance_share / revenue_allocation
    ("core.coinsurance_share", "policy_id"): ("Hợp đồng → core.policy", ""),
    ("core.coinsurance_share", "insurer_code"): ("DNBH tham gia → ref.insurer ('OWN' = chính công ty)", ""),
    ("core.coinsurance_share", "role"): ("Vai trò: LEADER (đồng chính) / FOLLOWER (đồng phụ) / SOLE (bảo hiểm 100%)", f"{TT232} Điều 19"),
    ("core.coinsurance_share", "share_pct"): ("Tỷ lệ tham gia %; tổng theo hợp đồng = 100", f"{LAW} Điều 4 khoản 29"),
    ("core.revenue_allocation", "policy_id"): ("Hợp đồng → core.policy", ""),
    ("core.revenue_allocation", "company_code"): ("Đơn vị được phân bổ doanh thu → ref.company", ""),
    ("core.revenue_allocation", "allocation_type_code"): ("Loại phân bổ → ref.allocation_type", ""),
    ("core.revenue_allocation", "allocation_pct"): ("Tỷ lệ phân bổ %; tổng theo hợp đồng = 100", ""),
}

BUSINESS_RULES = [
    ("Quy ước NULL & tham chiếu danh mục", "Lớp nguồn giữ NULL đúng nghiệp vụ: partner_code NULL = không qua đối tác (hợp lệ); channel_code NULL = nguồn thiếu kênh (lỗi dữ liệu). Mọi mã khác NULL đều có khóa ngoại đã kiểm chứng. Lớp phân tích (view) gán thành viên CHUA_XD / WEB_APP / KHONG_QUA_DT để dòng fact luôn tham chiếu được danh mục", "Quy ước dự án 13/10/2026"),
    ("Đồng bảo hiểm", "Mỗi hợp đồng có ≥ 1 dòng core.coinsurance_share; tổng share_pct = 100. Đơn không đồng BH: 1 dòng insurer_code = 'OWN', role = 'SOLE', 100%", f"{LAW} Điều 4 k29; {TT232} Điều 19"),
    ("Phân bổ doanh thu", "Mỗi hợp đồng có ≥ 1 dòng core.revenue_allocation; tổng allocation_pct = 100", "Thông lệ quản trị Tổng công ty – công ty thành viên"),
    ("Thời điểm ghi nhận doanh thu", "accounting_date = max(ngày cấp, ngày bắt đầu hiệu lực) với cấp mới/tái tục; = ngày chứng từ với SĐBS/hoàn/hủy", f"{TT67} Điều 41 k1 (phát sinh trách nhiệm bảo hiểm)"),
    ("Khoản giảm thu", "Hoàn phí, giảm phí, hủy đơn có premium_orig âm; hạch toán TK 5311/5321 (ref.transaction_type.gl_account)", f"{ND46} Điều 49 k3; {TT232}"),
    ("Trạng thái chứng từ", "status: APPROVED / PENDING / VOID — chỉ APPROVED là chứng từ hợp lệ để tính doanh thu", "Quy ước chuẩn: chỉ chứng từ đã duyệt là căn cứ ghi nhận; PENDING / VOID là kịch bản kiểm thử"),
    ("Doanh thu Tổng công ty", "= tổng doanh thu hợp nhất mọi đơn vị; Khối Trụ sở (company_type = HEAD_OFFICE) là một đơn vị ngang cấp Công ty", "Quy ước chuẩn theo cấp phân tích của đề bài"),
    ("Quy đổi ngoại tệ", "premium_vnd = premium_orig × fx_rate; fx_rate = tỷ giá hạch toán của tháng accounting_date (ref.fx_rate)", "Tỷ giá hạch toán KBNN"),
    ("Thuế GTGT", "vat_vnd = premium_vnd × ref.product.vat_rate; BH con người 0% (không chịu thuế), xe/tài sản/cháy nổ 10%", "Luật GTGT 48/2024 Điều 5 k8, Điều 9"),
    ("Hoa hồng", "commission_rate_pct ≤ ref.product.max_commission_pct; = 0 với bán trực tiếp và đấu thầu", f"{TT67} Điều 51"),
    ("Biểu phí bắt buộc", "TNDS bắt buộc tính theo biểu phí cố định theo loại xe; cháy nổ bắt buộc theo tỷ lệ phí tối thiểu theo nhóm cơ sở", f"{ND67} Phụ lục I, II"),
    ("Cách tính doanh thu từ dữ liệu nguồn (tham khảo cho giai đoạn ETL)", "doanh thu = premium_vnd × share_pct('OWN')/100 × allocation_pct/100, chỉ status = APPROVED, kỳ theo accounting_date", f"{TT232} Điều 19; {TT67} Điều 41"),
]

SCENARIOS = [
    ("Đồng bảo hiểm (đứng đầu / tham gia)", "core.coinsurance_share có > 1 dòng / hợp đồng; role LEADER / FOLLOWER", "Chỉ phần 'OWN' là doanh thu của công ty"),
    ("Phân bổ doanh thu nhiều đơn vị", "core.revenue_allocation: HO_TRO_CHEO, CHUYEN_GIAO", "Doanh thu theo đơn vị được phân bổ, khác đơn vị cấp đơn"),
    ("Khối Trụ sở khai thác rủi ro lớn", "issuing_company_code = 'HO' (company_type = HEAD_OFFICE)", "Phân biệt doanh thu hợp nhất và doanh thu khối Trụ sở"),
    ("SĐBS tăng / giảm phí, hoàn phí, hủy", "txn_type_code END_INC / END_DEC / REFUND / CANCEL", "Số âm/dương vào kỳ phát sinh; TK 5111/5311/5321"),
    ("SĐBS không đổi phí", "txn_type_code END_NOCHG, premium = 0", "Không ảnh hưởng doanh thu"),
    ("Chứng từ chưa duyệt / hủy chứng từ", "status PENDING / VOID (~1,5%)", "Loại khỏi doanh thu"),
    ("Hiệu lực sau ngày cấp (cả sang năm sau)", "effective_date > issue_date → accounting_date > txn_date", "Ghi nhận theo accounting_date, không theo ngày chứng từ"),
    ("Hợp đồng ngoại tệ (USD)", "core.policy.currency_code = 'USD'", "Quy đổi theo fx_rate của giao dịch"),
    ("Hợp đồng nhiều sản phẩm", "VCX ô tô + TNDS; cháy nổ BB + mọi rủi ro tài sản", "Tách doanh thu theo product_code"),
    ("Đơn lô giấy chứng nhận / khách lẻ theo bảng kê", "is_group_policy; ref.customer.is_aggregated_retail", "Loại khi phân tích khách hàng định danh"),
    ("Tái tục", "core.policy.renewal_of_policy_id", "Liên kết hợp đồng năm trước"),
    ("Kênh chưa khai báo (~0,5%)", "core.policy.channel_code IS NULL", "Gán 'Chưa xác định'"),
    ("Đơn vị không gắn địa bàn", "ref.company.province_code IS NULL (Trung tâm Kinh doanh số)", "Vùng miền để trống"),
]


# ---------------------------------------------------------------------------
# Bổ sung cho bộ dữ liệu KHỐI LƯỢNG LỚN (gen_volume.py → reportapi.bronze.ins_*)
# Tách riêng: các cột này không có trong DDL v2 nên không được ghi vào 01b_column_comments.sql
# ---------------------------------------------------------------------------
VOLUME_COLUMNS = {
    ("ref.customer", "gender"): ("Giới tính M / F — chỉ khách cá nhân, hộ gia đình (NULL với tổ chức)", "Dữ liệu sinh ngẫu nhiên"),
    ("ref.customer", "birth_year"): ("Năm sinh — chỉ khách cá nhân, hộ gia đình; bên mua ≥ 18 tuổi", "Dữ liệu sinh ngẫu nhiên"),
    ("core.policy", "prev_policy_no"): ("Số hợp đồng năm trước được tái tục (hợp đồng ngoài kỳ dữ liệu nên lưu text; NULL = cấp mới)", ""),
}
VOLUME_BUSINESS_RULES = [
    ("Thời điểm ghi nhận (bản khối lượng lớn)", "accounting_date = max(ngày chứng từ, ngày hiệu lực) cho MỌI giao dịch, kể cả SĐBS / hoàn / hủy (hủy chuyến du lịch trước ngày đi được ghi nhận cùng ngày với doanh thu gốc)", f"{TT67} Điều 41 k1"),
    ("Mức theo tháng [CHÍNH THỨC]", "Phí/ngày tháng 9 = 1,479 × tháng 8, theo phí gốc phi nhân thọ 2025 của Bộ Tài chính (7T 50.784 · 8T 56.376 · 9T 64.378 tỷ). Trong tháng phân bố đều — không có hiệu ứng cuối tháng", "Bản tin thị trường bảo hiểm tháng 8–10/2025, Bộ Tài chính"),
    ("Ngày hiệu lực [QUY ƯỚC]", "Đơn không phải du lịch hiệu lực ngay ngày cấp (không có nguồn về độ trễ); học sinh hiệu lực từ khai giảng 5/9", "Khung kế hoạch năm học Bộ GD&ĐT"),
    ("Du lịch [DATASET] / [NGUỒN THAY THẾ]", "Số ngày mua trước chuyến đi và độ dài chuyến đi trong nước lấy phân bố thực nghiệm từ Hotel booking demand (Data in Brief 2019); thời hạn chuyến đi quốc tế, cơ cấu kênh trung gian, tỷ lệ hoa hồng từ dataset Travel Insurance (hoa hồng cắt ở trần 20%)", "calibration/README.md"),
    ("Ngày làm việc [QUY ƯỚC]", "Kênh văn phòng giảm thứ 7, chủ nhật, lễ 01–02/9; kênh số hoạt động đều mọi ngày", "BLLĐ 2019 Điều 112"),
    ("Kiểm tra toàn vẹn", "41 quy tắc nghiệp vụ (audit/consistency_checks.sql): hợp đồng, khách hàng, giao dịch, dòng phí, đồng BH, phân bổ, tham chiếu danh mục — kết quả mong đợi 0 vi phạm", "audit/run_audit.py"),
]
