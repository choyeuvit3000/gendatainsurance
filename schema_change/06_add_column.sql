-- =====================================================================
-- CASE 06 — THÊM CỘT (ADD COLUMN)
-- Bảng : bronze.ins_customer   (~1,97 triệu dòng, sink iceberg-sink-pvi-ins-customer)
-- Cột  : kyc_status varchar(12) NULL — trạng thái xác minh danh tính khách hàng
--        VERIFIED / PENDING / REJECTED
-- Tình huống: hệ thống nguồn bắt đầu lưu trạng thái KYC.
--   - Dữ liệu cũ: NULL, chỉ backfill 1.000 khách gần nhất
--   - Khách mới tạo sau thay đổi: có giá trị
-- Đặc điểm PostgreSQL: ADD COLUMN nullable, không default → chỉ đổi metadata, không ghi lại bảng.
-- Kỳ vọng ở landing: sink tự THÊM cột kyc_status (evolve-schema). Event cũ = NULL.
-- Yêu cầu: đã chạy 05_registry_setup.sql. Chạy lại được. Hoàn tác: 98_rollback_add_rename_drop.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. DDL
ALTER TABLE bronze.ins_customer ADD COLUMN IF NOT EXISTS kyc_status varchar(12);
COMMENT ON COLUMN bronze.ins_customer.kyc_status IS
    'Trạng thái KYC: VERIFIED / PENDING / REJECTED (thêm ở CASE 06 mô phỏng schema change)';

-- 2. Ghi sổ thay đổi (kỳ vọng: 1 dòng ADD kyc_status)
SELECT change_type, table_name, old_column_name, new_column_name, new_data_type
FROM bronze.ins_capture_schema_changes('06_add_column: thêm kyc_status');

-- 3. Backfill 1.000 khách gần nhất (sinh event UPDATE có field mới)
UPDATE bronze.ins_customer
SET kyc_status = CASE WHEN tax_code IS NOT NULL THEN 'VERIFIED'          -- tổ chức có MST
                      WHEN right(customer_code, 1) IN ('0', '1') THEN 'PENDING'
                      ELSE 'VERIFIED' END
WHERE customer_code IN (SELECT customer_code FROM bronze.ins_customer
                        WHERE customer_code LIKE 'KH%' ORDER BY customer_code DESC LIMIT 1000)
  AND kyc_status IS NULL;

-- 4. Khách mới tạo SAU thay đổi: 3 khách, sao các cột gốc từ khách có sẵn (sinh event INSERT)
INSERT INTO bronze.ins_customer
       (customer_code, customer_name, segment_code, tax_code, province_code, home_company_code,
        is_aggregated_retail, created_date, kyc_status)
SELECT 'SIM-C06-' || lpad(rn::text, 3, '0'), 'Khách mô phỏng CASE 06 #' || rn,
       segment_code, tax_code, province_code, home_company_code, is_aggregated_retail, current_date,
       (ARRAY['VERIFIED', 'PENDING', 'REJECTED'])[rn]
FROM (SELECT c.*, row_number() OVER (ORDER BY customer_code) AS rn
      FROM bronze.ins_customer c
      WHERE customer_code LIKE 'KH%' AND NOT is_aggregated_retail
      ORDER BY customer_code LIMIT 3) s
ON CONFLICT (customer_code) DO NOTHING;

COMMIT;

-- Kiểm tra
SELECT kyc_status, count(*) FROM bronze.ins_customer
WHERE kyc_status IS NOT NULL GROUP BY 1 ORDER BY 2 DESC;
