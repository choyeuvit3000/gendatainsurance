-- =====================================================================
-- CASE 1 — THÊM CỘT (ADD COLUMN)
-- Bảng : bronze.ins_policy_transaction
-- Cột  : payment_method varchar(20) NULL
-- Tình huống: hệ thống nguồn bắt đầu ghi nhận phương thức thanh toán phí.
--   - Dữ liệu cũ: NULL (chỉ backfill 2.000 giao dịch gần nhất)
--   - Dữ liệu mới sau thay đổi: có giá trị
-- Đặc điểm: ADD COLUMN nullable, không default → chỉ đổi metadata, không ghi lại bảng.
-- Chạy lại nhiều lần được (IF NOT EXISTS). Hoàn tác: 99_rollback.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. DDL
ALTER TABLE bronze.ins_policy_transaction ADD COLUMN IF NOT EXISTS payment_method varchar(20);
COMMENT ON COLUMN bronze.ins_policy_transaction.payment_method IS
    'Phương thức thanh toán phí: CASH / BANK_TRANSFER / E_WALLET / CARD (thêm từ CASE 1 mô phỏng schema change)';

-- 2. Backfill một phần dữ liệu cũ (2.000 giao dịch gần nhất) theo kênh bán
UPDATE bronze.ins_policy_transaction t
SET payment_method = CASE p.channel_code
                         WHEN 'DIEN_TU' THEN 'E_WALLET'
                         WHEN 'BANCA'   THEN 'BANK_TRANSFER'
                         WHEN 'TRUC_TIEP' THEN 'BANK_TRANSFER'
                         WHEN 'MOI_GIOI'  THEN 'BANK_TRANSFER'
                         ELSE 'CASH' END
FROM bronze.ins_policy p
WHERE p.policy_id = t.policy_id
  AND t.payment_method IS NULL
  AND t.txn_id IN (SELECT txn_id FROM bronze.ins_policy_transaction
                   WHERE created_by <> 'SIM.SCHEMA_CHANGE' ORDER BY txn_id DESC LIMIT 2000);

-- 3. Phát sinh giao dịch mới SAU thay đổi: 5 SĐBS không đổi phí (đổi thông tin) có payment_method
WITH base AS (SELECT max(txn_id) AS m FROM bronze.ins_policy_transaction),
pick AS (
    SELECT p.policy_id, p.policy_no, p.effective_date,
           row_number() OVER (ORDER BY p.policy_id DESC) AS rn
    FROM bronze.ins_policy p
    WHERE p.channel_code = 'DIEN_TU' AND p.currency_code = 'VND'
    ORDER BY p.policy_id DESC
    LIMIT 5
)
INSERT INTO bronze.ins_policy_transaction
       (txn_id, policy_id, txn_no, txn_type_code, txn_date, accounting_date, status, fx_rate,
        created_by, created_at, payment_method)
SELECT base.m + pick.rn, pick.policy_id, pick.policy_no || '/S1', 'END_NOCHG',
       current_date, greatest(current_date, pick.effective_date), 'APPROVED', 1,
       'SIM.SCHEMA_CHANGE', now()::timestamp(0), (ARRAY['E_WALLET', 'CARD'])[1 + (pick.rn % 2)::int]
FROM pick, base;

-- dòng phí 0 đồng cho các giao dịch vừa thêm (mỗi giao dịch luôn có ≥ 1 dòng phí)
WITH base AS (SELECT max(coverage_id) AS m FROM bronze.ins_transaction_coverage),
new_txn AS (
    SELECT t.txn_id, row_number() OVER (ORDER BY t.txn_id) AS rn,
           (SELECT c.product_code FROM bronze.ins_policy_transaction t0
              JOIN bronze.ins_transaction_coverage c ON c.txn_id = t0.txn_id
             WHERE t0.policy_id = t.policy_id ORDER BY c.coverage_id LIMIT 1) AS product_code
    FROM bronze.ins_policy_transaction t
    WHERE t.created_by = 'SIM.SCHEMA_CHANGE'
      AND NOT EXISTS (SELECT 1 FROM bronze.ins_transaction_coverage c WHERE c.txn_id = t.txn_id)
)
INSERT INTO bronze.ins_transaction_coverage
       (coverage_id, txn_id, product_code, sum_insured, premium_rate_pct, insured_count,
        premium_orig, premium_vnd, vat_vnd, commission_rate_pct)
SELECT base.m + n.rn, n.txn_id, n.product_code, 0, NULL, 0, 0, 0, 0, 0
FROM new_txn n, base;

COMMIT;

-- Kiểm tra
SELECT payment_method, count(*) FROM bronze.ins_policy_transaction
WHERE payment_method IS NOT NULL GROUP BY 1 ORDER BY 2 DESC;
