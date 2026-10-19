-- =====================================================================
-- CHUẨN BỊ CHO CASE 06–08 — SỔ GHI THAY ĐỔI SCHEMA (schema change log)
--
-- Vì sao cần: landing (Iceberg) KHÔNG ghi lại việc xóa / đổi tên cột.
--   - Cột bị xóa ở nguồn vẫn còn ở landing, chỉ là NULL ở các event mới
--     → không phân biệt được "NULL vì cột đã bị xóa" với "NULL nghiệp vụ".
--   - Cột bị đổi tên xuất hiện ở landing như MỘT CỘT MỚI, cột cũ vẫn còn
--     → không biết cột mới là đổi tên từ cột nào.
--   Silver cần biết 2 điều này → ghi lại ngay tại nguồn.
--
-- Cách làm: chụp pg_attribute của các bảng bronze.ins_* rồi so với lần chụp trước.
--   PostgreSQL GIỮ NGUYÊN attnum khi RENAME COLUMN / ALTER COLUMN TYPE,
--   đánh dấu attisdropped = true khi DROP COLUMN, cấp attnum MỚI khi ADD COLUMN.
--   → phân biệt chắc chắn ADD / DROP / RENAME / ALTER_TYPE, không phải đoán
--     "xóa cột A + thêm cột B có phải là đổi tên hay không".
--
-- Không cần quyền superuser. Chạy 1 lần trước 06–08 (chạy lại không sao).
-- Gọi bronze.ins_capture_schema_changes() sau mỗi DDL (06–08 đã tự gọi).
-- Muốn tự động ghi mỗi khi có ALTER TABLE: xem 05b_event_trigger_optional.sql (cần superuser).
-- Hoàn tác: 98_rollback_add_rename_drop.sql (giữ sổ), hoặc DROP 2 bảng + hàm ở cuối file 98.
-- =====================================================================
BEGIN;
SET LOCAL lock_timeout = '10s';

-- 1. Ảnh chụp schema gần nhất: 1 dòng / bảng × attnum
CREATE TABLE IF NOT EXISTS bronze.ins_schema_snapshot (
    table_name   text        NOT NULL,
    attnum       smallint    NOT NULL,
    column_name  text        NOT NULL,   -- cột đã xóa: giữ tên cuối cùng trước khi xóa
    data_type    text,                   -- NULL khi cột đã xóa
    is_dropped   boolean     NOT NULL,
    captured_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (table_name, attnum)
);
COMMENT ON TABLE bronze.ins_schema_snapshot IS
    'Ảnh chụp pg_attribute của bronze.ins_* tại lần gọi ins_capture_schema_changes() gần nhất';

-- 2. Sổ thay đổi: silver đọc bảng này để biết cột nào đã xóa / đổi tên
CREATE TABLE IF NOT EXISTS bronze.ins_schema_change_log (
    change_id        bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    table_name       text        NOT NULL,
    change_type      text        NOT NULL CHECK (change_type IN ('ADD', 'DROP', 'RENAME', 'ALTER_TYPE')),
    attnum           smallint    NOT NULL,
    old_column_name  text,                -- NULL khi ADD
    new_column_name  text,                -- NULL khi DROP
    old_data_type    text,
    new_data_type    text,
    detected_at      timestamptz NOT NULL DEFAULT now(),
    wal_lsn          text        NOT NULL,  -- LSN lúc ghi nhận, dạng 'X/Y'
    wal_lsn_num      bigint      NOT NULL,  -- cùng LSN dạng số: so được với cột __source_lsn ở landing
    note             text
);
COMMENT ON TABLE bronze.ins_schema_change_log IS
    'Sổ thay đổi schema của bronze.ins_*: ADD / DROP / RENAME / ALTER_TYPE. Event landing có __source_lsn >= wal_lsn_num là event sau thay đổi';

-- 3a. Schema hiện tại của bronze.ins_* đọc từ catalog (gồm cả cột đã xóa: attisdropped)
CREATE OR REPLACE FUNCTION bronze.ins_schema_current()
RETURNS TABLE (table_name text, attnum smallint, column_name text, data_type text, is_dropped boolean)
LANGUAGE sql STABLE AS $fn$
    SELECT c.relname::text, a.attnum, a.attname::text,
           CASE WHEN a.attisdropped THEN NULL ELSE format_type(a.atttypid, a.atttypmod) END,
           a.attisdropped
    FROM pg_attribute a
    JOIN pg_class c     ON c.oid = a.attrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'bronze' AND c.relkind IN ('r', 'p')
      AND c.relname LIKE 'ins\_%'
      AND c.relname NOT LIKE 'ins\_schema\_%'      -- bỏ chính 2 bảng sổ
      AND c.relname NOT LIKE 'ins\_bak\_%'         -- bỏ bảng sao lưu của script mô phỏng
      AND a.attnum > 0
$fn$;

-- 3b. Hàm so sánh: ghi các thay đổi kể từ lần chụp trước, rồi cập nhật ảnh chụp
CREATE OR REPLACE FUNCTION bronze.ins_capture_schema_changes(p_note text DEFAULT NULL)
RETURNS SETOF bronze.ins_schema_change_log
LANGUAGE plpgsql AS $fn$
DECLARE
    v_lsn pg_lsn := pg_current_wal_lsn();
BEGIN
    -- bảng chưa có trong ảnh chụp (lần chạy đầu / bảng mới): chỉ chụp, không ghi sổ
    RETURN QUERY
    INSERT INTO bronze.ins_schema_change_log
           (table_name, change_type, attnum, old_column_name, new_column_name,
            old_data_type, new_data_type, wal_lsn, wal_lsn_num, note)
    SELECT d.table_name, d.change_type, d.attnum, d.old_name, d.new_name, d.old_type, d.new_type,
           v_lsn::text, (v_lsn - '0/0'::pg_lsn)::bigint, p_note
    FROM (
        SELECT cur.table_name, cur.attnum,
               CASE WHEN s.attnum IS NULL                       THEN 'ADD'
                    WHEN cur.is_dropped AND NOT s.is_dropped    THEN 'DROP'
                    WHEN cur.is_dropped OR s.is_dropped         THEN NULL   -- đã xóa từ trước: không ghi lại
                    WHEN cur.column_name <> s.column_name       THEN 'RENAME'
                    WHEN cur.data_type IS DISTINCT FROM s.data_type THEN 'ALTER_TYPE'
               END AS change_type,
               s.column_name AS old_name,
               CASE WHEN cur.is_dropped THEN NULL ELSE cur.column_name END AS new_name,
               s.data_type AS old_type, cur.data_type AS new_type
        FROM bronze.ins_schema_current() cur
        JOIN (SELECT DISTINCT k.table_name FROM bronze.ins_schema_snapshot k) k USING (table_name)
        LEFT JOIN bronze.ins_schema_snapshot s
               ON s.table_name = cur.table_name AND s.attnum = cur.attnum
        WHERE NOT (s.attnum IS NULL AND cur.is_dropped)   -- thêm rồi xóa giữa 2 lần chụp: bỏ qua
    ) d
    WHERE d.change_type IS NOT NULL
    ORDER BY d.table_name, d.attnum
    RETURNING *;

    INSERT INTO bronze.ins_schema_snapshot AS s (table_name, attnum, column_name, data_type, is_dropped, captured_at)
    SELECT cur.table_name, cur.attnum, cur.column_name, cur.data_type, cur.is_dropped, now()
    FROM bronze.ins_schema_current() cur
    ON CONFLICT (table_name, attnum) DO UPDATE
       SET column_name = CASE WHEN EXCLUDED.is_dropped THEN s.column_name ELSE EXCLUDED.column_name END,
           data_type   = EXCLUDED.data_type,
           is_dropped  = EXCLUDED.is_dropped,
           captured_at = EXCLUDED.captured_at
     WHERE (s.column_name, s.data_type, s.is_dropped) IS DISTINCT FROM
           (CASE WHEN EXCLUDED.is_dropped THEN s.column_name ELSE EXCLUDED.column_name END,
            EXCLUDED.data_type, EXCLUDED.is_dropped);
END
$fn$;
COMMENT ON FUNCTION bronze.ins_capture_schema_changes(text) IS
    'So pg_attribute của bronze.ins_* với ins_schema_snapshot, ghi ADD/DROP/RENAME/ALTER_TYPE vào ins_schema_change_log';

-- 4. Chụp mốc ban đầu (lần đầu: không ghi sổ dòng nào)
SELECT * FROM bronze.ins_capture_schema_changes('05_registry_setup: mốc ban đầu');

COMMIT;

-- Kiểm tra: schema hiện tại của bảng dùng cho case 06–08
SELECT attnum, column_name, data_type, is_dropped
FROM bronze.ins_schema_snapshot
WHERE table_name = 'ins_customer'
ORDER BY attnum;

-- (Tùy chọn) Đưa sổ thay đổi lên landing qua CDC, để silver đọc ngay trong lakehouse:
--   ALTER PUBLICATION dbz_pvi_pub ADD TABLE bronze.ins_schema_change_log;
--   + thêm bronze.ins_schema_change_log vào table.include.list của connector pg-src-pvi
--   + tạo sink iceberg-sink-pvi-ins-schema-change-log → pvi_landing.ins_schema_change_log
--   Xem README_add_rename_drop.md, mục "Đưa sổ lên landing".
