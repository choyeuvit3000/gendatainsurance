-- =====================================================================
-- LANDING → SILVER cho CASE 06–08 — chạy trên DREMIO (không phải PostgreSQL)
-- Bảng landing: hive.pvi_landing.ins_customer (Iceberg, append-only: mỗi event r/c/u/d là 1 dòng)
--   Cột kỹ thuật do Debezium unwrap thêm: __op, __source_ts_ms, __source_lsn, __deleted
-- Chạy từng khối bằng Ctrl+Enter (hoặc trong Dremio UI). Chờ sink commit (~30 giây) sau mỗi case.
-- =====================================================================

-- A0. Dremio cache metadata của bảng Hive → cột mới chỉ hiện sau khi refresh
ALTER TABLE hive.pvi_landing.ins_customer REFRESH METADATA;

-- A1. Cột ở landing. Kỳ vọng sau 06–08: CÒN gender, CÒN birth_year, THÊM kyc_status, THÊM year_of_birth
SELECT ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA."COLUMNS"
WHERE TABLE_SCHEMA = 'hive.pvi_landing' AND TABLE_NAME = 'ins_customer'
ORDER BY ORDINAL_POSITION;

-- A2. Event nào có giá trị ở cột nào, theo thứ tự LSN (chạy sau khi đã chạy đủ 06–08).
--     Chỉ xét khách cá nhân (có năm sinh / giới tính) + khách mô phỏng. Kỳ vọng:
--   __op  gender birth_year year_of_birth kyc   ý nghĩa
--   r/c   x      x          -             -     event trước 06 (nạp ban đầu)
--   u     x      x          -             x     backfill kyc ở 06 (trước 07)
--   u/c   x      -          x             -     event sau 07, trước 08
--   u/c   -      -          x             -     event sau 08: gender NULL dù là khách cá nhân
SELECT __op,
       CASE WHEN gender        IS NOT NULL THEN 'x' ELSE '-' END AS gender,
       CASE WHEN birth_year    IS NOT NULL THEN 'x' ELSE '-' END AS birth_year,
       CASE WHEN year_of_birth IS NOT NULL THEN 'x' ELSE '-' END AS year_of_birth,
       CASE WHEN kyc_status    IS NOT NULL THEN 'x' ELSE '-' END AS kyc_status,
       count(*) AS so_event,
       sum(CASE WHEN customer_code LIKE 'SIM-%' THEN 1 ELSE 0 END) AS trong_do_khach_mo_phong,
       min(__source_lsn) AS lsn_tu, max(__source_lsn) AS lsn_den
FROM hive.pvi_landing.ins_customer
WHERE segment_code = 'CA_NHAN' OR customer_code LIKE 'SIM-%'
GROUP BY 1, 2, 3, 4, 5
ORDER BY min(__source_lsn);

-- A3. Một khách bị sửa sau 07 và 08: thấy rõ giá trị "chuyển" từ birth_year sang year_of_birth
SELECT customer_code, __op, __source_lsn, gender, birth_year, year_of_birth, kyc_status
FROM hive.pvi_landing.ins_customer
WHERE customer_code = (SELECT min(customer_code) FROM hive.pvi_landing.ins_customer
                       WHERE year_of_birth IS NOT NULL AND customer_code LIKE 'KH%')
ORDER BY __source_lsn;

-- ---------------------------------------------------------------------
-- C. SILVER — trạng thái hiện tại của khách hàng, đã áp dụng sổ thay đổi schema
--   - DROP gender         → không select gender
--   - RENAME birth_year   → COALESCE(year_of_birth, birth_year) AS year_of_birth, tính TRÊN TỪNG EVENT
--                           (mỗi event chỉ có 1 trong 2 cột có giá trị, nên COALESCE không lấy nhầm
--                            giá trị cũ khi nguồn cố ý set NULL sau đổi tên)
--   - ADD kyc_status      → select bình thường (NULL với khách chưa có event sau 06)
-- Danh sách cột lấy từ 09_check_add_rename_drop.sql mục 5 (sinh tự động từ sổ).
-- ---------------------------------------------------------------------
SELECT customer_code, customer_name, segment_code, tax_code, province_code, home_company_code,
       is_aggregated_retail, created_date,
       year_of_birth,
       kyc_status
FROM (
    SELECT l.customer_code, l.customer_name, l.segment_code, l.tax_code, l.province_code,
           l.home_company_code, l.is_aggregated_retail, l.created_date,
           COALESCE(l.year_of_birth, l.birth_year) AS year_of_birth,
           l.kyc_status,
           l.__deleted,
           ROW_NUMBER() OVER (PARTITION BY l.customer_code
                              ORDER BY l.__source_lsn DESC, l.__source_ts_ms DESC) AS rn
    FROM hive.pvi_landing.ins_customer l
) x
WHERE rn = 1 AND COALESCE(__deleted, 'false') <> 'true';

-- C1. Đối chiếu nhanh: số khách có năm sinh ở silver phải bằng số khách có year_of_birth ở PostgreSQL
--     (PostgreSQL: SELECT count(year_of_birth) FROM bronze.ins_customer;)
SELECT count(*) AS so_khach, count(year_of_birth) AS co_nam_sinh, count(kyc_status) AS co_kyc
FROM (
    SELECT COALESCE(l.year_of_birth, l.birth_year) AS year_of_birth, l.kyc_status, l.__deleted,
           ROW_NUMBER() OVER (PARTITION BY l.customer_code
                              ORDER BY l.__source_lsn DESC, l.__source_ts_ms DESC) AS rn
    FROM hive.pvi_landing.ins_customer l
) x
WHERE rn = 1 AND COALESCE(__deleted, 'false') <> 'true';
