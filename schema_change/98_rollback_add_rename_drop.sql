-- =====================================================================
-- HOÀN TÁC CASE 06–08 — đưa bronze.ins_customer về schema ban đầu
--   1. Xóa khách mô phỏng (customer_code 'SIM-C0%')
--   2. CASE 08: thêm lại gender char(1) (cột mới nằm CUỐI bảng, attnum mới)
--   3. CASE 07: year_of_birth → birth_year
--   4. CASE 06: xóa kyc_status
--   5. Ghi sổ các thay đổi ngược (ADD gender, RENAME year_of_birth → birth_year, DROP kyc_status)
-- Phần TÙY CHỌN ở cuối: trả lại giá trị gender từ bảng sao lưu (~1,9 triệu UPDATE → ~1,9 triệu event CDC).
-- Landing KHÔNG quay về: kyc_status, year_of_birth vẫn còn ở Iceberg (sink không xóa cột).
-- Chạy lại được. NÊN chạy file này trước khi dùng gen_volume.py --replace
--   (--replace COPY vào ins_customer theo danh sách cột cố định gồm gender, birth_year).
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. Dữ liệu mô phỏng
DELETE FROM bronze.ins_customer WHERE customer_code LIKE 'SIM-C0%';

-- 2. CASE 08
ALTER TABLE bronze.ins_customer ADD COLUMN IF NOT EXISTS gender char(1);
COMMENT ON COLUMN bronze.ins_customer.gender IS 'Giới tính (M/F) — chỉ khách cá nhân, hộ gia đình';

-- 3. CASE 07
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'bronze' AND table_name = 'ins_customer' AND column_name = 'year_of_birth') THEN
        ALTER TABLE bronze.ins_customer RENAME COLUMN year_of_birth TO birth_year;
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_customer.birth_year IS 'Năm sinh — chỉ khách cá nhân, hộ gia đình';

-- 4. CASE 06
ALTER TABLE bronze.ins_customer DROP COLUMN IF EXISTS kyc_status;

-- 5. Ghi sổ (bỏ qua nếu chưa chạy 05)
DO $$
BEGIN
    IF to_regproc('bronze.ins_capture_schema_changes') IS NOT NULL THEN
        PERFORM bronze.ins_capture_schema_changes('98_rollback_add_rename_drop');
    END IF;
END $$;

COMMIT;

SELECT a.attnum, a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
FROM pg_attribute a
WHERE a.attrelid = 'bronze.ins_customer'::regclass AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum;

-- ---------------------------------------------------------------------
-- TÙY CHỌN A — trả lại giá trị gender (bỏ comment để chạy). Sinh ~1,9 triệu event CDC
--   vào pvi_landing.ins_customer. Chạy riêng, ngoài giờ test.
-- ---------------------------------------------------------------------
-- UPDATE bronze.ins_customer c SET gender = b.gender
-- FROM bronze.ins_bak_customer_gender b
-- WHERE b.customer_code = c.customer_code AND c.gender IS DISTINCT FROM b.gender;
-- DROP TABLE IF EXISTS bronze.ins_bak_customer_gender;

-- ---------------------------------------------------------------------
-- TÙY CHỌN B — gỡ hẳn sổ thay đổi schema + event trigger (05, 05b)
-- ---------------------------------------------------------------------
-- DROP EVENT TRIGGER IF EXISTS trg_ins_schema_change;
-- DROP FUNCTION IF EXISTS bronze.ins_schema_change_evt();
-- DROP FUNCTION IF EXISTS bronze.ins_capture_schema_changes(text);
-- DROP FUNCTION IF EXISTS bronze.ins_schema_current();
-- DROP TABLE IF EXISTS bronze.ins_schema_change_log, bronze.ins_schema_snapshot;
