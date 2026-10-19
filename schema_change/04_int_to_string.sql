-- =====================================================================
-- CASE 4 — ĐỔI KIỂU SỐ NGUYÊN → CHUỖI (int → varchar)
-- Bảng : bronze.ins_channel (7 dòng — danh mục kênh)
-- Cột  : sort_order  int  →  varchar(10)
-- Tình huống: nguồn đổi "thứ tự hiển thị" từ số sang mã chuỗi.
--   - TRUC_TIEP → '01'  (chuỗi trông như số)
--   - DIEN_TU   → 'D7'  (chuỗi không phải số)
-- Đặc điểm: int → varchar ở PostgreSQL ghi lại bảng (bảng nhỏ, tức thì).
-- Chạy lại nhiều lần được. Hoàn tác: 99_rollback.sql
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

DO $$
BEGIN
    IF (SELECT data_type FROM information_schema.columns
        WHERE table_schema = 'bronze' AND table_name = 'ins_channel' AND column_name = 'sort_order') = 'integer' THEN
        ALTER TABLE bronze.ins_channel ALTER COLUMN sort_order TYPE varchar(10) USING sort_order::text;
    END IF;
END $$;
COMMENT ON COLUMN bronze.ins_channel.sort_order IS 'Thứ tự hiển thị (đổi int → varchar(10) ở CASE 4 mô phỏng schema change)';

-- DML sau thay đổi
UPDATE bronze.ins_channel SET sort_order = '01' WHERE channel_code = 'TRUC_TIEP';
UPDATE bronze.ins_channel SET sort_order = 'D7' WHERE channel_code = 'DIEN_TU';

COMMIT;

SELECT channel_code, sort_order FROM bronze.ins_channel ORDER BY channel_code;
