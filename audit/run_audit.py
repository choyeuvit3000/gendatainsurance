"""Chạy consistency_checks.sql và in bảng vi phạm.

    PG_URI=postgresql://report:<pw>@127.0.0.1:15432/reportapi  python audit/run_audit.py
"""
import os
import re
import sys
import time
from pathlib import Path

import psycopg

sys.stdout.reconfigure(encoding="utf-8")
sql = (Path(__file__).parent / "consistency_checks.sql").read_text(encoding="utf-8")
sql = re.sub(r"--[^\n]*", "", sql)
stmts = [s.strip() for s in sql.split(";") if s.strip()]

with psycopg.connect(os.environ["PG_URI"]) as conn:
    conn.execute("SET work_mem = '256MB'")
    total = 0
    for s in stmts:
        t = time.time()
        cur = conn.execute(s)
        if not cur.description:
            continue
        rows = [r for r in cur.fetchall() if r[2]]
        code = re.search(r"SELECT '(\w+)'", s).group(1)
        if not rows:
            print(f"✅ {code}  ({time.time() - t:.0f}s)")
        for r in rows:
            if r[0].startswith("I"):          # dòng thông tin, không tính vi phạm
                print(f"ℹ️  {r[0]}  {r[1]}: {r[2]:,}  ví dụ: {r[3]}")
                continue
            total += r[2]
            print(f"❌ {r[0]}  {r[1]}: {r[2]:,}  ví dụ: {r[3]}")
    print(f"\nTổng dòng vi phạm: {total:,}")
