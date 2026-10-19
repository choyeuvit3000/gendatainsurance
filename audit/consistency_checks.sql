-- =====================================================================
-- RÀ SOÁT TÍNH NHẤT QUÁN NGHIỆP VỤ — bronze.ins_* (dữ liệu sinh bởi gen_volume.py)
-- Mỗi câu trả về: mã kiểm tra | mô tả | số dòng vi phạm | ví dụ
-- Chạy: python audit/run_audit.py  (hoặc từng câu trong DBeaver)
-- =====================================================================

-- Bảng tạm: sản phẩm chính + giao dịch gốc của mỗi hợp đồng
CREATE TEMP TABLE _main AS
SELECT DISTINCT ON (t.policy_id) t.policy_id, t.txn_id, t.txn_type_code, t.status, c.product_code, c.insured_count
FROM bronze.ins_policy_transaction t
JOIN bronze.ins_transaction_coverage c USING (txn_id)
WHERE t.txn_type_code IN ('NEW', 'RENEW')
ORDER BY t.policy_id, c.coverage_id;
CREATE INDEX ON _main (policy_id);
ANALYZE _main;

-- ---------------------------------------------------------------- HỢP ĐỒNG
-- P01 kênh của hợp đồng ≠ kênh của đối tác
SELECT 'P01', 'Kênh hợp đồng ≠ kênh của đối tác', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN bronze.ins_partner pa USING (partner_code)
WHERE pa.channel_code IS DISTINCT FROM p.channel_code;

-- P02 loại đối tác không bán sản phẩm này (ma trận hợp lệ theo thực tế thị trường)
SELECT 'P02', 'Loại đối tác không phù hợp sản phẩm: ' || pa.partner_type || ' × ' || m.product_code, count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN bronze.ins_partner pa USING (partner_code) JOIN _main m USING (policy_id)
WHERE NOT (
      (pa.partner_type = 'NGAN_HANG'       AND m.product_code IN ('NG_NVV','NG_SK_CN','NG_SK_BHN','NG_SM_CN','TS_NHA','XE_VCX_OTO','CHN_BB','CHN_TN'))
   OR (pa.partner_type = 'CTY_TAI_CHINH'   AND m.product_code IN ('NG_NVV','XE_VCX_OTO','XE_VCX_MOTO','XE_TNDS_OTO','XE_TNDS_MOTO'))
   OR (pa.partner_type IN ('DAI_LY_XE_MAY','BUU_CHINH') AND m.product_code IN ('XE_TNDS_MOTO','XE_VCX_MOTO'))
   OR (pa.partner_type = 'DANG_KIEM'       AND m.product_code IN ('XE_TNDS_OTO'))
   OR (pa.partner_type IN ('SHOWROOM_OTO','GARAGE') AND m.product_code IN ('XE_TNDS_OTO','XE_VCX_OTO'))
   OR (pa.partner_type IN ('OTA_DU_LICH','CTY_LU_HANH','HANG_HANG_KHONG') AND m.product_code IN ('NG_DL_ND','NG_DL_QT'))
   OR (pa.partner_type IN ('VI_DIEN_TU','SAN_TMDT') AND m.product_code IN ('XE_TNDS_MOTO','XE_TNDS_OTO','XE_VCX_MOTO','XE_VCX_OTO','NG_DL_ND','NG_DL_QT','NG_TN24','NG_SK_CN','NG_SK_BHN','NG_HSSV_TN','NG_HSSV_SK','NG_SM_CN','TS_NHA'))
   OR (pa.partner_type = 'VIEN_THONG'      AND m.product_code IN ('NG_TN24','XE_TNDS_MOTO','NG_SM_CN'))
   OR (pa.partner_type = 'CTY_MOI_GIOI'    AND m.product_code IN ('NG_SK_NHOM','NG_SK_CN','TS_MRR','TS_MRRCN','CHN_BB','CHN_TN','XE_VCX_OTO'))
   OR (pa.partner_type = 'NEN_TANG_DI_CHUYEN' AND m.product_code IN ('MV_XSM_CARE','MV_FOOD_CARE'))
   OR (pa.partner_type = 'OTA_VE_MAY_BAY'  AND m.product_code IN ('MV_DELAYCARE'))
   OR (pa.partner_type = 'INSURTECH'       AND m.product_code IN ('MV_TBDT_TMDT'))
)
GROUP BY pa.partner_type, m.product_code;

-- P03 NULL đối tác theo nghiệp vụ: kênh trung gian (BANCA, MOI_GIOI, DAI_LY_TC) BẮT BUỘC có đối tác;
--     trực tiếp / đại lý cá nhân / đấu thầu / không rõ kênh KHÔNG có đối tác; điện tử: có (nền tảng đối tác) hoặc NULL (web/app công ty)
SELECT 'P03', 'Kênh ' || coalesce(channel_code, 'NULL') || CASE WHEN partner_code IS NULL THEN ' thiếu đối tác' ELSE ' không được có đối tác' END, count(*), min(policy_no)
FROM bronze.ins_policy
WHERE (channel_code IN ('BANCA','MOI_GIOI','DAI_LY_TC') AND partner_code IS NULL)
   OR ((channel_code IN ('TRUC_TIEP','DAI_LY_CN','DAU_THAU') OR channel_code IS NULL) AND partner_code IS NOT NULL)
GROUP BY channel_code, partner_code IS NULL;

-- I01 (thông tin, không tính vi phạm) kênh NULL = dữ liệu bẩn có chủ đích (~0,5%); lớp phân tích gán CHUA_XD
SELECT 'I01', 'Hợp đồng không khai báo kênh (dữ liệu bẩn có chủ đích) — ' || round(100.0 * count(*) FILTER (WHERE channel_code IS NULL) / count(*), 2) || '%',
       count(*) FILTER (WHERE channel_code IS NULL), min(policy_no) FILTER (WHERE channel_code IS NULL)
FROM bronze.ins_policy;

-- R01 cột tham chiếu BẮT BUỘC theo nghiệp vụ không được NULL
--     (được phép NULL: ins_policy.partner_code — xem P03; ins_policy.channel_code — xem I01)
SELECT 'R01', 'NULL ở cột tham chiếu bắt buộc: ' || col, n, NULL FROM (
  SELECT 'ins_policy.customer_code' col, count(*) FILTER (WHERE customer_code IS NULL) n FROM bronze.ins_policy UNION ALL
  SELECT 'ins_policy.issuing_company_code', count(*) FILTER (WHERE issuing_company_code IS NULL) FROM bronze.ins_policy UNION ALL
  SELECT 'ins_policy.currency_code', count(*) FILTER (WHERE currency_code IS NULL) FROM bronze.ins_policy UNION ALL
  SELECT 'ins_policy_transaction.txn_type_code', count(*) FILTER (WHERE txn_type_code IS NULL) FROM bronze.ins_policy_transaction UNION ALL
  SELECT 'ins_transaction_coverage.product_code', count(*) FILTER (WHERE product_code IS NULL) FROM bronze.ins_transaction_coverage UNION ALL
  SELECT 'ins_coinsurance_share.insurer_code', count(*) FILTER (WHERE insurer_code IS NULL) FROM bronze.ins_coinsurance_share UNION ALL
  SELECT 'ins_revenue_allocation.company_code', count(*) FILTER (WHERE company_code IS NULL) FROM bronze.ins_revenue_allocation UNION ALL
  SELECT 'ins_customer.province_code', count(*) FILTER (WHERE province_code IS NULL) FROM bronze.ins_customer
) x WHERE n > 0;

-- R02 mọi cột tham chiếu đều có khóa ngoại đã kiểm chứng (convalidated)
SELECT 'R02', 'Thiếu khóa ngoại / chưa kiểm chứng: ' || need, 1, NULL
FROM (VALUES ('ins_policy(channel_code)'), ('ins_policy(partner_code)'), ('ins_policy(customer_code)'), ('ins_policy(issuing_company_code)'),
             ('ins_policy(currency_code)'), ('ins_policy_transaction(policy_id)'), ('ins_policy_transaction(txn_type_code)'),
             ('ins_transaction_coverage(txn_id)'), ('ins_transaction_coverage(product_code)'), ('ins_coinsurance_share(policy_id)'),
             ('ins_coinsurance_share(insurer_code)'), ('ins_revenue_allocation(policy_id)'), ('ins_revenue_allocation(company_code)'),
             ('ins_revenue_allocation(allocation_type_code)'), ('ins_customer(segment_code)'), ('ins_customer(province_code)'),
             ('ins_customer(home_company_code)')) v(need)
WHERE NOT EXISTS (SELECT 1 FROM pg_constraint c
                  WHERE c.contype = 'f' AND c.convalidated
                    AND replace(c.conrelid::regclass::text, 'bronze.', '') || substring(pg_get_constraintdef(c.oid) FROM '\(\w+\)') = need);

-- P04 Bảo hiểm PVI Digital chỉ cấp đơn kênh điện tử
SELECT 'P04', 'DGT cấp đơn kênh ' || coalesce(channel_code, 'NULL'), count(*), min(policy_no)
FROM bronze.ins_policy WHERE issuing_company_code = 'DGT' AND channel_code IS DISTINCT FROM 'DIEN_TU'
GROUP BY channel_code;

-- P05 số hợp đồng: <năm>-<đơn vị>-<SP>-<seq>; đơn vị trong số HĐ phải = đơn vị cấp đơn
SELECT 'P05', 'Mã đơn vị trong policy_no ≠ issuing_company_code', count(*), min(policy_no)
FROM bronze.ins_policy WHERE policy_no NOT LIKE 'SIM-%' AND split_part(policy_no, '-', 2) <> issuing_company_code;

-- P06 mã sản phẩm trong số HĐ phải khớp sản phẩm chính
SELECT 'P06', 'Mã SP trong policy_no ≠ sản phẩm chính (' || split_part(p.policy_no, '-', 3) || ' vs ' || m.product_code || ')', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN _main m USING (policy_id)
WHERE split_part(p.policy_no, '-', 3) <> CASE m.product_code
      WHEN 'XE_TNDS_MOTO' THEN 'TXM' WHEN 'XE_TNDS_OTO' THEN 'TXO' WHEN 'XE_VCX_OTO' THEN 'VXO' WHEN 'XE_VCX_MOTO' THEN 'VXM'
      WHEN 'NG_HSSV_TN' THEN 'HTN' WHEN 'NG_HSSV_SK' THEN 'HSK' WHEN 'NG_DL_ND' THEN 'DLN' WHEN 'NG_DL_QT' THEN 'DLQ'
      WHEN 'NG_SM_CN' THEN 'SMC' WHEN 'NG_NVV' THEN 'NVV' WHEN 'NG_TN24' THEN 'T24' WHEN 'NG_SK_CN' THEN 'SKC'
      WHEN 'NG_SK_NHOM' THEN 'SKN' WHEN 'NG_SK_BHN' THEN 'BHN' WHEN 'TS_NHA' THEN 'TSN' WHEN 'TS_MRR' THEN 'MRR'
      WHEN 'TS_MRRCN' THEN 'MRC' WHEN 'CHN_BB' THEN 'CBB' WHEN 'CHN_TN' THEN 'CTN'
      WHEN 'MV_XSM_CARE' THEN 'XSC' WHEN 'MV_FOOD_CARE' THEN 'FDC' WHEN 'MV_DELAYCARE' THEN 'DLY' WHEN 'MV_TBDT_TMDT' THEN 'TBD' END
GROUP BY split_part(p.policy_no, '-', 3), m.product_code;

-- P07 ngày: hiệu lực ≥ ngày cấp, hết hạn ≥ hiệu lực
SELECT 'P07', 'Ngày hiệu lực/hết hạn sai thứ tự', count(*), min(policy_no)
FROM bronze.ins_policy WHERE effective_date < issue_date OR expiry_date < effective_date;

-- P08 thời hạn theo sản phẩm (du lịch ≤ 365 ngày theo dataset Travel Insurance; vi mô theo chuyến / đơn / chuyến bay = 1 ngày;
--     còn lại 1 năm, trừ học sinh/năm học, người vay vốn nhiều năm)
SELECT 'P08', 'Thời hạn không hợp lý cho ' || m.product_code || ' (' || min(p.expiry_date - p.effective_date + 1) || '–' || max(p.expiry_date - p.effective_date + 1) || ' ngày)', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN _main m USING (policy_id)
WHERE (m.product_code IN ('NG_DL_ND','NG_DL_QT') AND p.expiry_date - p.effective_date + 1 > 365)
   OR (m.product_code IN ('MV_XSM_CARE','MV_FOOD_CARE','MV_DELAYCARE') AND p.expiry_date <> p.effective_date)
   OR (m.product_code NOT IN ('NG_DL_ND','NG_DL_QT','NG_NVV','NG_HSSV_TN','NG_HSSV_SK','MV_XSM_CARE','MV_FOOD_CARE','MV_DELAYCARE')
       AND p.expiry_date - p.effective_date + 1 <> 365)
GROUP BY m.product_code;

-- P09 tiền tệ: USD chỉ cho du lịch quốc tế, mọi rủi ro tài sản / công nghiệp
SELECT 'P09', 'Đơn USD cho sản phẩm ' || m.product_code, count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN _main m USING (policy_id)
WHERE p.currency_code = 'USD' AND m.product_code NOT IN ('NG_DL_QT','TS_MRR','TS_MRRCN')
GROUP BY m.product_code;

-- P10 tái tục: prev_policy_no ⇔ giao dịch gốc RENEW; sản phẩm không tái tục (du lịch, người vay vốn) không có RENEW
SELECT 'P10', 'prev_policy_no không khớp loại giao dịch gốc (' || m.txn_type_code || ')', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN _main m USING (policy_id)
WHERE (p.prev_policy_no IS NOT NULL) <> (m.txn_type_code = 'RENEW') GROUP BY m.txn_type_code
UNION ALL
SELECT 'P10', 'RENEW cho sản phẩm không tái tục ' || product_code, count(*), min(policy_id::text)
FROM _main WHERE txn_type_code = 'RENEW' AND product_code IN ('NG_DL_ND','NG_DL_QT','NG_NVV') GROUP BY product_code;

-- P11 đơn nhóm/lô: is_group_policy ⇔ số người/xe > 1 (đơn lẻ du lịch/sức khỏe gia đình được phép 2–4 người)
SELECT 'P11', 'is_group_policy=' || p.is_group_policy || ' nhưng insured_count=' || CASE WHEN m.insured_count = 1 THEN '1' ELSE '>4' END || ' (' || m.product_code || ')', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN _main m USING (policy_id)
WHERE (p.is_group_policy AND m.insured_count = 1) OR (NOT p.is_group_policy AND m.insured_count > 4)
GROUP BY p.is_group_policy, m.insured_count = 1, m.product_code;

-- ---------------------------------------------------------------- KHÁCH HÀNG
-- C01 phân khúc khách × sản phẩm
SELECT 'C01', 'Phân khúc ' || cu.segment_code || ' mua ' || m.product_code, count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN bronze.ins_customer cu USING (customer_code) JOIN _main m USING (policy_id)
WHERE (cu.segment_code IN ('CA_NHAN','HO_GIA_DINH') AND m.product_code IN ('NG_SK_NHOM','TS_MRR','TS_MRRCN'))
   OR (cu.segment_code IN ('DN_TRONG_NUOC','DN_FDI','CO_QUAN_NN','CO_SO_GD') AND m.product_code IN ('NG_SK_CN','NG_SK_BHN','NG_SM_CN','NG_TN24','NG_NVV','TS_NHA','XE_VCX_MOTO'))
   OR (cu.segment_code = 'CO_SO_GD' AND m.product_code NOT IN ('NG_HSSV_TN','NG_HSSV_SK','CHN_BB','CHN_TN'))
   OR (cu.segment_code = 'HO_GIA_DINH' AND m.product_code NOT IN ('TS_NHA','CHN_BB','CHN_TN'))
   OR (m.product_code IN ('NG_HSSV_TN','NG_HSSV_SK') AND p.is_group_policy AND cu.segment_code <> 'CO_SO_GD')
GROUP BY cu.segment_code, m.product_code;

-- C02 thuộc tính khách theo loại: cá nhân có giới tính/năm sinh, không MST; tổ chức có MST, không giới tính
SELECT 'C02', 'Thuộc tính sai theo loại khách (' || segment_code || ')', count(*), min(customer_code)
FROM bronze.ins_customer
WHERE NOT is_aggregated_retail AND (
      (segment_code IN ('CA_NHAN','HO_GIA_DINH') AND (gender IS NULL OR birth_year IS NULL OR tax_code IS NOT NULL))
   OR (segment_code NOT IN ('CA_NHAN','HO_GIA_DINH') AND (tax_code IS NULL OR gender IS NOT NULL OR birth_year IS NOT NULL)))
GROUP BY segment_code;

-- C03 tuổi bên mua bảo hiểm ≥ 18 tại thời điểm cấp đơn
SELECT 'C03', 'Bên mua dưới 18 tuổi', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN bronze.ins_customer cu USING (customer_code)
WHERE cu.birth_year IS NOT NULL AND extract(year FROM p.issue_date) - cu.birth_year < 18;

-- C04 khách tạo sau lần mua đầu tiên
SELECT 'C04', 'created_date của khách > ngày cấp đơn đầu tiên', count(*), min(cu.customer_code)
FROM bronze.ins_customer cu JOIN (SELECT customer_code, min(issue_date) d FROM bronze.ins_policy GROUP BY 1) f USING (customer_code)
WHERE cu.created_date > f.d;

-- C05 khách lẻ theo bảng kê chỉ dùng cho đơn lô, và đơn lô phải dùng khách lẻ theo bảng kê
SELECT 'C05', 'Khách lẻ bảng kê ↔ đơn lô không khớp (aggregated=' || cu.is_aggregated_retail || ', group=' || p.is_group_policy || ', ' || m.product_code || ')', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN bronze.ins_customer cu USING (customer_code) JOIN _main m USING (policy_id)
WHERE cu.is_aggregated_retail AND NOT p.is_group_policy
GROUP BY cu.is_aggregated_retail, p.is_group_policy, m.product_code;

-- C06 khách lẻ bảng kê thuộc đúng đơn vị cấp đơn
SELECT 'C06', 'Khách lẻ bảng kê của đơn vị khác', count(*), min(p.policy_no)
FROM bronze.ins_policy p JOIN bronze.ins_customer cu USING (customer_code)
WHERE cu.is_aggregated_retail AND cu.home_company_code <> p.issuing_company_code;

-- C07 tỉnh của khách ↔ công ty quản lý khách (theo địa bàn)
SELECT 'C07', 'Công ty quản lý ' || cu.home_company_code || ' không phụ trách tỉnh ' || cu.province_code, count(*), min(cu.customer_code)
FROM bronze.ins_customer cu
JOIN bronze.ins_company co ON co.company_code = cu.home_company_code
WHERE NOT cu.is_aggregated_retail AND co.company_type = 'MEMBER'
  AND co.province_code <> cu.province_code
  AND NOT (cu.province_code, cu.home_company_code) IN (
      -- tỉnh không có đơn vị PVI đặt trụ sở → đơn vị gần nhất (gen_volume._NO_UNIT)
      ('TQG','TNU'),('LCI','VPU'),('LSN','TNU'),('CBG','TNU'),('DBN','HNO'),('LCU','VPU'),('SLA','HNO'))
GROUP BY cu.home_company_code, cu.province_code;

-- C08 tên khách theo phân khúc
SELECT 'C08', 'Tên không khớp phân khúc ' || segment_code, count(*), min(customer_name)
FROM bronze.ins_customer
WHERE NOT is_aggregated_retail AND (
      (segment_code = 'HO_GIA_DINH' AND customer_name NOT LIKE 'Hộ gia đình %')
   OR (segment_code IN ('DN_TRONG_NUOC','DN_FDI') AND customer_name NOT LIKE '%Công ty%' AND customer_name NOT LIKE 'Tổng công ty%')
   OR (segment_code = 'CO_SO_GD' AND customer_name NOT LIKE 'Trường%'))
GROUP BY segment_code;

-- ---------------------------------------------------------------- GIAO DỊCH
-- T01 số giao dịch bắt đầu bằng số hợp đồng; /00 = gốc, /01 = SĐBS
SELECT 'T01', 'txn_no không khớp policy_no / loại giao dịch', count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t JOIN bronze.ins_policy p USING (policy_id)
WHERE t.created_by <> 'SIM.SCHEMA_CHANGE' AND (
      t.txn_no NOT LIKE p.policy_no || '/%'
   OR (t.txn_type_code IN ('NEW','RENEW') AND t.txn_no NOT LIKE '%/00')
   OR (t.txn_type_code NOT IN ('NEW','RENEW') AND t.txn_no LIKE '%/00'));

-- T02 SĐBS sau ngày cấp, trước khi hết hạn
SELECT 'T02', 'SĐBS ngoài khoảng (ngày cấp, ngày hết hạn]', count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t JOIN bronze.ins_policy p USING (policy_id)
WHERE t.txn_type_code NOT IN ('NEW','RENEW') AND (t.txn_date <= p.issue_date OR t.txn_date > p.expiry_date);

-- T03 ngày ghi nhận = max(ngày chứng từ, ngày hiệu lực)
SELECT 'T03', 'accounting_date ≠ max(txn_date, effective_date)', count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t JOIN bronze.ins_policy p USING (policy_id)
WHERE t.accounting_date <> greatest(t.txn_date, p.effective_date);

-- T04 created_at cùng ngày chứng từ
SELECT 'T04', 'created_at khác ngày txn_date', count(*), min(txn_no)
FROM bronze.ins_policy_transaction WHERE created_at::date <> txn_date;

-- T05 người tạo: API.<đối tác> ⇔ kênh số có đối tác; WEB.APP ⇔ kênh số không đối tác; <đơn vị>.NVxx khớp đơn vị cấp đơn
SELECT 'T05', 'created_by không khớp kênh/đối tác/đơn vị', count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t JOIN bronze.ins_policy p USING (policy_id)
WHERE t.created_by <> 'SIM.SCHEMA_CHANGE' AND NOT (
      (p.channel_code = 'DIEN_TU' AND p.partner_code IS NOT NULL AND t.created_by = 'API.' || p.partner_code)
   OR (p.channel_code = 'DIEN_TU' AND p.partner_code IS NULL AND t.created_by = 'WEB.APP')
   OR (p.channel_code IS DISTINCT FROM 'DIEN_TU' AND t.created_by LIKE p.issuing_company_code || '.NV__'));

-- T06 SĐBS trên hợp đồng mà chứng từ gốc VOID (hợp đồng không tồn tại)
SELECT 'T06', 'SĐBS trên hợp đồng có chứng từ gốc ' || m.status, count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t JOIN _main m USING (policy_id)
WHERE t.txn_type_code NOT IN ('NEW','RENEW') AND m.status = 'VOID'
GROUP BY m.status;

-- T07 tỷ giá: VND = 1; USD = tỷ giá hạch toán tháng của accounting_date
SELECT 'T07', 'fx_rate sai (' || p.currency_code || ')', count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t JOIN bronze.ins_policy p USING (policy_id)
LEFT JOIN bronze.ins_fx_rate f ON f.currency_code = p.currency_code AND f.rate_month = date_trunc('month', t.accounting_date)::date
WHERE t.created_by <> 'SIM.SCHEMA_CHANGE'
  AND ((p.currency_code = 'VND' AND t.fx_rate <> 1) OR (p.currency_code = 'USD' AND t.fx_rate IS DISTINCT FROM f.rate_to_vnd))
GROUP BY p.currency_code;

-- ---------------------------------------------------------------- DÒNG PHÍ
-- V01 dấu phí theo loại giao dịch
SELECT 'V01', 'Dấu phí sai cho ' || t.txn_type_code, count(*), min(t.txn_no)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id) JOIN bronze.ins_transaction_type tt USING (txn_type_code)
WHERE sign(c.premium_vnd) <> tt.premium_sign AND NOT (c.premium_vnd = 0 AND tt.premium_sign <> 0)
GROUP BY t.txn_type_code;

-- V02 premium_vnd = round(premium_orig × fx_rate)
SELECT 'V02', 'premium_vnd ≠ premium_orig × fx_rate', count(*), min(t.txn_no)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id)
WHERE abs(c.premium_vnd - round(c.premium_orig * t.fx_rate)) > 1;

-- V03 VAT theo thuế suất sản phẩm
SELECT 'V03', 'vat_vnd ≠ premium_vnd × thuế suất (' || c.product_code || ')', count(*), min(c.coverage_id::text)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_product pr USING (product_code)
WHERE abs(c.vat_vnd - round(c.premium_vnd * pr.vat_rate / 100)) > 1
GROUP BY c.product_code;

-- V04 hoa hồng: ≤ trần; = 0 với trực tiếp / đấu thầu / web-app công ty; > 0 với kênh trung gian
SELECT 'V04', 'Hoa hồng sai theo kênh ' || coalesce(p.channel_code, 'NULL') || CASE WHEN c.commission_rate_pct > pr.max_commission_pct THEN ' (vượt trần)' WHEN c.commission_rate_pct = 0 THEN ' (= 0)' ELSE ' (> 0)' END, count(*), min(t.txn_no)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id) JOIN bronze.ins_policy p USING (policy_id)
JOIN bronze.ins_product pr USING (product_code)
WHERE c.commission_rate_pct > pr.max_commission_pct
   OR ((p.channel_code IN ('TRUC_TIEP','DAU_THAU') OR p.channel_code IS NULL OR (p.channel_code = 'DIEN_TU' AND p.partner_code IS NULL)) AND c.commission_rate_pct > 0)
   OR (p.channel_code IN ('DAI_LY_CN','DAI_LY_TC','BANCA','MOI_GIOI') AND c.commission_rate_pct = 0
       AND c.product_code NOT IN ('NG_DL_ND','NG_DL_QT'))      -- du lịch: 57% không hoa hồng theo dataset Travel Insurance
GROUP BY p.channel_code, c.commission_rate_pct > pr.max_commission_pct, c.commission_rate_pct = 0;

-- V05 tỷ lệ phí chỉ cho sản phẩm tính theo % STBH, và phí ≈ STBH × tỷ lệ (giao dịch gốc)
SELECT 'V05', 'premium_rate_pct sai cách tính phí (' || pr.pricing_basis || ', ' || c.product_code || ')', count(*), min(c.coverage_id::text)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id) JOIN bronze.ins_product pr USING (product_code)
WHERE t.txn_type_code IN ('NEW','RENEW') AND (
      (pr.pricing_basis = 'RATE_ON_SI' AND (c.premium_rate_pct IS NULL OR abs(c.premium_orig - c.sum_insured * c.premium_rate_pct / 100) > greatest(1, abs(c.premium_orig) * 0.01)))
   OR (pr.pricing_basis <> 'RATE_ON_SI' AND c.premium_rate_pct IS NOT NULL))
GROUP BY pr.pricing_basis, c.product_code;

-- V06 TNDS bắt buộc đúng biểu phí NĐ 67/2023 (phí / xe)
SELECT 'V06', 'Phí TNDS/xe ngoài biểu phí (' || c.product_code || ': ' || (c.premium_orig / c.insured_count)::bigint || ')', count(*), min(c.coverage_id::text)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id)
WHERE t.txn_type_code IN ('NEW','RENEW') AND c.insured_count > 0 AND (
      (c.product_code = 'XE_TNDS_MOTO' AND c.premium_orig / c.insured_count NOT IN (55000, 60000, 290000))
   OR (c.product_code = 'XE_TNDS_OTO'  AND c.premium_orig / c.insured_count NOT IN (437000,794000,1270000,1825000,756000,929000,1080000,853000,1660000,2746000,3200000)))
GROUP BY c.product_code, (c.premium_orig / c.insured_count)::bigint;

-- V07 dòng phí kèm theo hợp lệ (gói sản phẩm)
SELECT 'V07', 'Gói sản phẩm không hợp lệ: ' || m.product_code || ' + ' || c.product_code, count(*), min(t.txn_no)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id) JOIN _main m USING (policy_id)
WHERE c.product_code <> m.product_code AND NOT (m.product_code, c.product_code) IN (
      ('XE_VCX_OTO','XE_TNDS_OTO'),('XE_VCX_MOTO','XE_TNDS_MOTO'),('NG_SK_CN','NG_TN24'),('CHN_BB','TS_MRR'))
GROUP BY m.product_code, c.product_code;

-- V08 giao dịch gốc: STBH > 0, số người/xe ≥ 1, phí > 0
SELECT 'V08', 'Giao dịch gốc có STBH/số người/phí ≤ 0 (' || c.product_code || ')', count(*), min(c.coverage_id::text)
FROM bronze.ins_transaction_coverage c JOIN bronze.ins_policy_transaction t USING (txn_id)
WHERE t.txn_type_code IN ('NEW','RENEW') AND (c.sum_insured <= 0 OR c.insured_count < 1 OR c.premium_vnd <= 0)
GROUP BY c.product_code;

-- V09 mọi giao dịch có ít nhất 1 dòng phí
SELECT 'V09', 'Giao dịch không có dòng phí', count(*), min(t.txn_no)
FROM bronze.ins_policy_transaction t
WHERE NOT EXISTS (SELECT 1 FROM bronze.ins_transaction_coverage c WHERE c.txn_id = t.txn_id);

-- ---------------------------------------------------------------- ĐỒNG BH / PHÂN BỔ
-- A01 đồng BH: đúng 1 dòng OWN; nếu nhiều DN thì đúng 1 LEADER; SOLE chỉ khi 1 dòng 100%
SELECT 'A01', 'Cấu trúc đồng bảo hiểm sai', count(*), min(policy_id::text)
FROM (SELECT policy_id, count(*) n, count(*) FILTER (WHERE insurer_code = 'OWN') own,
             count(*) FILTER (WHERE role = 'LEADER') lead, count(*) FILTER (WHERE role = 'SOLE') sole
      FROM bronze.ins_coinsurance_share GROUP BY 1) x
WHERE own <> 1 OR (n = 1 AND sole <> 1) OR (n > 1 AND (lead <> 1 OR sole > 0));

-- A02 đồng BH chỉ cho rủi ro lớn (tài sản/cháy nổ, sức khỏe nhóm)
SELECT 'A02', 'Đồng BH cho sản phẩm ' || m.product_code, count(DISTINCT cs.policy_id), min(cs.policy_id::text)
FROM bronze.ins_coinsurance_share cs JOIN _main m USING (policy_id)
WHERE cs.role <> 'SOLE' AND m.product_code NOT IN ('TS_MRR','TS_MRRCN','CHN_BB','CHN_TN','NG_SK_NHOM')
GROUP BY m.product_code;

-- A03 phân bổ: TU_KHAI_THAC → đơn vị cấp đơn; CHUYEN_GIAO → không phải đơn vị cấp đơn; HO_TRO_CHEO gồm đơn vị cấp đơn
SELECT 'A03', 'Phân bổ sai loại ' || ra.allocation_type_code, count(*), min(p.policy_no)
FROM bronze.ins_revenue_allocation ra JOIN bronze.ins_policy p USING (policy_id)
WHERE (ra.allocation_type_code = 'TU_KHAI_THAC' AND ra.company_code <> p.issuing_company_code)
   OR (ra.allocation_type_code = 'CHUYEN_GIAO'  AND ra.company_code = p.issuing_company_code)
   OR (ra.allocation_type_code = 'HO_TRO_CHEO'  AND NOT EXISTS (SELECT 1 FROM bronze.ins_revenue_allocation r2
         WHERE r2.policy_id = ra.policy_id AND r2.company_code = p.issuing_company_code))
GROUP BY ra.allocation_type_code;

-- A04 chuyển giao của Trung tâm KD số phải về công ty quản lý khách
SELECT 'A04', 'DGT chuyển giao không về công ty quản lý khách', count(*), min(p.policy_no)
FROM bronze.ins_revenue_allocation ra JOIN bronze.ins_policy p USING (policy_id) JOIN bronze.ins_customer cu USING (customer_code)
WHERE p.issuing_company_code = 'DGT' AND ra.allocation_type_code = 'CHUYEN_GIAO' AND ra.company_code <> cu.home_company_code;
