-- =====================================================================
-- CASE 08 — XÓA CỘT (DROP COLUMN)
-- Bảng : bronze.ins_customer
-- Cột  : gender char(1) — nguồn ngừng lưu giới tính khách hàng (mô phỏng)
-- Đặc điểm PostgreSQL: DROP COLUMN chỉ đánh dấu attisdropped trong metadata, không ghi lại bảng.
--   Cột không nằm trong view nào (v_ins_revenue_line / mv_ins_* không dùng) nên không cần CASCADE.
-- Kỳ vọng ở landing (đã kiểm chứng trên mã sink 0.6.19):
--   - Sink KHÔNG xóa cột: gender vẫn còn, event sau thay đổi có gender = NULL.
--   - Nếu cột ở landing là required thì sink chỉ đổi sang optional.
--   → Landing không tự biết "đã xóa". Silver đọc ins_schema_change_log (DROP gender)
--     để bỏ cột khỏi danh sách select (xem 10_silver_dremio.sql).
-- Sao lưu: trước khi xóa, chép (customer_code, gender) sang bronze.ins_bak_customer_gender
--   để 98_rollback trả lại được giá trị. Bảng sao lưu không nằm trong CDC.
-- Yêu cầu: đã chạy 05. Chạy lại được. Hoàn tác: 98_rollback_add_rename_drop.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. Sao lưu + DDL (bỏ qua nếu đã xóa)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'bronze' AND table_name = 'ins_customer' AND column_name = 'gender') THEN
        DROP TABLE IF EXISTS bronze.ins_bak_customer_gender;
        CREATE TABLE bronze.ins_bak_customer_gender AS
            SELECT customer_code, gender FROM bronze.ins_customer WHERE gender IS NOT NULL;
        ALTER TABLE bronze.ins_bak_customer_gender ADD PRIMARY KEY (customer_code);
        ALTER TABLE bronze.ins_customer DROP COLUMN gender;
    END IF;
END $$;

-- 2. Ghi sổ thay đổi (kỳ vọng: 1 dòng DROP gender)
SELECT change_type, table_name, attnum, old_column_name, old_data_type
FROM bronze.ins_capture_schema_changes('08_drop_column: nguồn bỏ gender');

-- 3. Nguồn sửa 500 khách sau thay đổi (chỉ để sinh event UPDATE không còn field gender)
UPDATE bronze.ins_customer
SET customer_name = customer_name
WHERE customer_code IN (SELECT customer_code FROM bronze.ins_customer
                        WHERE customer_code LIKE 'KH%' AND segment_code = 'CA_NHAN'
                        ORDER BY customer_code DESC LIMIT 500);

-- 4. Khách mới SAU thay đổi: 2 khách cá nhân, không có gender
INSERT INTO bronze.ins_customer
       (customer_code, customer_name, segment_code, tax_code, province_code, home_company_code,
        is_aggregated_retail, created_date)
SELECT 'SIM-C08-' || lpad(rn::text, 3, '0'), 'Khách mô phỏng CASE 08 #' || rn,
       segment_code, tax_code, province_code, home_company_code, is_aggregated_retail, current_date
FROM (SELECT c.*, row_number() OVER (ORDER BY customer_code) AS rn
      FROM bronze.ins_customer c
      WHERE customer_code LIKE 'KH%' AND segment_code = 'CA_NHAN' AND NOT is_aggregated_retail
      ORDER BY customer_code LIMIT 2) s
ON CONFLICT (customer_code) DO NOTHING;

COMMIT;

-- Kiểm tra: gender không còn; sổ có DROP
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'bronze' AND table_name = 'ins_customer' ORDER BY ordinal_position;
SELECT count(*) AS so_khach_da_sao_luu_gender FROM bronze.ins_bak_customer_gender;
