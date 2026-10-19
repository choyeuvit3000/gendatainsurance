-- =====================================================================
-- ĐỔI PARTITION + SẮP XẾP các bảng Iceberg hive.pvi_landing.ins_* (Dremio 26)
-- Lý do: bảng nhỏ (5–122 MB) nhưng chia theo ngày / bucket → hàng trăm file 0,06–0,4 MB.
-- Chạy KHI các sink iceberg-sink-pvi-ins-* tương ứng đang dừng (spec.state = stopped).
-- Đổi partition tại chỗ (partition evolution): giữ bảng, giữ lịch sử snapshot.
-- Ghi chú: sau khi đổi, hàm TABLE(table_partitions(...)) của Dremio 26 báo lỗi
--   "Number of partition columns not match" (lỗi Dremio với spec đã evolve); truy vấn dữ liệu bình thường.
-- =====================================================================

-- Doanh thu / giao dịch: theo THÁNG ghi nhận (accounting_date là chuỗi 'yyyy-MM-dd' → truncate 7 = 'yyyy-MM')
ALTER TABLE hive.pvi_landing.ins_policy_transaction DROP PARTITION FIELD accounting_date;
ALTER TABLE hive.pvi_landing.ins_policy_transaction ADD PARTITION FIELD truncate(7, accounting_date);
ALTER TABLE hive.pvi_landing.ins_policy_transaction LOCALSORT BY (accounting_date, txn_id);
OPTIMIZE TABLE hive.pvi_landing.ins_policy_transaction REWRITE DATA USING BIN_PACK (MIN_INPUT_FILES = 1);

-- Hợp đồng: theo THÁNG cấp đơn
ALTER TABLE hive.pvi_landing.ins_policy DROP PARTITION FIELD issue_date;
ALTER TABLE hive.pvi_landing.ins_policy ADD PARTITION FIELD truncate(7, issue_date);
ALTER TABLE hive.pvi_landing.ins_policy LOCALSORT BY (issue_date, policy_id);
OPTIMIZE TABLE hive.pvi_landing.ins_policy REWRITE DATA USING BIN_PACK (MIN_INPUT_FILES = 1);

-- Dòng phí: không có cột ngày → bỏ bucket, sắp xếp theo txn_id (tăng theo thời gian → join với giao dịch đã lọc ngày vẫn cắt tỉa file)
ALTER TABLE hive.pvi_landing.ins_transaction_coverage DROP PARTITION FIELD bucket(8, txn_id);
ALTER TABLE hive.pvi_landing.ins_transaction_coverage LOCALSORT BY (txn_id);
OPTIMIZE TABLE hive.pvi_landing.ins_transaction_coverage REWRITE DATA USING BIN_PACK (MIN_INPUT_FILES = 1);

-- Đồng BH, phân bổ: bảng rất nhỏ → bỏ bucket, sắp xếp theo policy_id
ALTER TABLE hive.pvi_landing.ins_coinsurance_share DROP PARTITION FIELD bucket(8, policy_id);
ALTER TABLE hive.pvi_landing.ins_coinsurance_share LOCALSORT BY (policy_id);
OPTIMIZE TABLE hive.pvi_landing.ins_coinsurance_share REWRITE DATA USING BIN_PACK (MIN_INPUT_FILES = 1);

ALTER TABLE hive.pvi_landing.ins_revenue_allocation DROP PARTITION FIELD bucket(8, policy_id);
ALTER TABLE hive.pvi_landing.ins_revenue_allocation LOCALSORT BY (policy_id);
OPTIMIZE TABLE hive.pvi_landing.ins_revenue_allocation REWRITE DATA USING BIN_PACK (MIN_INPUT_FILES = 1);

-- Khách hàng: bỏ partition theo năm tạo (không phải chiều lọc chính), sắp xếp theo customer_code
ALTER TABLE hive.pvi_landing.ins_customer DROP PARTITION FIELD truncate(4, created_date);
ALTER TABLE hive.pvi_landing.ins_customer LOCALSORT BY (customer_code);
OPTIMIZE TABLE hive.pvi_landing.ins_customer REWRITE DATA USING BIN_PACK (MIN_INPUT_FILES = 1);
