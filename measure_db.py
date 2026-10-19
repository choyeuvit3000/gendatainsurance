"""Đo số liệu thật trên bronze.ins_* (reportapi) → docs/db_snapshot.json.
Dùng cho tài liệu học, hỏi đáp và deck (scripts/build_learning.py, scripts/build_deck.js) — mọi con số về "dữ liệu trên DB" lấy từ file này.

Chạy (khi tunnel mở, xem README):
    PG_URI=postgresql://report:<mật khẩu>@127.0.0.1:15432/reportapi python measure_db.py
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

import psycopg

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).parent / "docs" / "db_snapshot.json"
S = "bronze.ins_"
GRP = f"""JOIN {S}product pr ON pr.product_code = c.product_code"""
OWN = f"""JOIN {S}coinsurance_share cs ON cs.policy_id = t.policy_id AND cs.insurer_code = 'OWN'"""

Q = {
    "rows": f"""SELECT 'policy', count(*) FROM {S}policy UNION ALL SELECT 'policy_transaction', count(*) FROM {S}policy_transaction
               UNION ALL SELECT 'transaction_coverage', count(*) FROM {S}transaction_coverage
               UNION ALL SELECT 'coinsurance_share', count(*) FROM {S}coinsurance_share
               UNION ALL SELECT 'revenue_allocation', count(*) FROM {S}revenue_allocation
               UNION ALL SELECT 'customer', count(*) FROM {S}customer""",
    "id_range": f"""SELECT min(policy_id), max(policy_id), min(customer_code), max(customer_code) FROM {S}policy""",
    "txn_per_day": f"""SELECT extract(month FROM txn_date)::int, min(n), max(n), round(avg(n)) FROM
                      (SELECT txn_date, count(*) n FROM {S}policy_transaction WHERE txn_date BETWEEN '2026-08-01' AND '2026-09-30' GROUP BY 1) x
                      GROUP BY 1 ORDER BY 1""",
    "txn_type": f"SELECT txn_type_code, count(*) FROM {S}policy_transaction GROUP BY 1 ORDER BY 2 DESC",
    "status": f"SELECT status, count(*) FROM {S}policy_transaction GROUP BY 1 ORDER BY 2 DESC",
    # doanh thu ghi nhận (accounting_date trong kỳ) theo nhóm sản phẩm và tháng
    "rev_group_month": f"""SELECT pr.product_group_code, extract(month FROM t.accounting_date)::int,
                              sum(c.premium_vnd * cs.share_pct / 100) / 1e9
                          FROM {S}transaction_coverage c JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
                          {OWN} {GRP}
                          WHERE t.accounting_date BETWEEN '2026-08-01' AND '2026-09-30' GROUP BY 1, 2 ORDER BY 1, 2""",
    # phí gốc khai thác (cấp mới / tái tục, theo ngày chứng từ) — đúng thước đo dùng để hiệu chỉnh
    "written_group": f"""SELECT pr.product_group_code, sum(c.premium_vnd * cs.share_pct / 100) / 1e9
                        FROM {S}transaction_coverage c JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
                             AND t.txn_type_code IN ('NEW', 'RENEW') {OWN} {GRP} GROUP BY 1 ORDER BY 1""",
    # sản phẩm chính của hợp đồng = dòng phí đầu tiên của giao dịch cấp mới / tái tục
    "policies_group": f"""SELECT pr.product_group_code, count(*) FROM (
                             SELECT DISTINCT ON (t.policy_id) t.policy_id, c.product_code
                             FROM {S}policy_transaction t JOIN {S}transaction_coverage c ON c.txn_id = t.txn_id
                             WHERE t.txn_type_code IN ('NEW', 'RENEW') ORDER BY t.policy_id, c.coverage_id) m
                         JOIN {S}product pr ON pr.product_code = m.product_code GROUP BY 1""",
    "segment": f"""WITH r AS (SELECT t.policy_id, sum(c.premium_vnd * cs.share_pct / 100) rev
                             FROM {S}transaction_coverage c JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
                             {OWN} WHERE t.accounting_date BETWEEN '2026-08-01' AND '2026-09-30' GROUP BY 1)
                  SELECT CASE WHEN cu.is_aggregated_retail THEN 'KHACH_LE_GOP' ELSE cu.segment_code END, count(*), sum(coalesce(r.rev, 0)) / 1e9
                  FROM {S}policy p JOIN {S}customer cu ON cu.customer_code = p.customer_code LEFT JOIN r ON r.policy_id = p.policy_id
                  GROUP BY 1 ORDER BY 3 DESC""",
    "channel": f"""SELECT coalesce(p.channel_code, 'NULL'), sum(c.premium_vnd * cs.share_pct / 100) / 1e9
                  FROM {S}transaction_coverage c JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
                  {OWN} JOIN {S}policy p ON p.policy_id = t.policy_id
                  WHERE t.accounting_date BETWEEN '2026-08-01' AND '2026-09-30' GROUP BY 1 ORDER BY 2 DESC""",
    "top_share": f"""WITH r AS (SELECT t.policy_id, sum(c.premium_vnd * cs.share_pct / 100) rev
                                FROM {S}transaction_coverage c JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
                                {OWN} WHERE t.accounting_date BETWEEN '2026-08-01' AND '2026-09-30' GROUP BY 1),
                     k AS (SELECT rev, ntile(100) OVER (ORDER BY rev DESC) pct FROM r)
                    SELECT sum(rev) FILTER (WHERE pct <= 10) / sum(rev), sum(rev) FILTER (WHERE pct = 1) / sum(rev) FROM k""",
    "spill_after": f"""SELECT sum(c.premium_vnd * cs.share_pct / 100) / 1e9 FROM {S}transaction_coverage c
                      JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED' {OWN}
                      WHERE t.accounting_date > '2026-09-30'""",
    "deductions": f"""SELECT sum(c.premium_vnd * cs.share_pct / 100) / 1e9 FROM {S}transaction_coverage c
                     JOIN {S}policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
                     AND t.txn_type_code NOT IN ('NEW', 'RENEW') {OWN}
                     WHERE t.accounting_date BETWEEN '2026-08-01' AND '2026-09-30'""",
}


def main():
    uri = os.environ.get("PG_URI") or sys.exit("Thiếu PG_URI")
    out = {"measured_at": dt.datetime.now().isoformat(timespec="seconds")}
    with psycopg.connect(uri, connect_timeout=30) as c:
        cur = c.cursor()
        cur.execute("SET statement_timeout = '15min'")
        for k, q in Q.items():
            cur.execute(q)
            out[k] = [[float(x) if hasattr(x, "as_integer_ratio") and not isinstance(x, int) else x for x in r] for r in cur.fetchall()]
            print(k, out[k][:12])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("→", OUT)


if __name__ == "__main__":
    main()
