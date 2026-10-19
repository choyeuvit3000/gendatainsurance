-- atomic.pvi_vw_revenue_insurance — bản tối ưu 14/10/2026 (bản cũ: backup_2026-10-14/dremio_view.sql)
-- Thay đổi:
--  1. Mức chi tiết = dòng phí × đơn vị được phân bổ (bỏ GROUP BY). Việc gộp do Aggregation Reflection đảm nhận.
--  2. Ngay kiểu DATE (trước: VARCHAR) → lọc / time grain theo ngày đúng kiểu.
--  3. Thêm ma_hop_dong (policy_id) để đếm hợp đồng đúng; bỏ so_hop_dong (SUM các COUNT DISTINCT bị cộng trùng).
--  4. Kỳ báo cáo đủ 01/08 – 30/09 (trước: < '2026-09-30' bỏ sót ngày 30/09).
-- Chỉ số trên dashboard:
--  - Doanh thu        = SUM(doanh_thu_vnd)
--  - Số hợp đồng      = APPROX_COUNT_DISTINCT(ma_hop_dong)     (khớp reflection; sai số ~1%)
--  - Số khách hàng    = APPROX_COUNT_DISTINCT(ma_khach_hang)   (đếm theo MÃ, không theo tên)
SELECT
    CAST(t.accounting_date AS DATE)                                      AS Ngay,

    COALESCE(ch.channel_name, 'Chưa khai báo')                           AS kenh_ban,
    ch.report_channel_group                                              AS nhom_kenh_bao_cao,
    pt.partner_name                                                      AS doi_tac,

    lob.lob_name                                                         AS nghiep_vu,
    lob.poc_group_name                                                   AS nhom_nghiep_vu_poc,

    pg.product_group_name                                                AS nhom_san_pham,
    pr.product_code                                                      AS ma_san_pham,
    pr.product_name                                                      AS san_pham,

    co.company_code                                                      AS ma_don_vi,
    co.company_name                                                      AS don_vi,

    cs.segment_name                                                      AS phan_khuc_kh,
    cu.customer_code                                                     AS ma_khach_hang,
    cu.customer_name                                                     AS khach_hang,

    p.policy_id                                                          AS ma_hop_dong,
    tc.premium_vnd * cin.share_pct / 100.0 * ra.allocation_pct / 100.0  AS doanh_thu_vnd
FROM hive.pvi_staging."ins_policy_transaction"   t
JOIN hive.pvi_staging."ins_transaction_coverage" tc  ON tc.txn_id = t.txn_id
JOIN hive.pvi_staging."ins_policy"               p   ON p.policy_id = t.policy_id
JOIN hive.pvi_staging."ins_coinsurance_share"    cin ON cin.policy_id = p.policy_id
                                                    AND cin.insurer_code = 'OWN'
JOIN hive.pvi_staging."ins_revenue_allocation"   ra  ON ra.policy_id = p.policy_id
JOIN hive.pvi_staging."ins_company"              co  ON co.company_code = ra.company_code
JOIN hive.pvi_staging."ins_product"              pr  ON pr.product_code = tc.product_code
JOIN hive.pvi_staging."ins_product_group"        pg  ON pg.product_group_code = pr.product_group_code
JOIN hive.pvi_staging."ins_line_of_business"     lob ON lob.lob_code = pg.lob_code
JOIN hive.pvi_staging."ins_customer"             cu  ON cu.customer_code = p.customer_code
JOIN hive.pvi_staging."ins_customer_segment"     cs  ON cs.segment_code = cu.segment_code
LEFT JOIN hive.pvi_staging."ins_channel"         ch  ON ch.channel_code = p.channel_code
LEFT JOIN hive.pvi_staging."ins_partner"         pt  ON pt.partner_code = p.partner_code
WHERE t.status = 'APPROVED'
  AND t.accounting_date >= '2026-08-01'
  AND t.accounting_date <= '2026-09-30'
