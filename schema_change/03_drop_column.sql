-- =====================================================================
-- CASE 3 — XÓA CỘT (DROP COLUMN)
-- Bảng : bronze.ins_policy
-- Cột  : renewal_of_policy_id bigint (FK tự tham chiếu ins_policy) — cột lỗi thời,
--        luôn NULL, đã được thay bằng prev_policy_no (số hợp đồng năm trước, text).
-- Tình huống: hệ thống nguồn bỏ trường cũ khi chuyển sang trường mới.
-- Đặc điểm: DROP COLUMN chỉ đánh dấu cột bị xóa trong metadata (không ghi lại bảng),
--   khóa ngoại trên cột bị xóa theo. Downstream đọc cột này sẽ lỗi / nhận NULL.
--   Script thêm 1 hợp đồng tái tục mới để tạo sự kiện DML sau thay đổi.
-- Chạy lại nhiều lần được (IF EXISTS). Hoàn tác: 99_rollback.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. DDL
ALTER TABLE bronze.ins_policy DROP COLUMN IF EXISTS renewal_of_policy_id;

-- 2. Phát sinh dữ liệu mới SAU thay đổi: 1 hợp đồng tái tục đầy đủ
--    (hợp đồng + giao dịch RENEW + dòng phí + đồng BH + phân bổ), dùng prev_policy_no
DO $$
DECLARE
    src  bronze.ins_policy%ROWTYPE;
    pid  bigint;
    tid  bigint;
    cid  bigint;
BEGIN
    IF EXISTS (SELECT 1 FROM bronze.ins_policy WHERE policy_no LIKE 'SIM-%') THEN
        RETURN;   -- đã chạy trước đó
    END IF;
    -- hợp đồng gốc: VCX ô tô bán lẻ, kênh đại lý cá nhân
    SELECT p.* INTO src
    FROM bronze.ins_policy p
    JOIN bronze.ins_policy_transaction t ON t.policy_id = p.policy_id AND t.txn_type_code = 'NEW'
    JOIN bronze.ins_transaction_coverage c ON c.txn_id = t.txn_id AND c.product_code = 'XE_VCX_OTO'
    WHERE p.channel_code = 'DAI_LY_CN' AND NOT p.is_group_policy
    ORDER BY p.policy_id
    LIMIT 1;

    SELECT max(policy_id) + 1 INTO pid FROM bronze.ins_policy;
    SELECT max(txn_id) + 1 INTO tid FROM bronze.ins_policy_transaction;
    SELECT max(coverage_id) + 1 INTO cid FROM bronze.ins_transaction_coverage;

    INSERT INTO bronze.ins_policy
           (policy_id, policy_no, issuing_company_code, customer_code, channel_code, partner_code,
            currency_code, issue_date, effective_date, expiry_date, is_group_policy, prev_policy_no)
    VALUES (pid, 'SIM-' || src.policy_no, src.issuing_company_code, src.customer_code, src.channel_code,
            src.partner_code, src.currency_code, current_date, current_date + 1, current_date + 365,
            false, src.policy_no);

    INSERT INTO bronze.ins_policy_transaction
           (txn_id, policy_id, txn_no, txn_type_code, txn_date, accounting_date, status, fx_rate,
            created_by, created_at)
    VALUES (tid, pid, 'SIM-' || src.policy_no || '/00', 'RENEW', current_date, current_date + 1,
            'APPROVED', 1, 'SIM.SCHEMA_CHANGE', now()::timestamp(0));

    -- phí tái tục = phí năm trước × 1,05
    INSERT INTO bronze.ins_transaction_coverage
           (coverage_id, txn_id, product_code, sum_insured, premium_rate_pct, insured_count,
            premium_orig, premium_vnd, vat_vnd, commission_rate_pct)
    SELECT cid + row_number() OVER (ORDER BY c.coverage_id) - 1, tid, c.product_code, c.sum_insured,
           c.premium_rate_pct, c.insured_count, round(c.premium_orig * 1.05), round(c.premium_vnd * 1.05),
           round(c.vat_vnd * 1.05), c.commission_rate_pct
    FROM bronze.ins_transaction_coverage c
    JOIN bronze.ins_policy_transaction t ON t.txn_id = c.txn_id
    WHERE t.policy_id = src.policy_id AND t.txn_type_code IN ('NEW', 'RENEW');

    INSERT INTO bronze.ins_coinsurance_share (policy_id, insurer_code, role, share_pct)
    SELECT pid, insurer_code, role, share_pct FROM bronze.ins_coinsurance_share WHERE policy_id = src.policy_id;

    INSERT INTO bronze.ins_revenue_allocation (policy_id, company_code, allocation_type_code, allocation_pct)
    SELECT pid, company_code, allocation_type_code, allocation_pct FROM bronze.ins_revenue_allocation
    WHERE policy_id = src.policy_id;
END $$;

COMMIT;

-- Kiểm tra
SELECT policy_id, policy_no, prev_policy_no, issue_date, effective_date
FROM bronze.ins_policy WHERE policy_no LIKE 'SIM-%';
