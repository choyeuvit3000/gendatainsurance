-- =====================================================================
-- CASE 07 — ĐỔI TÊN CỘT (RENAME COLUMN)
-- Bảng : bronze.ins_customer
-- Cột  : birth_year smallint  →  year_of_birth smallint   (kiểu giữ nguyên)
-- Tình huống: nguồn chuẩn hóa tên trường theo từ điển dữ liệu mới.
-- Đặc điểm PostgreSQL: RENAME chỉ đổi metadata, giữ nguyên attnum và dữ liệu.
--   View dùng cột này (nếu có) vẫn chạy: view lưu theo attnum, không theo tên.
-- Kỳ vọng ở landing (đã kiểm chứng trên mã sink 0.6.19):
--   - Sink so cột theo TÊN, không có thao tác rename → THÊM cột year_of_birth.
--   - Cột birth_year GIỮ NGUYÊN: event trước thay đổi có giá trị ở birth_year,
--     event sau thay đổi có giá trị ở year_of_birth, birth_year = NULL.
--   → Silver hợp nhất: COALESCE(year_of_birth, birth_year) theo TỪNG event (xem 10_silver_dremio.sql).
-- Lưu ý: dòng cũ KHÔNG được phát lại. Khách không bị sửa sau thay đổi sẽ chỉ có giá trị ở birth_year.
-- Yêu cầu: đã chạy 05. Chạy lại được. Hoàn tác: 98_rollback_add_rename_drop.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. DDL (bỏ qua nếu đã đổi)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'bronze' AND table_name = 'ins_customer' AND column_name = 'birth_year')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'bronze' AND table_name = 'ins_customer' AND column_name = 'year_of_birth') THEN
        ALTER TABLE bronze.ins_customer RENAME COLUMN birth_year TO year_of_birth;
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_customer.year_of_birth IS
    'Năm sinh — chỉ khách cá nhân, hộ gia đình (đổi tên từ birth_year ở CASE 07 mô phỏng schema change)';

-- 2. Ghi sổ thay đổi (kỳ vọng: 1 dòng RENAME birth_year → year_of_birth, cùng attnum)
SELECT change_type, table_name, attnum, old_column_name, new_column_name
FROM bronze.ins_capture_schema_changes('07_rename_column: birth_year → year_of_birth');

-- 3. Nguồn sửa 500 khách cá nhân sau thay đổi (giá trị giữ nguyên, chỉ để sinh event UPDATE
--    mang tên cột mới — giống nguồn cập nhật hồ sơ khách)
UPDATE bronze.ins_customer
SET year_of_birth = year_of_birth
WHERE customer_code IN (SELECT customer_code FROM bronze.ins_customer
                        WHERE customer_code LIKE 'KH%' AND year_of_birth IS NOT NULL
                        ORDER BY customer_code LIMIT 500);

-- 4. Khách cá nhân mới SAU thay đổi: 2 khách, có year_of_birth
INSERT INTO bronze.ins_customer
       (customer_code, customer_name, segment_code, tax_code, province_code, home_company_code,
        is_aggregated_retail, created_date, year_of_birth)
SELECT 'SIM-C07-' || lpad(rn::text, 3, '0'), 'Khách mô phỏng CASE 07 #' || rn,
       segment_code, tax_code, province_code, home_company_code, is_aggregated_retail, current_date,
       (1985 + rn)::smallint
FROM (SELECT c.*, row_number() OVER (ORDER BY customer_code) AS rn
      FROM bronze.ins_customer c
      WHERE customer_code LIKE 'KH%' AND year_of_birth IS NOT NULL AND NOT is_aggregated_retail
      ORDER BY customer_code LIMIT 2) s
ON CONFLICT (customer_code) DO NOTHING;

COMMIT;

-- Kiểm tra: tên cột mới, giá trị còn nguyên
SELECT customer_code, year_of_birth
FROM bronze.ins_customer
WHERE customer_code LIKE 'SIM-C07-%'
   OR customer_code IN (SELECT customer_code FROM bronze.ins_customer
                        WHERE customer_code LIKE 'KH%' AND year_of_birth IS NOT NULL
                        ORDER BY customer_code LIMIT 3)
ORDER BY customer_code;
