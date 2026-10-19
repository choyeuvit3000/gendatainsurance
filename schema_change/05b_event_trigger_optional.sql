-- =====================================================================
-- TÙY CHỌN — TỰ ĐỘNG GHI SỔ MỖI KHI CÓ ALTER TABLE (event trigger)
--
-- Không có file này: phải tự gọi bronze.ins_capture_schema_changes() sau mỗi DDL
--   (06–08 đã tự gọi). DDL nào chạy ngoài các script này sẽ chỉ được ghi ở lần gọi kế tiếp
--   (vẫn ghi đúng ADD/DROP/RENAME vì so theo attnum, chỉ là detected_at / wal_lsn trễ hơn).
-- Có file này: mọi ALTER TABLE trên DB đều gọi hàm ngay lúc kết thúc lệnh.
--
-- YÊU CẦU: quyền superuser (PostgreSQL 14 chỉ cho superuser tạo event trigger).
--   User `report` không phải superuser → script báo NOTICE và bỏ qua, không lỗi.
-- AN TOÀN: event trigger chạy cho MỌI ALTER TABLE trên cả DB (kể cả bảng không phải ins_*).
--   Hàm bọc EXCEPTION → nếu sổ lỗi thì chỉ cảnh báo, KHÔNG chặn lệnh ALTER TABLE của người khác.
-- Gỡ: DROP EVENT TRIGGER IF EXISTS trg_ins_schema_change; (cuối file 98 đã có)
-- =====================================================================
CREATE OR REPLACE FUNCTION bronze.ins_schema_change_evt()
RETURNS event_trigger
LANGUAGE plpgsql AS $fn$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_event_trigger_ddl_commands() c
               WHERE c.schema_name = 'bronze' AND c.object_type IN ('table', 'table column')) THEN
        PERFORM bronze.ins_capture_schema_changes('event trigger: ' || tg_tag);
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'ins_schema_change_evt bỏ qua: %', SQLERRM;
END
$fn$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_event_trigger WHERE evtname = 'trg_ins_schema_change') THEN
        CREATE EVENT TRIGGER trg_ins_schema_change ON ddl_command_end
            WHEN TAG IN ('ALTER TABLE')
            EXECUTE FUNCTION bronze.ins_schema_change_evt();
    END IF;
    RAISE NOTICE 'Đã bật event trigger trg_ins_schema_change';
EXCEPTION WHEN insufficient_privilege THEN
    RAISE NOTICE 'Không đủ quyền tạo event trigger (cần superuser) → bỏ qua. 06–08 vẫn tự gọi ins_capture_schema_changes().';
END $$;

SELECT evtname, evtevent, evtenabled, evttags FROM pg_event_trigger WHERE evtname = 'trg_ins_schema_change';
