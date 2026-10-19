-- atomic.pvi_vw_revenue_insurance_agg — doanh thu gộp sẵn theo 10 chiều dashboard (~263 nghìn dòng)
-- Dùng cho mọi chart doanh thu. Có Raw Reflection riêng; Superset bọc LIMIT để bộ lọc / cross-filter vẫn dùng reflection.
-- Đếm hợp đồng / khách hàng KHÔNG dùng view này (cần chi tiết) → dùng atomic.pvi_vw_revenue_insurance.
SELECT Ngay, kenh_ban, nhom_kenh_bao_cao, doi_tac, nghiep_vu, nhom_nghiep_vu_poc,
       nhom_san_pham, san_pham, don_vi, phan_khuc_kh,
       SUM(doanh_thu_vnd) AS doanh_thu_vnd
FROM "atomic".pvi_vw_revenue_insurance
GROUP BY Ngay, kenh_ban, nhom_kenh_bao_cao, doi_tac, nghiep_vu, nhom_nghiep_vu_poc,
         nhom_san_pham, san_pham, don_vi, phan_khuc_kh
