-- =====================================================================
-- CASE 2 — ĐỔI KIỂU DỮ LIỆU (ALTER COLUMN TYPE)
-- Bảng : bronze.ins_policy_transaction
-- Cột  : fx_rate  numeric(18,2)  →  numeric(18,6)
-- Tình huống: tỷ giá hạch toán cần 6 chữ số thập phân (ví dụ 26187.123456),
--   kiểu cũ chỉ giữ 2 số lẻ.
-- Đặc điểm: tăng scale của numeric → PostgreSQL GHI LẠI TOÀN BỘ BẢNG (~4,2 triệu dòng,
--   khóa ACCESS EXCLUSIVE khoảng 1–2 phút, sinh WAL cỡ kích thước bảng).
--   CDC (Debezium) không phát sự kiện cho việc ghi lại bảng; schema mới chỉ thấy
--   ở sự kiện DML đầu tiên sau đó → script thêm 3 giao dịch USD để tạo sự kiện.
-- Chạy lại nhiều lần được. Hoàn tác: 99_rollback.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. DDL (bỏ qua nếu đã đúng kiểu)
DO $$
BEGIN
    IF (SELECT numeric_scale FROM information_schema.columns
        WHERE table_schema = 'bronze' AND table_name = 'ins_policy_transaction'
          AND column_name = 'fx_rate') <> 6 THEN
        ALTER TABLE bronze.ins_policy_transaction ALTER COLUMN fx_rate TYPE numeric(18,6);
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_policy_transaction.fx_rate IS
    'Tỷ giá hạch toán (VND = 1). Đổi numeric(18,2) → numeric(18,6) ở CASE 2 mô phỏng schema change';

-- 2. Phát sinh giao dịch mới SAU thay đổi: 3 SĐBS không đổi phí trên đơn USD, tỷ giá 6 số lẻ
WITH base AS (SELECT max(txn_id) AS m FROM bronze.ins_policy_transaction),
pick AS (
    SELECT p.policy_id, p.policy_no, p.effective_date,
           row_number() OVER (ORDER BY p.policy_id DESC) AS rn
    FROM bronze.ins_policy p
    WHERE p.currency_code = 'USD'
    ORDER BY p.policy_id DESC
    LIMIT 3
)
INSERT INTO bronze.ins_policy_transaction
       (txn_id, policy_id, txn_no, txn_type_code, txn_date, accounting_date, status, fx_rate,
        created_by, created_at)
SELECT base.m + pick.rn, pick.policy_id, pick.policy_no || '/S2', 'END_NOCHG',
       current_date, greatest(current_date, pick.effective_date), 'APPROVED',
       26187.123456 + pick.rn / 1000000.0,
       'SIM.SCHEMA_CHANGE', now()::timestamp(0)
FROM pick, base;

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
SELECT txn_no, currency_code, fx_rate
FROM bronze.ins_policy_transaction t JOIN bronze.ins_policy p USING (policy_id)
WHERE t.created_by = 'SIM.SCHEMA_CHANGE' AND t.txn_no LIKE '%/S2';
