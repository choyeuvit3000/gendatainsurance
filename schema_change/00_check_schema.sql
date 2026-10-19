-- =====================================================================
-- XEM SCHEMA HIỆN TẠI của 2 bảng dùng để mô phỏng thay đổi schema
-- Chạy trước và sau mỗi case để so sánh.
-- =====================================================================
SELECT table_name, ordinal_position AS pos, column_name,
       CASE WHEN data_type = 'numeric' THEN format('numeric(%s,%s)', numeric_precision, numeric_scale)
            WHEN data_type = 'character varying' THEN format('varchar(%s)', character_maximum_length)
            ELSE data_type END AS data_type,
       is_nullable
FROM information_schema.columns
WHERE table_schema = 'bronze' AND table_name IN ('ins_policy', 'ins_policy_transaction')
ORDER BY table_name, ordinal_position;

-- Số dòng do script mô phỏng tạo ra (created_by = 'SIM.SCHEMA_CHANGE')
SELECT txn_type_code, count(*) AS so_giao_dich_mo_phong, min(created_at), max(created_at)
FROM bronze.ins_policy_transaction
WHERE created_by = 'SIM.SCHEMA_CHANGE'
GROUP BY 1;
