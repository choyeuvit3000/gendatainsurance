-- =====================================================================
-- HOÀN TÁC cả 3 case — đưa schema + dữ liệu về như ban đầu
--   1. Xóa dữ liệu do script mô phỏng tạo ra (created_by = 'SIM.SCHEMA_CHANGE', policy_no 'SIM-%')
--   2. CASE 3: thêm lại renewal_of_policy_id + khóa ngoại
--   3. CASE 2: fx_rate numeric(18,6) → numeric(18,2)  (ghi lại bảng lần nữa)
--   4. CASE 1: xóa cột payment_method
-- Chạy lại nhiều lần được.
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. Dữ liệu mô phỏng
DELETE FROM bronze.ins_transaction_coverage c
USING bronze.ins_policy_transaction t
WHERE c.txn_id = t.txn_id AND t.created_by = 'SIM.SCHEMA_CHANGE';
DELETE FROM bronze.ins_coinsurance_share  WHERE policy_id IN (SELECT policy_id FROM bronze.ins_policy WHERE policy_no LIKE 'SIM-%');
DELETE FROM bronze.ins_revenue_allocation WHERE policy_id IN (SELECT policy_id FROM bronze.ins_policy WHERE policy_no LIKE 'SIM-%');
DELETE FROM bronze.ins_policy_transaction WHERE created_by = 'SIM.SCHEMA_CHANGE';
DELETE FROM bronze.ins_policy WHERE policy_no LIKE 'SIM-%';

-- 2. CASE 3
ALTER TABLE bronze.ins_policy ADD COLUMN IF NOT EXISTS renewal_of_policy_id bigint;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conrelid = 'bronze.ins_policy'::regclass AND contype = 'f'
                     AND conname = 'ins_policy_renewal_of_policy_id_fkey') THEN
        ALTER TABLE bronze.ins_policy ADD CONSTRAINT ins_policy_renewal_of_policy_id_fkey
            FOREIGN KEY (renewal_of_policy_id) REFERENCES bronze.ins_policy(policy_id);
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_policy.renewal_of_policy_id IS 'Hợp đồng được tái tục (NULL = cấp mới)';

-- 3. CASE 2
DO $$
BEGIN
    IF (SELECT numeric_scale FROM information_schema.columns
        WHERE table_schema = 'bronze' AND table_name = 'ins_policy_transaction'
          AND column_name = 'fx_rate') <> 2 THEN
        ALTER TABLE bronze.ins_policy_transaction ALTER COLUMN fx_rate TYPE numeric(18,2);
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_policy_transaction.fx_rate IS 'Tỷ giá hạch toán (VND = 1)';

-- 4. CASE 1
ALTER TABLE bronze.ins_policy_transaction DROP COLUMN IF EXISTS payment_method;

-- 5. CASE 4: sort_order varchar → int, trả lại giá trị gốc 1..7
DO $$
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_schema = 'bronze' AND table_name = 'ins_channel' AND column_name = 'sort_order') <> 'integer' THEN
        UPDATE bronze.ins_channel SET sort_order = '1' WHERE channel_code = 'TRUC_TIEP';
        UPDATE bronze.ins_channel SET sort_order = '7' WHERE channel_code = 'DIEN_TU';
        ALTER TABLE bronze.ins_channel ALTER COLUMN sort_order TYPE int USING sort_order::int;
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_channel.sort_order IS NULL;

COMMIT;
