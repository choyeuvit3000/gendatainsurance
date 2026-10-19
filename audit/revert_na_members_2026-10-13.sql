-- =====================================================================
-- HOÀN TÁC MỘT LẦN (13/10/2026): trả bronze về NULL đúng nghiệp vụ nguồn
--   Bản fix trước đã thay NULL bằng thành viên giả (CHUA_XD, WEB_APP, NA_*). Quyết định cuối:
--   bronze giữ NULL như hệ thống lõi; thành viên "không qua đối tác" / "chưa xác định" chỉ ở lớp phân tích.
--   Giữ nguyên các sửa lỗi thật (XM_*/BC_A cho TNDS xe máy, xóa SĐBS trên HĐ chưa duyệt, tỷ lệ phí).
-- Sau script: chạy lại phần view (gen_volume.RPT_SQL) để view gán thành viên ở lớp phân tích.
-- =====================================================================
BEGIN;
UPDATE bronze.ins_policy
SET partner_code = NULL,
    channel_code = CASE WHEN channel_code = 'CHUA_XD' THEN NULL ELSE channel_code END
WHERE partner_code IN ('NA_TRUC_TIEP', 'NA_DAI_LY_CN', 'NA_DAU_THAU', 'WEB_APP', 'NA_CHUA_XD');
COMMIT;

BEGIN;
DELETE FROM bronze.ins_partner WHERE partner_code IN ('NA_TRUC_TIEP', 'NA_DAI_LY_CN', 'NA_DAU_THAU', 'WEB_APP', 'NA_CHUA_XD');
DELETE FROM bronze.ins_channel WHERE channel_code = 'CHUA_XD';
COMMIT;
