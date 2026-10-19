-- =====================================================================
-- KIỂM TRA CASE 06–08 trên PostgreSQL (chạy trước và sau mỗi case)
-- =====================================================================

-- 1. Cột hiện tại của bronze.ins_customer (kèm attnum: rename giữ attnum, add cấp attnum mới)
SELECT a.attnum, a.attname AS column_name, format_type(a.atttypid, a.atttypmod) AS data_type,
       NOT a.attnotnull AS is_nullable
FROM pg_attribute a
WHERE a.attrelid = 'bronze.ins_customer'::regclass AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attnum;

-- 2. Sổ thay đổi schema (silver đọc bảng này)
--    Nếu đã bật 05b (event trigger) thì dòng được ghi lúc chạy ALTER, ghi chú 'event trigger: ALTER TABLE';
--    lệnh gọi trong 06–08 khi đó trả về 0 dòng — bình thường.
SELECT change_id, table_name, change_type, attnum, old_column_name, new_column_name,
       old_data_type, new_data_type, detected_at, wal_lsn, wal_lsn_num, note
FROM bronze.ins_schema_change_log
ORDER BY change_id;

-- 3. Trạng thái cột theo sổ: cột nào silver được select, cột nào là tên cũ của cột nào
--    (đây chính là "hợp đồng" silver dùng; 10_silver_dremio.sql có bản tương tự trên landing)
SELECT s.table_name, s.attnum, s.column_name, s.data_type,
       CASE WHEN s.is_dropped THEN 'DA_XOA → silver bỏ cột' ELSE 'DANG_DUNG' END AS trang_thai,
       (SELECT string_agg(DISTINCT l.old_column_name, ', ')
          FROM bronze.ins_schema_change_log l
         WHERE l.table_name = s.table_name AND l.attnum = s.attnum AND l.change_type = 'RENAME'
           AND l.old_column_name <> s.column_name
       ) AS ten_cu_can_hop_nhat
FROM bronze.ins_schema_snapshot s
WHERE s.table_name = 'ins_customer'
ORDER BY s.attnum;

-- 4. Dòng mô phỏng
SELECT left(customer_code, 7) AS nhom, count(*) FROM bronze.ins_customer
WHERE customer_code LIKE 'SIM-C0%' GROUP BY 1 ORDER BY 1;

-- 5. Sinh danh sách cột cho silver từ sổ → dán vào view silver (10_silver_dremio.sql, phần C)
--    - cột đang dùng, không đổi tên: giữ nguyên
--    - cột đã đổi tên (1 hoặc nhiều lần): COALESCE(tên_mới, tên_cũ_gần_nhất, ..., tên_đầu_tiên)
--    - cột đã xóa: không có trong danh sách (liệt kê ở cột cot_da_xoa để ghi chú)
SELECT s.table_name,
       string_agg(CASE WHEN r.old_names IS NULL THEN quote_ident(s.column_name)
                       ELSE format('COALESCE(%s, %s) AS %s', quote_ident(s.column_name), r.old_names,
                                   quote_ident(s.column_name)) END,
                  E',\n       ' ORDER BY s.attnum) FILTER (WHERE NOT s.is_dropped) AS silver_select_list,
       string_agg(s.column_name, ', ' ORDER BY s.attnum) FILTER (WHERE s.is_dropped
                  AND s.column_name NOT LIKE '%pg.dropped%') AS cot_da_xoa
FROM bronze.ins_schema_snapshot s
LEFT JOIN LATERAL (
    SELECT string_agg(DISTINCT quote_ident(l.old_column_name), ', ') AS old_names
    FROM bronze.ins_schema_change_log l
    WHERE l.table_name = s.table_name AND l.attnum = s.attnum AND l.change_type = 'RENAME'
      AND l.old_column_name <> s.column_name
) r ON true
WHERE s.table_name = 'ins_customer'
GROUP BY s.table_name;

-- 6. Quét ngay (không ghi sổ nếu không có gì đổi) — dùng khi nghi có DDL chạy ngoài script
-- SELECT * FROM bronze.ins_capture_schema_changes('quét tay');
