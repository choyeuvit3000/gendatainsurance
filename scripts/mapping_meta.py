"""Mapping mô hình v2 ↔ hệ thống nguồn PIAS (PVS_2026) — kèm bằng chứng kiểm chứng.

TÀI LIỆU NỘI BỘ DỰ ÁN. Kiểm chứng chỉ đọc trên chứng từ tháng 06/2025 (99.454 chứng từ, 85.568 đơn gốc);
một số phép thử chạy trên mẫu 01–07/06/2025 (23.379 chứng từ đã duyệt). Chỉ ghi số lượng / tỷ lệ, không ghi số tiền.

Trạng thái:
  OK   khớp trực tiếp, đã kiểm chứng
  TF   biến đổi theo quy tắc, đã kiểm chứng
  STD  quy ước chuẩn do dự án chốt khi nguồn mơ hồ — có căn cứ dữ liệu / quy định, áp dụng làm chuẩn
  GAP  PIAS không có — v2 sinh mới / suy ra
  OUT  PIAS có nhưng v2 không dùng (ngoài phạm vi)
"""

SAMPLE = "Chứng từ tháng 06/2025: 99.454 chứng từ (85.568 đơn gốc, 13.886 SĐBS); 98.773 đã duyệt"

# v2 table -> (nguồn PIAS, ghi chú, [(cột v2, nguồn PIAS, quy tắc, trạng thái, bằng chứng)])
TABLE_MAP = {
    "core.policy": ("nvu_bht_ctu (dòng ma_sdbs = '')", "PIAS không tách hợp đồng / giao dịch: hợp đồng = chứng từ đơn gốc", [
        ("policy_id", "nvu_bht_ctu.pr_key", "pr_key của chứng từ đơn gốc", "OK", ""),
        ("policy_no", "nvu_bht_ctu.so_donbh", "Giữ nguyên", "OK", "Duy nhất ở 100% trong 85.568 đơn gốc"),
        ("issuing_company_code", "nvu_bht_ctu.ma_donvi", "Giữ nguyên. Nếu rỗng: lấy đoạn 2 của so_donbh; nếu mã đó không có trong dm_donvi (vd 'FE' — đơn đối tác số) → đơn vị kinh doanh số (DIGITAL)", "STD",
         "682 chứng từ đã duyệt có ma_donvi rỗng — đơn đối tác dạng 25/FE/18/SMCN/…; mã 'FE' không có trong dm_donvi"),
        ("customer_code", "nvu_bht_ctu.ma_kh", "Giữ nguyên", "OK", "1 / 99.454 không có trong dm_khach"),
        ("channel_code", "ma_kthac + ma_nhkenhbh + dm_khach.to_chuc (của ma_daily)", "Theo bảng mã 'Kênh'", "TF",
         "ma_kthac: 1 đại lý 69% (100% có ma_daily), 2 môi giới 2,6% (100% có ma_moigioi), 31/32 trực tiếp 28%"),
        ("partner_code", "nvu_bht_ctu.ma_kenhbh", "003 → dm_bancas (3 ký tự đầu = ngân hàng); 004/007/008/012/016 → dm_kenhnvu; N08xx → dm_khach (showroom)", "TF",
         "Ngân hàng: 99,7% khớp dm_bancas; nhóm 007/012/004/008/016: ~100% khớp dm_kenhnvu; N08xx: 100% là mã khách hàng"),
        ("currency_code", "nvu_bht_ctu.ma_tte", "Giữ nguyên", "OK", "VND 91%, USD 8%, còn lại EUR/JPY…"),
        ("issue_date", "nvu_bht_ctu.ngay_capd", "Giữ nguyên", "OK", "ngay_ctu = ngay_capd ở 94,6% đơn gốc"),
        ("effective_date", "nvu_bht_ctu.ngay_dau", "Giữ nguyên", "OK", "43,8% đơn bắt đầu hiệu lực sau ngày chứng từ; 7,7% trước"),
        ("expiry_date", "nvu_bht_ctu.ngay_cuoi", "Giữ nguyên", "OK", ""),
        ("is_group_policy", "nvu_bht_seri (đếm GCN theo fr_key) / nvu_bht_ct.so_tvien", "TRUE nếu > 1 GCN hoặc > 1 thành viên", "TF",
         "Đơn xe: 3.462 đơn mô tô ↔ 68.386 GCN; 34.779 đơn ô tô ↔ 79.892 GCN"),
        ("renewal_of_policy_id", "(không có liên kết tường minh)", "Suy ra: cùng khách + cùng loại đơn, cấp trước 300–430 ngày", "GAP",
         "so_donbh_tt và rtinh_trang_taituc luôn rỗng. Quy ước: chỉ nối khi rloai_don = '01' (tái tục) — lấy đơn gốc gần nhất cùng ma_kh + ma_donbh"),
    ]),
    "core.policy_transaction": ("nvu_bht_ctu (mọi dòng)", "Mỗi chứng từ (đơn gốc hoặc SĐBS) = 1 giao dịch", [
        ("txn_id", "nvu_bht_ctu.pr_key", "Giữ nguyên", "OK", ""),
        ("policy_id", "pr_key của đơn gốc cùng so_donbh", "SĐBS nối về đơn gốc theo so_donbh", "TF", "100% trong 13.886 SĐBS tìm được đơn gốc"),
        ("txn_no", "nvu_bht_ctu.so_donbh_bs (SĐBS) / so_donbh", "", "OK", "100% SĐBS có so_donbh_bs"),
        ("txn_type_code", "nvu_bht_ctu.ma_sdbs + ma_sdbs_ct; đơn gốc: rloai_don", "Theo bảng mã 'Loại giao dịch' — dùng mã chi tiết ma_sdbs_ct; đơn gốc rloai_don '01' → RENEW, '02' → NEW", "TF",
         "Procedure GuiMail_Taituc_1Thang nhận diện đơn bị hủy bằng ma_sdbs_ct IN ('0401','0302'). rloai_don: hàng hóa / giải thưởng (không bao giờ tái tục) 100% '02'; sức khỏe nhóm 48%, cháy nổ 45%, ô tô 26% là '01'"),
        ("txn_date", "nvu_bht_ctu.ngay_ctu", "Giữ nguyên", "OK", ""),
        ("accounting_date", "nvu_bht_ctu.ngay_ctu, ngay_dau (đối soát: nvu_bht_ktu.ngay_ctu_kt qua nvu_bht_kt.pr_key_nvu_bht_ct = nvu_bht_ct.pr_key)",
         "Quy ước: đơn gốc / tái tục = max(ngay_ctu, ngay_dau) — thời điểm phát sinh trách nhiệm (TT 67/2023 Đ41); SĐBS = ngay_ctu. Ngày hạch toán chỉ dùng đối soát", "STD",
         "90% chứng từ có dòng hạch toán; cùng ngày 26%, trễ 1–31 ngày 67%, > 31 ngày 6%. LƯU Ý: kt.pr_key_nvu KHÔNG nối được ctu.pr_key (trùng dải khóa)"),
        ("status", "nvu_bht_ctu.trang_thai (+ tam_tinh)", "02 → APPROVED; 01 → PENDING; VOID không phát sinh từ PIAS", "TF",
         "02: 98.773 · 01: 681 · tam_tinh luôn 0. Procedure nghiệp vụ lọc trang_thai = '02'. Chưa thấy mã tương ứng VOID"),
        ("fx_rate", "nvu_bht_ctu.tygia_ht", "Giữ nguyên", "OK", "VND = 1 ở 100%; USD khớp dm_tygia (loai_ht = 'HT') 65%, phần còn lại tỷ giá riêng theo hợp đồng"),
        ("created_by", "nvu_bht_ctu.ma_user", "Giữ nguyên", "OK", ""),
        ("created_at", "nvu_bht_ctu.ngay_cnhat", "Giữ nguyên", "OK", ""),
    ]),
    "core.transaction_coverage": ("nvu_bht_ct", "fr_key → nvu_bht_ctu.pr_key", [
        ("coverage_id", "nvu_bht_ct.pr_key", "", "OK", ""),
        ("txn_id", "nvu_bht_ct.fr_key", "", "OK", ""),
        ("product_code", "nvu_bht_ct.ma_sp", "Theo bảng mã 'Sản phẩm'", "TF", "0 mã không có trong dm_sp; 0 mã tổng hợp (tong_hop = 1)"),
        ("sum_insured", "nvu_bht_ct.so_tienbh", "", "OK", ""),
        ("premium_rate_pct", "nvu_bht_ct.tyle_phi", "Đơn vị %: dùng nguyên giá trị", "OK", "75% dòng khớp so_tienbh × tyle_phi / 100; tính như phân số chỉ khớp 1%"),
        ("insured_count", "COUNT(nvu_bht_seri) theo chứng từ; nếu không có: COUNT(nvu_bht_the); mặc định 1", "Quy ước: đếm giấy chứng nhận / thẻ", "STD",
         "nvu_bht_ct.so_tvien luôn = 0 ở mọi nhóm sản phẩm (mẫu 01–07/06/2025) → không dùng"),
        ("premium_orig", "nvu_bht_ct.nguyen_tep", "Phí 100% hợp đồng, nguyên tệ", "OK", "27% dòng có nguyen_tep = 0 (thành phần gói / không phí)"),
        ("premium_vnd", "nvu_bht_ct.so_tienp", "", "OK", "so_tienp = nguyen_tep × tygia_ht ở 99,4% dòng"),
        ("vat_vnd", "nvu_bht_ct.tien_vat", "", "OK", "Đúng công thức ở 99,5%; muc_vat ∈ {0, 10} (1 dòng = 100 — lỗi nhập liệu)"),
        ("commission_rate_pct", "nvu_bht_kt.tyle_hhong × 100 (đại lý); nvu_bht_ctu.tyle_moigioi (môi giới)", "", "TF",
         "nvu_bht_ct.tyle_hhong gần như luôn 0 (1 / 169.269 dòng) → KHÔNG dùng. kt.tyle_hhong là phân số (0,20 = 20%), khớp dm_hhong; > 0 ở 29% dòng. tyle_moigioi có ở 92,5% đơn môi giới"),
    ]),
    "core.coinsurance_share": ("nvu_bht_dbh + dòng 'OWN' suy ra", "nvu_bht_dbh chỉ chứa các DN bảo hiểm KHÁC", [
        ("policy_id", "nvu_bht_dbh.fr_key", "→ pr_key đơn gốc", "OK", "2.041 đơn có đồng BH trong tháng"),
        ("insurer_code", "nvu_bht_dbh.ma_khach (dm_khach)", "Dòng 'OWN' = chính công ty, sinh thêm", "TF",
         "Đối tác: Bảo hiểm BIDV, Bảo Việt, MIC, PTI, PJICO… — không có dòng của chính công ty"),
        ("role", "nvu_bht_dbh.vai_tro", "Có dòng 'Đồng chính' → công ty là FOLLOWER; chỉ có 'Đồng phụ' → công ty là LEADER; không có dòng → SOLE", "TF",
         "'Đồng chính': 469 dòng / 469 đơn (TB 47,5%); 'Đồng phụ': 4.219 dòng / 1.885 đơn (TB 18%)"),
        ("share_pct", "nvu_bht_dbh.nguyen_tep, nvu_bht_ct.nguyen_tep", "Quy ước theo số tiền: OWN = (Σct − Σdbh) / Σct × 100; DN khác = dbh / Σct × 100 (tyle_tg chỉ tham chiếu)", "STD",
         "Theo số tiền khớp nvu_bht_pbo 99,5%; theo tỷ lệ chỉ khớp 86%"),
    ]),
    "core.revenue_allocation": ("nvu_bht_pbo", "fr_key → nvu_bht_ctu.pr_key; mỗi chứng từ ≥ 1 dòng", [
        ("policy_id", "nvu_bht_pbo.fr_key", "→ pr_key đơn gốc", "OK", "100% chứng từ có dòng phân bổ"),
        ("company_code", "nvu_bht_pbo.ma_donvi_pbo", "", "OK", "80% dòng phân bổ cho chính đơn vị cấp đơn"),
        ("allocation_type_code", "nvu_bht_pbo.ma_kieupbo", "Theo bảng mã 'Loại phân bổ'", "TF", "02.02: 135.137 · 02.01: 7.471 · 01: 114 · rỗng: 60"),
        ("allocation_pct", "nvu_bht_pbo.tyle_pbo", "", "OK", "Σtyle_pbo = 100 ở 100% chứng từ đã duyệt"),
        ("(không dùng)", "nvu_bht_pbo.ma_khpbo", "Người / phòng hưởng doanh thu — ngoài 6 chiều phân tích", "OUT",
         "100% có trong dm_khach; không trùng đại lý (ma_daily) → là cán bộ / phòng khai thác"),
        ("(không dùng)", "nvu_bht_pbo.ky_pbo", "", "OK", "Luôn = 0"),
    ]),
    "ref.company": ("dm_donvi (52 đơn vị) + cấp Tổng công ty bổ sung", "dm_donvi không có cấp cha", [
        ("company_code / name", "dm_donvi.ma_donvi / ten_donvi", "", "OK", ""),
        ("company_type", "(suy ra từ dm_donvi)", "'00' Trụ sở và các trung tâm trực thuộc (27 bảo lãnh viện phí, 31/32 CSKH) → HEAD_OFFICE; PVI Digital + mã đối tác số → DIGITAL; còn lại → MEMBER", "STD", "Trung tâm là đơn vị trực thuộc trụ sở, không phải công ty thành viên"),
        ("parent_company_code", "(không có)", "Gán Tổng công ty", "GAP", ""),
        ("province_code", "dm_donvi.ma_tinh (VIxx, 63 tỉnh cũ)", "Map 63 → 34 tỉnh theo NQ 202/2025", "TF", "Một số đơn vị mới không có ma_tinh"),
    ]),
    "ref.province / ref.region": ("dm_nuoc_tinhtp", "", [
        ("province_code", "dm_nuoc_tinhtp.ma_tinh (4 ký tự)", "Bảng map 63 → 34 tỉnh", "TF", ""),
        ("region_code", "dm_nuoc_tinhtp.ma_vmien", "MIENBAC / MIENTRUNG / MIENNAM", "OK", ""),
    ]),
    "ref.product / product_group / line_of_business": ("dm_sp, dm_nsp", "dm_sp.ma_nsp1 không nhất quán → dùng bảng crosswalk", [
        ("product_code", "dm_sp.ma_sp (6 ký tự, tong_hop = 0)", "Nhiều mã PIAS → 1 sản phẩm v2", "TF", "Xem bảng mã 'Sản phẩm'"),
        ("lob_code", "dm_nsp (2 ký tự)", "06 cháy nổ tách riêng khỏi 02 tài sản", "TF", ""),
        ("report_line_code", "(không có; dm_sp.ma_tagetik là phân loại khác)", "Gán theo TT 67/2023 Mẫu 2-PNT", "GAP", ""),
        ("vat_rate", "dm_sp.muc_vat", "", "OK", ""),
    ]),
    "ref.channel / ref.partner": ("dm_kthac, dm_nhkenhkt, dm_kenhnvu, dm_bancas, dm_khach", "", [
        ("channel_code", "dm_kthac + dm_nhkenhkt", "Theo bảng mã 'Kênh'", "TF", ""),
        ("partner_code", "dm_kenhnvu / dm_bancas / dm_khach", "", "TF", "dm_bancas: mã 6 ký tự, 3 ký tự đầu = ngân hàng (000 VP Bank, 004 SeABank, 020 HDBank…)"),
    ]),
    "ref.customer / customer_segment": ("dm_khach, dm_nhkh", "", [
        ("customer_code / name / tax_code", "dm_khach.ma_kh / ten_kh / maso_vat", "", "OK", ""),
        ("segment_code", "dm_khach.to_chuc + ma_nhkh", "KLCN → CA_NHAN; N13 → HO_GIA_DINH; N04 → DN_TRONG_NUOC; N05 → DN_FDI…", "TF", "ma_nhkh rỗng ở phần lớn khách → dựa vào to_chuc"),
        ("is_aggregated_retail", "(không có cờ)", "Nhận diện khách gộp theo bảng kê", "GAP", "Người được bảo hiểm thật nằm ở nvu_bht_seri (ten_khach, bien_ksoat)"),
    ]),
    "ref.transaction_type / insurer / allocation_type / fx_rate": ("nvu_dm_sdbs, dm_khach, nvu_dm_kieupbo, dm_tygia", "", [
        ("txn_type_code", "nvu_dm_sdbs", "Theo bảng mã 'Loại giao dịch'", "TF", ""),
        ("insurer_code", "dm_khach (các DNBH xuất hiện trong nvu_bht_dbh)", "", "TF", "Nhóm khách N21 'Nhà Đồng Bảo hiểm' chưa được dùng nhất quán"),
        ("allocation_type_code", "nvu_dm_kieupbo", "", "TF", ""),
        ("rate_to_vnd", "dm_tygia.ty_gia (loai_ht = 'HT')", "Quy ước: ref.fx_rate lấy loại HT; giao dịch luôn dùng tygia_ht của chính chứng từ", "STD", "loai_ht: HT (hạch toán, 19 dòng), TT (5.199), BA (484); 65% giao dịch USD khớp HT"),
    ]),
}

# Bảng mã: tên -> (mô tả, [cột], [dòng])
CODE_MAPS = {
    "Loại giao dịch": ("ma_sdbs / ma_sdbs_ct → txn_type_code. Số chứng từ T6/2025.", ["ma_sdbs", "ma_sdbs_ct", "Ý nghĩa (nvu_dm_sdbs)", "Số CT", "→ v2", "TT"], [
        ("'' (rloai_don = '02')", "''", "Đơn gốc — cấp mới", "≈ 70.000", "NEW", "TF"),
        ("'' (rloai_don = '01')", "''", "Đơn gốc — tái tục", "≈ 12.100", "RENEW", "TF"),
        ("'' (rloai_don = '' / '1' / 'txtMa_rl')", "''", "Đơn gốc — cờ rỗng hoặc rác", "≈ 3.500", "NEW (mặc định)", "STD"),
        ("01", "0101 / 0102 / 0103 / 0104 / ''", "Tăng phí (chỉ tăng phí; tăng phí + tăng/giảm STBH; đổi tỷ lệ đồng BH)", "3.005 / 685 / 8 / 1 / 7", "END_INC", "TF"),
        ("02", "0201 / 0202 / 0203 / ''", "Giảm phí", "2.319 / 1.235 / 1 / 12", "END_DEC", "TF"),
        ("03", "0301 / ''", "Hoàn phí", "346 / 6", "REFUND", "TF"),
        ("03", "0302", "Hoàn phí hủy đơn", "767", "CANCEL", "TF"),
        ("04", "0401", "Hủy đơn", "2.042", "CANCEL", "TF"),
        ("05", "0501 / 0502 / 0503 / ''", "Thay đổi khác (không đổi phí / chỉ đổi STBH)", "3.293 / 30 / 49 / 13", "END_NOCHG", "TF"),
        ("06", "0601", "Đơn BH có phí đặt cọc, theo kỳ", "67", "Theo dấu phí: > 0 END_INC, < 0 END_DEC, = 0 END_NOCHG", "STD"),
    ]),
    "Trạng thái": ("trang_thai → status", ["trang_thai", "Số CT", "→ v2", "TT"], [
        ("02", "98.773", "APPROVED", "TF"), ("01", "681", "PENDING", "TF"), ("(không có trong PIAS)", "—", "VOID — không phát sinh", "STD"),
    ]),
    "Kênh": ("Áp dụng theo THỨ TỰ ƯU TIÊN từ trên xuống: môi giới → ngân hàng → điện tử → đại lý → trực tiếp. Số chứng từ T6/2025.", ["ma_kthac", "ma_nhkenhbh", "Điều kiện thêm", "Số CT", "→ v2", "TT"], [
        ("2 Qua môi giới", "bất kỳ", "", "2.603", "MOI_GIOI", "TF"),
        ("bất kỳ (1 hoặc 32)", "003 Ngân hàng & TCTC", "ma_kenhbh là chi nhánh ngân hàng (99,7% khớp dm_bancas)", "10.500", "BANCA — Mẫu 3-PNT xếp 'qua TCTD' theo đối tác", "STD"),
        ("bất kỳ", "006 Trực tuyến", "", "—", "DIEN_TU", "TF"),
        ("bất kỳ", "008 Điện thoại di động (app MyPVI)", "", "≈ 790", "DIEN_TU — giao dịch điện tử (Luật KDBH Đ87 k4 điểm d)", "STD"),
        ("1 Qua đại lý", "999 / 007 / 012 / 004 / N08xx / 016", "dm_khach.to_chuc(ma_daily) = 1", "≈ 35.300", "DAI_LY_TC", "TF"),
        ("1 Qua đại lý", "999 / 007 / 012 / 004 / N08xx / 016", "dm_khach.to_chuc(ma_daily) = 0", "≈ 23.000", "DAI_LY_CN", "TF"),
        ("3 / 31 / 32 Trực tiếp", "999 và các nhóm khác", "", "≈ 25.000", "TRUC_TIEP", "TF"),
        ("—", "—", "Đấu thầu", "—", "DAU_THAU (PIAS không có mã)", "GAP"),
    ]),
    "Vai trò đồng BH": ("nvu_bht_dbh.vai_tro → role của công ty", ["Dòng trong nvu_bht_dbh", "Vai trò của công ty", "Số đơn", "TT"], [
        ("Không có dòng", "SOLE (100%)", "≈ 97.400", "TF"),
        ("Có dòng 'Đồng chính' (DN khác đứng đầu)", "FOLLOWER", "469", "TF"),
        ("Chỉ có dòng 'Đồng phụ'", "LEADER", "≈ 1.570", "TF"),
    ]),
    "Loại phân bổ": ("nvu_bht_pbo.ma_kieupbo (nvu_dm_kieupbo) → allocation_type_code", ["ma_kieupbo", "Ý nghĩa", "Số dòng", "→ v2", "TT"], [
        ("02.02", "Tự khai thác có tính hiệu quả", "135.137", "TU_KHAI_THAC (cùng đơn vị) / HO_TRO_CHEO (khác đơn vị, 20%)", "TF"),
        ("02.01", "Tự khai thác không tính hiệu quả", "7.471", "HO_TRO_CHEO (99,9% khác đơn vị)", "TF"),
        ("01", "Chuyển giao doanh thu", "114", "CHUYEN_GIAO", "TF"),
        ("''", "(rỗng)", "60", "TU_KHAI_THAC nếu cùng đơn vị cấp đơn, HO_TRO_CHEO nếu khác", "STD"),
    ]),
    "Sản phẩm": ("dm_sp.ma_sp (6 ký tự) → product_code. Số đơn có phát sinh T6/2025.", ["Sản phẩm v2", "Mã dm_sp", "Ghi chú", "TT"], [
        ("XE_TNDS_OTO", "050101", "≈ 23.900 đơn", "TF"),
        ("XE_TNDS_MOTO", "050201", "≈ 3.200 đơn", "TF"),
        ("XE_VCX_OTO", "050104, 050106 (pin)", "≈ 10.800 đơn", "TF"),
        ("XE_VCX_MOTO", "050205", "", "TF"),
        ("NG_HSSV_TN / NG_HSSV_SK", "010301 / 010302, 010303", "Mùa thấp (tháng 6)", "TF"),
        ("NG_DL_ND", "010601, 010602", "≈ 5.500 đơn", "TF"),
        ("NG_DL_QT", "010603, 010604, 010605, 010606, 010607, 010610, 010612", "7 mã", "TF"),
        ("NG_SM_CN", "010401", "", "TF"),
        ("NG_NVV", "010402 (An tâm tín dụng), 010405", "", "TF"),
        ("NG_TN24", "010201, 010202, 010205, 010206, 010208, 010209, 010210", "PIAS nhóm 0102 'Tai nạn con người'", "TF"),
        ("NG_SK_NHOM / NG_SK_CN", "010101, 010701–010706, 010713–010719", "Theo dm_khach.to_chuc của bên mua: tổ chức → NHOM, cá nhân → CN. 010702: 100% tổ chức; 010713: 99,6%; 010704: 78% cá nhân", "STD"),
        ("NG_SK_BHN", "010707, 010708, 010711, 010712", "", "TF"),
        ("TS_NHA", "020108, 020113, 020115, 020118, 020123, 020124, 020125, 020127", "8 mã", "TF"),
        ("TS_MRR", "020102, 020107, 020109, 020111, 020116", "", "TF"),
        ("TS_MRRCN", "020103, 020120", "", "TF"),
        ("CHN_BB", "060101, 060104, 060103, 060105", "060103/060105 = cháy nổ bắt buộc kèm gián đoạn kinh doanh → theo thành phần bắt buộc", "STD"),
        ("CHN_TN", "020101", "Cháy nổ tự nguyện nằm trong nhóm 0201 của PIAS", "TF"),
        ("NG_TN24", "050103 (tai nạn người ngồi trên xe), 0108xx (bồi thường người lao động)", "Bản chất là tai nạn con người — dòng A.1 Mẫu 2-PNT", "STD"),
        ("NG_SK_CN", "0105xx (trợ cấp nằm viện – phẫu thuật)", "Bản chất bảo hiểm sức khỏe", "STD"),
        ("TS_MRRCN", "020104, 020105, 020106, 020112, 020121 (máy móc, thiết bị)", "Tài sản kỹ thuật thuộc nhóm 0201 của PIAS", "STD"),
        ("(ngoài phạm vi POC)", "050102, 050105, 050202, 050204 (TNDS tự nguyện, TNDS hàng hóa trên xe)", "POC nhóm Xe chỉ gồm TNDS bắt buộc và vật chất xe (đề bài)", "OUT"),
        ("(loại trừ)", "060102 'Phí PCCC'", "Không phải phí bảo hiểm", "OUT"),
    ]),
}

# Đính chính so với bản mapping trước
CORRECTIONS = [
    ("Hoa hồng", "nvu_bht_ct.tyle_hhong", "nvu_bht_kt.tyle_hhong × 100 (đại lý) + nvu_bht_ctu.tyle_moigioi (môi giới)", "ct.tyle_hhong > 0 chỉ ở 1 / 169.269 dòng"),
    ("Kênh", "Chỉ ma_nhkenhbh", "ma_kthac (đại lý / môi giới / trực tiếp) × ma_nhkenhbh × loại đại lý", "ma_kthac là hình thức khai thác theo dm_kthac"),
    ("Đại lý cá nhân / tổ chức", "Theo nhóm kênh", "Theo dm_khach.to_chuc của ma_daily", "Nhóm 999: 52% tổ chức / 48% cá nhân"),
    ("Loại giao dịch", "Chỉ ma_sdbs (2 ký tự)", "ma_sdbs_ct (4 ký tự): 0302 hoàn phí hủy đơn → CANCEL", "Procedure nghiệp vụ dùng ma_sdbs_ct để nhận diện hủy"),
    ("Tái tục", "Không xác định được", "nvu_bht_ctu.rloai_don: '01' tái tục, '02' cấp mới", "Hàng hóa / giải thưởng 100% '02'; sức khỏe nhóm 48% '01'"),
    ("Ngày hạch toán", "nvu_bht_kt.pr_key_nvu → ctu", "nvu_bht_kt.pr_key_nvu_bht_ct → nvu_bht_ct.pr_key", "Nối theo pr_key_nvu cho ra hóa đơn năm 2021 — trùng dải khóa"),
    ("Phần của công ty (đồng BH)", "100 − Σtyle_tg", "Theo số tiền: (ct − Σdbh) / ct", "Khớp 99,5% so với 86%"),
    ("Đối tác ngân hàng", "Không xác định", "ma_kenhbh → dm_bancas (3 ký tự đầu = ngân hàng)", "Khớp 99,7%"),
]

DECISIONS = [  # (vấn đề, quy ước chuẩn, căn cứ)
    ("Định nghĩa doanh thu", "Doanh thu phí bảo hiểm gốc phần của công ty, chưa VAT, sau đồng BH và theo đơn vị được phân bổ (không dùng doanh thu kế toán phân bổ theo kỳ)", "TT 232/2012 Đ19; dữ liệu: nvu_bht_pbo = ct − dbh ở 99,5% đơn"),
    ("Ngày ghi nhận doanh thu", "Đơn gốc / tái tục: max(ngay_ctu, ngay_dau). SĐBS: ngay_ctu. Ngày hạch toán (nvu_bht_ktu) chỉ để đối soát", "TT 67/2023 Đ41 (phát sinh trách nhiệm); ngày hạch toán chỉ có ở 90% chứng từ"),
    ("Trạng thái chứng từ", "02 → APPROVED (tính doanh thu); 01 → PENDING; PIAS không có VOID", "Procedure nghiệp vụ lọc trang_thai = '02'"),
    ("Tái tục", "rloai_don '01' → RENEW, '02' → NEW, giá trị khác → NEW; nối đơn cũ cùng khách + cùng loại đơn, cấp trước 300–430 ngày", "Hàng hóa / giải thưởng 100% '02'; sức khỏe nhóm 48% '01'"),
    ("Phần của công ty khi đồng BH", "Tính theo số tiền: (Σct − Σdbh) / Σct", "Khớp nvu_bht_pbo 99,5% (theo tỷ lệ chỉ 86%)"),
    ("Kênh bán", "Thứ tự ưu tiên: môi giới (ma_kthac 2) → ngân hàng (nhóm 003) → điện tử (006, 008) → đại lý tổ chức / cá nhân (theo to_chuc của ma_daily) → trực tiếp", "Luật KDBH Đ87 k4; TT 67/2023 Mẫu 3-PNT"),
    ("Đơn vị rỗng", "Lấy đoạn 2 của so_donbh; không có trong dm_donvi → đơn vị kinh doanh số", "682 chứng từ dạng 25/FE/… (đối tác số)"),
    ("Doanh thu Tổng công ty", "= Tổng doanh thu hợp nhất mọi đơn vị. Khối Trụ sở (gồm các trung tâm trực thuộc) là một đơn vị ngang cấp Công ty", "Cấp phân tích của đề bài: Tổng DT → Tổng công ty → Công ty"),
    ("Sức khỏe nhóm / cá nhân", "Theo to_chuc của bên mua", "010702: 100% tổ chức; 010704: 78% cá nhân"),
    ("Số người / xe được bảo hiểm", "Đếm GCN (nvu_bht_seri) hoặc thẻ (nvu_bht_the), mặc định 1", "nvu_bht_ct.so_tvien luôn = 0"),
    ("Sản phẩm biên", "Tai nạn người ngồi trên xe, bồi thường NLĐ → tai nạn; trợ cấp nằm viện → sức khỏe; máy móc thiết bị → mọi rủi ro công nghiệp; TNDS tự nguyện và phí PCCC → loại", "Bản chất rủi ro theo NĐ 46/2023 Đ4–5 và Mẫu 2-PNT"),
    ("Người hưởng phân bổ (ma_khpbo)", "Không đưa vào v2", "Ngoài 6 chiều phân tích của đề bài"),
    ("Kênh / đối tác để trống", "Lớp nguồn (bronze, landing) giữ NULL như hệ thống lõi: đối tác NULL = không qua đối tác (hợp lệ), kênh NULL = thiếu dữ liệu. Lớp staging / phân tích gán: kênh NULL → CHUA_XD; đối tác NULL → WEB_APP (kênh điện tử) hoặc KHONG_QUA_DT (kênh khác) để mọi dòng fact tham chiếu được danh mục", "Đối tác không bắt buộc theo nghiệp vụ; kênh bắt buộc (TT 67/2023 Mẫu 3-PNT) nhưng nguồn có thể thiếu — chốt 13/10/2026"),
]

# Sơ đồ luồng nguồn → đích (mermaid flowchart)
FLOW = """flowchart LR
  subgraph PIAS["PIAS (PVS_2026)"]
    ctu["nvu_bht_ctu<br/>chứng từ đơn / SĐBS"]
    ct["nvu_bht_ct<br/>phí theo SP"]
    dbh["nvu_bht_dbh<br/>đồng BH (DN khác)"]
    pbo["nvu_bht_pbo<br/>phân bổ DT"]
    kt["nvu_bht_kt / ktu<br/>hạch toán, hoa hồng"]
    seri["nvu_bht_seri<br/>GCN"]
    dm["dm_donvi · dm_sp · dm_nsp · dm_kthac · dm_nhkenhkt<br/>dm_kenhnvu · dm_bancas · dm_khach · nvu_dm_sdbs · nvu_dm_kieupbo · dm_tygia"]
  end
  subgraph V2["Mô hình v2"]
    pol["core.policy"]
    txn["core.policy_transaction"]
    cov["core.transaction_coverage"]
    coi["core.coinsurance_share"]
    alc["core.revenue_allocation"]
    ref["ref.* (16 danh mục)"]
  end
  ctu -->|"đơn gốc"| pol
  ctu -->|"mọi chứng từ"| txn
  kt -->|"ngày hạch toán"| txn
  ct --> cov
  kt -->|"hoa hồng"| cov
  dbh -->|"+ dòng OWN"| coi
  pbo --> alc
  seri -->|"đơn nhóm / lô"| pol
  dm --> ref"""
