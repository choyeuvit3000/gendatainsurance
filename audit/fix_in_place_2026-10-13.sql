-- =====================================================================
-- SỬA TẠI CHỖ dữ liệu bronze.ins_* theo kết quả rà soát 13/10/2026
-- (bộ sinh gen_volume.py đã sửa tương ứng — lần nạp sau không cần script này)
--   F1  danh mục bổ sung: đối tác đại lý xe máy / bưu cục
--   (F2, F3 đã bỏ: NULL ở channel_code / partner_code là hợp lệ theo nghiệp vụ nguồn — xem audit P03, I01;
--    lớp phân tích bronze.v_ins_revenue_line gán thành viên "không qua đối tác" / "chưa xác định")
--   F4  TNDS xe máy bán qua garage / showroom ô tô → đại lý xe máy, bưu cục (P02)
--   F5  SĐBS trên hợp đồng có chứng từ gốc VOID / PENDING → xóa          (T06)
--   F6  tỷ lệ phí = phí thực thu / STBH                                  (V05)
--   F7  làm mới materialized view
-- Mỗi bước 1 transaction; chỉ cập nhật dòng sai → ít event CDC nhất. Chạy lại được.
-- =====================================================================

-- F1 ------------------------------------------------------------------
BEGIN;
INSERT INTO bronze.ins_partner (partner_code, partner_name, partner_type, channel_code) VALUES
    ('XM_A', 'Đại lý xe máy ủy quyền A', 'DAI_LY_XE_MAY', 'DAI_LY_TC'),
    ('XM_B', 'Đại lý xe máy ủy quyền B', 'DAI_LY_XE_MAY', 'DAI_LY_TC'),
    ('XM_C', 'Đại lý xe máy ủy quyền C', 'DAI_LY_XE_MAY', 'DAI_LY_TC'),
    ('BC_A', 'Mạng lưới bưu cục A', 'BUU_CHINH', 'DAI_LY_TC')
ON CONFLICT (partner_code) DO NOTHING;
COMMIT;

-- F4 ------------------------------------------------------------------
-- phân bổ lệch như bộ sinh (đối tác lớn chiếm phần lớn): XM_A 45% · XM_B 24% · XM_C 17% · BC_A 14%
BEGIN;
UPDATE bronze.ins_policy
SET partner_code = CASE WHEN policy_id % 100 < 45 THEN 'XM_A' WHEN policy_id % 100 < 69 THEN 'XM_B'
                        WHEN policy_id % 100 < 86 THEN 'XM_C' ELSE 'BC_A' END
WHERE split_part(policy_no, '-', 3) = 'TXM'
  AND partner_code IN ('GA_A', 'GA_B', 'SR_A', 'SR_B', 'SR_C', 'SR_D');
COMMIT;

-- F5 ------------------------------------------------------------------
BEGIN;
CREATE TEMP TABLE _bad_endo ON COMMIT DROP AS
SELECT e.txn_id
FROM bronze.ins_policy_transaction e
JOIN bronze.ins_policy_transaction b ON b.policy_id = e.policy_id AND b.txn_type_code IN ('NEW', 'RENEW')
WHERE e.txn_type_code NOT IN ('NEW', 'RENEW') AND b.status IN ('VOID', 'PENDING');
DELETE FROM bronze.ins_transaction_coverage WHERE txn_id IN (SELECT txn_id FROM _bad_endo);
DELETE FROM bronze.ins_policy_transaction  WHERE txn_id IN (SELECT txn_id FROM _bad_endo);
COMMIT;

-- F6 ------------------------------------------------------------------
-- giao dịch gốc: tỷ lệ = phí / STBH
BEGIN;
UPDATE bronze.ins_transaction_coverage c
SET premium_rate_pct = round(c.premium_orig / c.sum_insured * 100, 6)
FROM bronze.ins_policy_transaction t
WHERE t.txn_id = c.txn_id AND t.txn_type_code IN ('NEW', 'RENEW')
  AND c.premium_rate_pct IS NOT NULL AND c.sum_insured > 0
  AND c.premium_rate_pct <> round(c.premium_orig / c.sum_insured * 100, 6);
-- SĐBS: giữ tỷ lệ của dòng gốc cùng sản phẩm
UPDATE bronze.ins_transaction_coverage c
SET premium_rate_pct = b.premium_rate_pct
FROM bronze.ins_policy_transaction t,
     bronze.ins_policy_transaction bt,
     bronze.ins_transaction_coverage b
WHERE t.txn_id = c.txn_id AND t.txn_type_code NOT IN ('NEW', 'RENEW')
  AND bt.policy_id = t.policy_id AND bt.txn_type_code IN ('NEW', 'RENEW')
  AND b.txn_id = bt.txn_id AND b.product_code = c.product_code
  AND c.premium_rate_pct IS NOT NULL AND c.premium_rate_pct <> b.premium_rate_pct;
COMMIT;

-- F7 ------------------------------------------------------------------
REFRESH MATERIALIZED VIEW bronze.mv_ins_revenue_daily;
REFRESH MATERIALIZED VIEW bronze.mv_ins_txn_hourly;
ANALYZE bronze.ins_policy;
ANALYZE bronze.ins_policy_transaction;
ANALYZE bronze.ins_transaction_coverage;
