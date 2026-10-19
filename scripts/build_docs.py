r"""
Sinh tài liệu cho mô hình v2 từ CATALOG PostgreSQL thật (không gõ tay kiểu dữ liệu / khóa):
  docs/Data_Dictionary_v2.xlsx      Data dictionary chi tiết
  docs/POC_Doanh_thu_BH_v2.html     Tổng hợp toàn bộ tài liệu (1 file)
  01b_column_comments.sql           COMMENT ON TABLE/COLUMN cho PostgreSQL

Chạy (cần Python 3.11 cho pgserver — Postgres nhúng, không cài vào máy):
  uv run --python 3.11 --with pgserver --with "psycopg[binary]" --with markdown --with openpyxl python scripts/build_docs.py
Hoặc trỏ tới Postgres có sẵn:  set PG_URI=postgresql://user:pass@host:5432/postgres

Bộ dữ liệu KHỐI LƯỢNG LỚN (gen_volume.py → bronze.ins_* trên reportapi), đọc trực tiếp, không tạo DB:
  set DOCS_TARGET=volume
  set PG_URI=postgresql://report:<pw>@127.0.0.1:15432/reportapi     (tunnel k8s)
  → docs/Data_Dictionary_volume.xlsx, docs/POC_Doanh_thu_BH_volume.html
"""
import datetime as dt
import html
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import markdown
import psycopg
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink

sys.path.insert(0, str(Path(__file__).parent))
from dictionary_meta import BUSINESS_RULES, COLUMNS, SCENARIOS, TABLES, VOLUME_BUSINESS_RULES, VOLUME_COLUMNS  # noqa: E402

SCRIPTS = Path(__file__).parent
V2 = SCRIPTS.parent
DOCS = V2 / "docs"
DB = "ins_revenue_poc_docs"
TODAY = dt.date.today()

# Chế độ: v2 (mặc định, DB dựng từ 01_ddl + 02_data) | volume (đọc bronze.ins_* có sẵn — tên vật lý ref.X/core.X → bronze.ins_X)
VOLUME = os.getenv("DOCS_TARGET", "v2") == "volume"
VOL_DIR = V2                       # repo đã gộp: nội dung bộ volume nằm ngay trong thư mục gốc
OUT_DIR = VOL_DIR / "docs" if VOLUME else DOCS
SRC_DIR = VOL_DIR if VOLUME else V2
XLSX_NAME = "Data_Dictionary_volume.xlsx" if VOLUME else "Data_Dictionary_v2.xlsx"
HTML_NAME = "POC_Doanh_thu_BH_volume.html" if VOLUME else "POC_Doanh_thu_BH_v2.html"
DOC_TITLE = "POC Doanh thu bảo hiểm — dữ liệu khối lượng lớn" if VOLUME else "POC Doanh thu bảo hiểm v2"
PHYS_SCHEMA, PHYS_PREFIX = "bronze", "ins_"
if VOLUME:
    COLUMNS = {**COLUMNS, **VOLUME_COLUMNS}
    BUSINESS_RULES = BUSINESS_RULES + VOLUME_BUSINESS_RULES


def phys(t):
    """Tên logic ref.X / core.X → tên vật lý (chế độ volume: bronze.ins_X)."""
    return f"{PHYS_SCHEMA}.{PHYS_PREFIX}{t.split('.', 1)[1]}" if VOLUME else t


def rw(sql):
    return re.sub(r"\b(?:ref|core)\.\w+", lambda m: phys(m.group(0)), sql) if VOLUME else sql


LOGICAL = {t.split(".", 1)[1]: t for t in TABLES}   # tên bảng gốc → ref.X / core.X
WHERE_COLS = (f"c.table_schema = '{PHYS_SCHEMA}' AND c.table_name LIKE '{PHYS_PREFIX}%'" if VOLUME
              else "c.table_schema IN ('ref','core')")
WHERE_CONS = (f"n.nspname = '{PHYS_SCHEMA}' AND cl.relname LIKE '{PHYS_PREFIX}%'" if VOLUME else "n.nspname IN ('ref','core')")
KPI_WHERE = ("t.accounting_date BETWEEN '2026-08-01' AND '2026-09-30'" if VOLUME
             else "extract(year FROM t.accounting_date) = 2025")
KPI_LABEL = "Doanh thu 08–09/2026 (tỷ VND)" if VOLUME else "Doanh thu 2025 (tỷ VND)"


# ============================================================================
# 1. Dựng DB và đọc catalog
# ============================================================================
def start_db():
    uri = os.getenv("PG_URI")
    psql = "psql"
    srv = None
    if not uri:
        import pgserver
        import tempfile
        pgdir = Path(os.getenv("PGSERVER_DIR", Path(tempfile.gettempdir()) / "ins_revenue_poc_pgdata")).resolve()
        srv = pgserver.get_server(str(pgdir), cleanup_mode="stop")
        uri = srv.get_uri()
        psql = os.path.join(os.path.dirname(pgserver.__file__), "pginstall", "bin", "psql.exe" if os.name == "nt" else "psql")
    base = uri.rsplit("/", 1)[0]

    def run(db, *args):
        r = subprocess.run([psql, "-w", "-X", "-q", "-v", "ON_ERROR_STOP=1", *args, "-d", f"{base}/{db}"],
                           cwd=V2, capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
                           env=dict(os.environ, PGCLIENTENCODING="UTF8"), timeout=1800)
        if r.returncode:
            raise SystemExit(f"psql lỗi {args}: {r.stderr[-2000:]}")

    run("postgres", "-c", f"DROP DATABASE IF EXISTS {DB}", "-c", f"CREATE DATABASE {DB}")
    for f in ("01_ddl.sql", "01b_column_comments.sql", "02_data.sql"):
        if (V2 / f).exists():
            run(DB, "-f", f)
    return srv, f"{base}/{DB}"


def read_catalog(conn):
    q = lambda sql: conn.execute(sql).fetchall()  # noqa: E731
    cols = q("""
        SELECT c.table_schema, c.table_name, c.ordinal_position, c.column_name,
               format_type(a.atttypid, a.atttypmod), c.is_nullable = 'NO', c.is_identity = 'YES'
        FROM information_schema.columns c
        JOIN information_schema.tables t USING (table_schema, table_name)
        JOIN pg_attribute a ON a.attrelid = format('%I.%I', c.table_schema, c.table_name)::regclass AND a.attname = c.column_name
        WHERE {WHERE_COLS} AND t.table_type = 'BASE TABLE'
        ORDER BY 1, 2, 3""".replace("{WHERE_COLS}", WHERE_COLS))
    if VOLUME:   # bronze.ins_X → (ref|core, X); bỏ bảng không thuộc mô hình
        cols = [(*LOGICAL[t[len(PHYS_PREFIX):]].split("."), *r) for s, t, *r in cols if t[len(PHYS_PREFIX):] in LOGICAL]
    cons = q("""
        SELECT n.nspname || '.' || cl.relname, a.attname, co.contype,
               fn.nspname || '.' || fcl.relname, fa.attname
        FROM pg_constraint co
        JOIN pg_class cl ON cl.oid = co.conrelid JOIN pg_namespace n ON n.oid = cl.relnamespace
        CROSS JOIN LATERAL unnest(co.conkey, coalesce(co.confkey, co.conkey)) AS k(a1, a2)
        JOIN pg_attribute a ON a.attrelid = cl.oid AND a.attnum = k.a1
        LEFT JOIN pg_class fcl ON fcl.oid = co.confrelid LEFT JOIN pg_namespace fn ON fn.oid = fcl.relnamespace
        LEFT JOIN pg_attribute fa ON fa.attrelid = fcl.oid AND fa.attnum = k.a2
        WHERE {WHERE_CONS} AND co.contype IN ('p','f','u')""".replace("{WHERE_CONS}", WHERE_CONS))
    if VOLUME:
        def to_log(x):
            return x and LOGICAL.get(x.split(".", 1)[1][len(PHYS_PREFIX):])
        cons = [(to_log(tb), c, ct, to_log(ft), fc) for tb, c, ct, ft, fc in cons if to_log(tb)]
    pk, fk, uq = defaultdict(set), {}, defaultdict(set)
    for tbl, col, ct, ftbl, fcol in cons:
        if ct == "p":
            pk[tbl].add(col)
        elif ct == "f":
            fk[(tbl, col)] = f"{ftbl}.{fcol}"
        else:
            uq[tbl].add(col)
    tables = sorted({f"{s}.{t}" for s, t, *_ in cols}, key=lambda x: (["ref", "core"].index(x.split(".")[0]), list(TABLES).index(x) if x in TABLES else 99))
    cols.sort(key=lambda r: (tables.index(f"{r[0]}.{r[1]}"), r[2]))  # cùng thứ tự với sheet tổng quan: ref → core
    rows = {t: conn.execute(f"SELECT count(*) FROM {phys(t)}").fetchone()[0] for t in tables}
    stats = {}
    for s, t, _, c, *_ in cols:
        tbl = f"{s}.{t}"
        n_null, n_dist = conn.execute(f'SELECT count(*) FILTER (WHERE "{c}" IS NULL), count(DISTINCT "{c}") FROM {phys(tbl)}').fetchone()
        samples = [r[0] for r in conn.execute(f'SELECT DISTINCT "{c}"::text FROM {phys(tbl)} WHERE "{c}" IS NOT NULL ORDER BY 1 LIMIT 3').fetchall()]
        stats[(tbl, c)] = (n_null / rows[tbl] if rows[tbl] else 0, n_dist, " | ".join(x[:40] for x in samples))
    codes = {name: (lambda r: ([d.name for d in r.description], r.fetchall()))(conn.execute(rw(sql))) for name, sql in {
        "DM Sản phẩm": """SELECT p.product_code, p.product_name, g.product_group_name, l.lob_name, l.poc_group_name, p.report_line_code,
                                 p.is_compulsory, p.pricing_basis, p.vat_rate, p.max_commission_pct, p.solvency2_lob, p.legal_basis
                          FROM ref.product p JOIN ref.product_group g USING (product_group_code) JOIN ref.line_of_business l USING (lob_code)
                          ORDER BY g.sort_order, p.product_code""",
        "DM Kênh - Đối tác": """SELECT c.channel_code, c.channel_name, c.report_channel_group, p.partner_code, p.partner_name, p.partner_type, c.legal_basis
                                FROM ref.channel c LEFT JOIN ref.partner p USING (channel_code) ORDER BY c.sort_order, p.partner_code NULLS FIRST""",
        "DM Loại giao dịch": "SELECT * FROM ref.transaction_type ORDER BY premium_sign DESC, txn_type_code",
        "DM Đơn vị": """SELECT c.company_code, c.company_name, c.company_type, c.parent_company_code, p.province_name, r.region_name
                        FROM ref.company c LEFT JOIN ref.province p USING (province_code) LEFT JOIN ref.region r USING (region_code)
                        ORDER BY c.parent_company_code NULLS FIRST, c.company_type, c.company_code""",
        "DM Dòng báo cáo": "SELECT * FROM ref.regulatory_line ORDER BY report_line_code",
    }.items()}
    kpi = conn.execute(rw("""
        SELECT (SELECT count(*) FROM core.policy), (SELECT count(*) FROM core.policy_transaction),
               (SELECT count(*) FROM core.transaction_coverage),
               (SELECT round(sum(cv.premium_vnd * own.share_pct / 100 * ra.allocation_pct / 100) / 1e9)
                FROM core.transaction_coverage cv
                JOIN core.policy_transaction t  ON t.txn_id = cv.txn_id AND t.status = 'APPROVED'
                JOIN core.coinsurance_share own ON own.policy_id = t.policy_id AND own.insurer_code = 'OWN'
                JOIN core.revenue_allocation ra ON ra.policy_id = t.policy_id
                WHERE {KPI_WHERE}),
               (SELECT count(*) FROM ref.customer)""".replace("{KPI_WHERE}", KPI_WHERE))).fetchone()
    samples = {}
    for t in tables:
        cur = conn.execute(f"SELECT * FROM {phys(t)} ORDER BY 1 LIMIT 5")
        samples[t] = ([d.name for d in cur.description], cur.fetchall())
    return cols, pk, fk, uq, tables, rows, stats, codes, kpi, samples


# ============================================================================
# 2. COMMENT ON
# ============================================================================
def write_comments():
    lit = lambda s: "'" + s.replace("'", "''") + "'"  # noqa: E731
    out = ["/* COMMENT ON TABLE/COLUMN — sinh bởi scripts/build_docs.py từ scripts/dictionary_meta.py. Chạy sau 01_ddl.sql */"]
    for t, (_, desc, grain, basis) in TABLES.items():
        out.append(f"COMMENT ON TABLE {t} IS {lit(f'{desc}. Grain: {grain}. Căn cứ: {basis}')};")
    for (t, c), (desc, basis) in COLUMNS.items():
        out.append(f"COMMENT ON COLUMN {t}.{c} IS {lit(desc + (f' [{basis}]' if basis else ''))};")
    (V2 / "01b_column_comments.sql").write_text("\n".join(out) + "\n", encoding="utf-8")


# ============================================================================
# 3. EXCEL
# ============================================================================
FONT = "Arial"
NAVY = "1F3A5F"
LAYER_FILL = {"Danh mục": "E8F0FA", "Giao dịch": "FFF4E0", "Phân tích": "E9F5EC"}
thin = Side(style="thin", color="D0D7DE")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 30


def body(cell, wrap=False, bold=False, fill=None, fmt=None, color=None):
    cell.font = Font(name=FONT, size=10, bold=bold, color=color)
    cell.alignment = Alignment(vertical="top", wrap_text=wrap)
    cell.border = BORDER
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    if fmt:
        cell.number_format = fmt


def title(ws, text, sub):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
    ws["A2"] = sub
    ws["A2"].font = Font(name=FONT, size=9, italic=True, color="57606A")


def widths(ws, w):
    for i, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = x


LAYER_TAB = {"Danh mục": "4A7BB7", "Giao dịch": "D08A2E", "Phân tích": "3E8E5A"}
DATA_ROW0 = 15          # dòng đầu tiên của danh sách cột trong sheet bảng
COUNT_RANGE = f"$A${DATA_ROW0}:$A$400"


def xl_value(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if hasattr(v, "as_integer_ratio") and not isinstance(v, int):
        return float(v)
    if isinstance(v, str):
        return v[:80]
    return v


def write_excel(cols, pk, fk, uq, tables, rows, stats, codes, samples):
    wb = Workbook()
    src = (f"Sinh tự động từ catalog PostgreSQL reportapi — bronze.ins_* (scripts/build_docs.py, DOCS_TARGET=volume) ngày {TODAY:%d/%m/%Y}. "
           "Tên bảng ghi theo mô hình logic: ref.X / core.X = bronze.ins_X." if VOLUME else
           f"Sinh tự động từ catalog PostgreSQL (scripts/build_docs.py) ngày {TODAY:%d/%m/%Y}. Số dòng / giá trị mẫu đếm trên bộ dữ liệu dummy sau khi chạy 01 → 03.")
    formula_cells = set()   # (sheet, coordinate) là công thức thật — mọi ô khác ép về văn bản
    sheet_of = {t: t for t in tables}  # tên sheet = schema.bảng (≤ 31 ký tự)
    link_font = Font(name=FONT, size=10, color="0563C1", underline="single")

    def link(cell, sheet, ref="A1"):
        cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'{sheet}'!{ref}", display=str(cell.value))
        cell.font = link_font

    # ---- Hướng dẫn
    ws = wb.active
    ws.title = "Hướng dẫn"
    title(ws, f"DATA DICTIONARY — {DOC_TITLE} (PostgreSQL)", src)
    guide = [
        ("Mục đích", "Mô tả chi tiết các bảng/cột của DỮ LIỆU NGUỒN được sinh ra cho POC doanh thu bảo hiểm (đủ thông tin cho 6 chiều phân tích: Thời gian, Kênh bán, Nghiệp vụ, Sản phẩm, Đơn vị, Khách hàng)."),
        ("Lớp 'Danh mục' (schema ref)", "Danh mục chuẩn hóa theo nguồn public: Luật KDBH 2022, NĐ 46/2023, NĐ 67/2023, TT 67/2023, TT 232/2012, NQ 202/2025, số liệu IAV/MOF."),
        ("Lớp 'Giao dịch' (schema core)", "Hợp đồng → giao dịch → chi tiết phí theo sản phẩm; đồng bảo hiểm; phân bổ doanh thu cho đơn vị."),
        ("Cách tính doanh thu từ dữ liệu nguồn", "premium_vnd × share_pct('OWN')/100 × allocation_pct/100 (VND, chưa VAT); chỉ giao dịch APPROVED; kỳ theo accounting_date."),
        ("Sheet 'Tổng quan bảng'", "1 dòng / bảng. Bấm tên bảng để mở sheet chi tiết của bảng đó. 'Số cột' là công thức đếm từ sheet bảng."),
        ("Sheet theo bảng (vd 'core.policy')", "Mỗi bảng 1 sheet, tên sheet = schema.bảng, màu tab theo lớp. Gồm: (1) thông tin bảng — lớp, mô tả, grain, khóa chính, số dòng, căn cứ; (2) danh sách cột — kiểu dữ liệu, NOT NULL/PK/FK/UNIQUE, mô tả, căn cứ, giá trị mẫu, số giá trị khác nhau, % NULL; (3) khóa ngoại đi ra và bảng tham chiếu tới; (4) 5 dòng dữ liệu mẫu."),
        ("Sheet 'Quan hệ FK'", "Toàn bộ khóa ngoại: bảng/cột con → bảng/cột cha (bấm tên bảng để mở sheet)."),
        ("Sheet 'Quy tắc nghiệp vụ'", "Các quy tắc tính doanh thu và căn cứ pháp lý."),
        ("Sheet 'Kịch bản dữ liệu'", "Các tình huống cài sẵn trong dữ liệu dummy để kiểm thử ETL."),
        ("Sheet 'DM …'", "Giá trị các danh mục mã chính (sản phẩm, kênh/đối tác, loại giao dịch, đơn vị, dòng báo cáo)."),
        ("Màu", "Tab / cột 'Lớp': xanh dương = Danh mục · cam = Giao dịch · xanh lá = Phân tích. Tên cột khóa chính in đậm."),
        ("Lưu ý dữ liệu", "Danh mục doanh nghiệp là Tổng Công ty Bảo hiểm PVI với 47 đơn vị thật (pvi.com.vn/vi/network); 3 đối tác số có công bố hợp tác với PVI mang tên thật (Green SM, ATADI, Fuse); các đối tác khác và DN đồng bảo hiểm ẩn danh. Mọi giao dịch, số tiền, khách hàng là giả lập — không phải số liệu thật của PVI hay của từng đơn vị."),
    ]
    ws.append([])
    ws.append(["Mục", "Nội dung"])
    style_header(ws, 4, 2)
    for k, v in guide:
        ws.append([k, v])
        body(ws.cell(ws.max_row, 1), bold=True)
        body(ws.cell(ws.max_row, 2), wrap=True)
    widths(ws, [32, 120])

    # ---- Tổng quan bảng
    wo = wb.create_sheet("Tổng quan bảng")
    wo.sheet_properties.tabColor = NAVY
    title(wo, "Tổng quan bảng", src)
    hdr = ["STT", "Schema", "Bảng (bấm để mở)", "Lớp", "Mô tả", "Grain (1 dòng là gì)", "Khóa chính", "Số cột", "Số dòng (dummy)", "Căn cứ / chuẩn tham chiếu"]
    wo.append([])
    wo.append(hdr)
    style_header(wo, 4, len(hdr))
    for i, tbl in enumerate(tables, 1):
        s, t = tbl.split(".")
        layer, desc, grain, basis = TABLES[tbl]
        r = wo.max_row + 1
        wo.append([i, s, t, layer, desc, grain, ", ".join(sorted(pk[tbl])), f"=COUNT('{sheet_of[tbl]}'!{COUNT_RANGE})", rows[tbl], basis])
        formula_cells.add(("Tổng quan bảng", f"H{r}"))
        for col in range(1, len(hdr) + 1):
            body(wo.cell(r, col), wrap=col in (5, 6, 10), fill=LAYER_FILL[layer] if col == 4 else None, fmt="#,##0" if col in (8, 9) else None)
        link(wo.cell(r, 3), sheet_of[tbl])
    r = wo.max_row + 1
    wo.cell(r, 3, "TỔNG")
    wo.cell(r, 8, f"=SUM(H5:H{r - 1})")
    wo.cell(r, 9, f"=SUM(I5:I{r - 1})")
    formula_cells.update({("Tổng quan bảng", f"H{r}"), ("Tổng quan bảng", f"I{r}")})
    for col in range(1, len(hdr) + 1):
        body(wo.cell(r, col), bold=True, fmt="#,##0" if col in (8, 9) else None, fill="F6F8FA")
    wo.cell(r + 2, 1, "Ghi chú: 'Số cột' là công thức COUNT trên sheet của từng bảng; 'Số dòng' đếm trên PostgreSQL sau khi nạp dữ liệu dummy.").font = Font(name=FONT, size=9, italic=True)
    wo.freeze_panes = "D5"
    wo.auto_filter.ref = f"A4:{get_column_letter(len(hdr))}{r - 1}"
    widths(wo, [6, 8, 26, 11, 52, 30, 26, 9, 14, 52])

    # ---- Quan hệ FK
    wf = wb.create_sheet("Quan hệ FK")
    title(wf, "Quan hệ khóa ngoại", src)
    wf.append([])
    wf.append(["STT", "Bảng con", "Cột", "→ Bảng cha", "Cột cha", "Ý nghĩa"])
    style_header(wf, 4, 6)
    for i, ((tbl, c), ref) in enumerate(sorted(fk.items(), key=lambda x: (tables.index(x[0][0]), x[0][1])), 1):
        rt, rc = ref.rsplit(".", 1)
        wf.append([i, tbl, c, rt, rc, COLUMNS.get((tbl, c), ("",))[0]])
        for col in range(1, 7):
            body(wf.cell(wf.max_row, col), wrap=col == 6)
        link(wf.cell(wf.max_row, 2), sheet_of[tbl])
        link(wf.cell(wf.max_row, 4), sheet_of[rt])
    wf.freeze_panes = "A5"
    wf.auto_filter.ref = f"A4:F{wf.max_row}"
    widths(wf, [6, 28, 24, 28, 24, 70])

    # ---- Quy tắc + kịch bản
    for name, hdr, data, w in (("Quy tắc nghiệp vụ", ["STT", "Quy tắc", "Diễn giải / công thức", "Căn cứ"], BUSINESS_RULES, [6, 32, 80, 50]),
                               ("Kịch bản dữ liệu", ["STT", "Tình huống", "Nhận diện trong dữ liệu", "Xử lý mong đợi"], SCENARIOS, [6, 42, 56, 52])):
        wsx = wb.create_sheet(name)
        title(wsx, name, src)
        wsx.append([])
        wsx.append(hdr)
        style_header(wsx, 4, len(hdr))
        for i, row in enumerate(data, 1):
            wsx.append([i, *row])
            for col in range(1, len(hdr) + 1):
                body(wsx.cell(wsx.max_row, col), wrap=True, bold=col == 2)
        widths(wsx, w)

    # ---- 1 sheet / bảng
    by_tbl = defaultdict(list)
    for s, t, pos, c, typ, notnull, ident in cols:
        by_tbl[f"{s}.{t}"].append((pos, c, typ, notnull, ident))
    COLHDR = ["STT", "Cột", "Kiểu dữ liệu", "NOT NULL", "Khóa chính", "Khóa ngoại →", "UNIQUE", "Mô tả", "Căn cứ / nguồn",
              "Giá trị mẫu", "Số giá trị khác nhau", "% NULL"]
    label_fill = "F3F4F6"
    for tbl in tables:
        layer, desc, grain, basis = TABLES[tbl]
        sh = wb.create_sheet(sheet_of[tbl])
        sh.sheet_properties.tabColor = LAYER_TAB[layer]
        sh["A1"] = f"{tbl} — {desc}"
        sh["A1"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
        sh["A2"] = "← Về Tổng quan bảng"
        link(sh["A2"], "Tổng quan bảng")
        info = [("Schema", tbl.split(".")[0]), ("Bảng", tbl.split(".")[1]), ("Lớp", layer), ("Mô tả", desc), ("Grain (1 dòng là gì)", grain),
                ("Khóa chính", ", ".join(sorted(pk[tbl])) or "—"), ("Số cột", f"=COUNT({COUNT_RANGE})"),
                ("Số dòng (dummy)", rows[tbl]), ("Căn cứ / chuẩn tham chiếu", basis)]
        for k, (lab, val) in enumerate(info):
            r = 4 + k
            sh.cell(r, 1, lab)
            body(sh.cell(r, 1), bold=True, fill=label_fill)
            sh.merge_cells(start_row=r, start_column=2, end_row=r, end_column=len(COLHDR))
            sh.cell(r, 2, val)
            body(sh.cell(r, 2), wrap=True, fmt="#,##0" if lab in ("Số cột", "Số dòng (dummy)") else None,
                 fill=LAYER_FILL[layer] if lab == "Lớp" else None)
            sh.cell(r, 2).alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            if lab == "Số cột":
                formula_cells.add((sh.title, f"B{r}"))
        hdr_row = DATA_ROW0 - 1
        for col, h in enumerate(COLHDR, 1):
            sh.cell(hdr_row, col, h)
        style_header(sh, hdr_row, len(COLHDR))
        r = hdr_row
        for pos, c, typ, notnull, ident in by_tbl[tbl]:
            r += 1
            d, b = COLUMNS.get((tbl, c), ("", ""))
            null_pct, n_dist, sample = stats[(tbl, c)]
            is_pk = c in pk[tbl]
            vals = [pos, c, typ + (" (identity)" if ident else ""), "✓" if notnull else "", "PK" if is_pk else "",
                    fk.get((tbl, c), ""), "✓" if c in uq[tbl] else "", d, b, sample, n_dist, null_pct]
            for col, v in enumerate(vals, 1):
                sh.cell(r, col, v)
                body(sh.cell(r, col), wrap=col in (6, 8, 9, 10), bold=is_pk and col == 2,
                     fmt="0.0%" if col == 12 else ("#,##0" if col == 11 else None))
            if (tbl, c) in fk:
                link(sh.cell(r, 6), sheet_of[fk[(tbl, c)].rsplit(".", 1)[0]])
        sh.auto_filter.ref = f"A{hdr_row}:{get_column_letter(len(COLHDR))}{r}"

        def section(title_text, header, data_rows, start):
            """Khối phụ bắt đầu từ cột B (cột A chỉ chứa STT của danh sách cột -> công thức COUNT đúng)."""
            sh.cell(start, 2, title_text).font = Font(name=FONT, size=11, bold=True, color=NAVY)
            for j, h in enumerate(header):
                cell = sh.cell(start + 1, 2 + j, h)
                cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor=NAVY)
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                cell.border = BORDER
            rr = start + 1
            for row in data_rows:
                rr += 1
                for j, v in enumerate(row):
                    sh.cell(rr, 2 + j, xl_value(v))
                    body(sh.cell(rr, 2 + j), wrap=True)
            if not data_rows:
                rr += 1
                sh.cell(rr, 2, "(không có)")
                body(sh.cell(rr, 2), color="57606A")
            return rr + 2

        nxt = r + 3
        out_fk = [(c, *fk[(tbl, c)].rsplit(".", 1), COLUMNS.get((tbl, c), ("",))[0]) for _, c, *_ in by_tbl[tbl] if (tbl, c) in fk]
        start_out = nxt
        nxt = section("Khóa ngoại — bảng này tham chiếu tới", ["Cột", "→ Bảng cha", "Cột cha", "Ý nghĩa"], out_fk, nxt)
        for k, row in enumerate(out_fk):
            link(sh.cell(start_out + 2 + k, 3), sheet_of[row[1]])
        in_fk = sorted((t2, c2, ref.rsplit(".", 1)[1], COLUMNS.get((t2, c2), ("",))[0])
                       for (t2, c2), ref in fk.items() if ref.rsplit(".", 1)[0] == tbl)
        start_in = nxt
        nxt = section("Được tham chiếu bởi — bảng con trỏ tới bảng này", ["Bảng con", "Cột", "→ Cột của bảng này", "Ý nghĩa"], in_fk, nxt)
        for k, row in enumerate(in_fk):
            link(sh.cell(start_in + 2 + k, 2), sheet_of[row[0]])
        names, data = samples[tbl]
        section(f"Dữ liệu mẫu — 5 dòng đầu (sắp theo cột '{names[0]}')", names, data, nxt)
        widths(sh, [8, 26, 22, 10, 10, 30, 9, 60, 36, 36, 12, 9] + [16] * max(0, len(names) - 11))

    # ---- Danh mục mã
    for name, (hdrs, data) in codes.items():
        wsx = wb.create_sheet(name)
        title(wsx, name, src)
        wsx.append([])
        wsx.append(hdrs)
        style_header(wsx, 4, len(hdrs))
        for row in data:
            wsx.append([xl_value(v) for v in row])
            for col in range(1, len(hdrs) + 1):
                body(wsx.cell(wsx.max_row, col), wrap=True)
        wsx.freeze_panes = "B5"
        widths(wsx, [max(10, min(48, max(len(str(h)) for h in [hdrs[i]] + [r[i] for r in data]) + 2)) for i in range(len(hdrs))])

    for wsx in wb.worksheets:
        wsx.sheet_view.showGridLines = False
        # chốt chặn: văn bản bắt đầu bằng '=' không được hiểu là công thức
        for row in wsx.iter_rows():
            for cell in row:
                if cell.data_type == "f" and (wsx.title, cell.coordinate) not in formula_cells:
                    cell.data_type = "s"
    wb.calculation.fullCalcOnLoad = True  # Excel tự tính lại công thức khi mở
    out = Path(os.getenv("DD_OUT", OUT_DIR / XLSX_NAME))
    out.parent.mkdir(parents=True, exist_ok=True)  # DD_OUT: ghi ra file khác khi bản chính đang mở trong Excel
    wb.save(out)
    return out


# ============================================================================
# 4. HTML
# ============================================================================
SECTIONS_V2 = [  # id, tiêu đề, file nguồn (tương đối với SRC_DIR)
    ("tong-quan", "Tổng quan & cách chạy", "README.md"),
    ("can-cu", "Căn cứ thiết kế", "DESIGN_RATIONALE.md"),
    ("logic-sinh", "Logic sinh dữ liệu", "GENERATION_LOGIC.md"),
    ("hoi-dap", "Hỏi đáp: Tại sao?", "HOI_DAP_TAI_SAO.md"),
    ("phap-ly", "Nguồn pháp lý", "sources/regulations.md"),
    ("thi-truong", "Số liệu thị trường", "sources/market_data.md"),
    ("quoc-te", "Chuẩn quốc tế", "sources/international_standards.md"),
]
SECTIONS_VOL = [
    ("tong-quan", "Tổng quan & cách chạy", "README.md"),
    ("can-cu-tham-so", "Căn cứ tham số", "calibration/README.md"),
    ("can-cu", "Căn cứ thiết kế mô hình (v2)", "DESIGN_RATIONALE.md"),
    ("schema-change", "Mô phỏng thay đổi schema", "schema_change/README.md"),
    ("phap-ly", "Nguồn pháp lý", "sources/regulations.md"),
]
SECTIONS = SECTIONS_VOL if VOLUME else SECTIONS_V2
LINK_MAP_VOL = {"README.md": "#tong-quan", "calibration/README.md": "#can-cu-tham-so", "schema_change/README.md": "#schema-change",
                "DESIGN_RATIONALE.md": "#can-cu", "sources/": "#phap-ly",
                "sources/regulations.md": "#phap-ly", "regulations.md": "#phap-ly",
                "GENERATION_LOGIC.md": "../GENERATION_LOGIC.md", "../GENERATION_LOGIC.md": "../GENERATION_LOGIC.md"}
LINK_MAP = {"README.md": "#tong-quan", "DESIGN_RATIONALE.md": "#can-cu", "GENERATION_LOGIC.md": "#logic-sinh", "HOI_DAP_TAI_SAO.md": "#hoi-dap", "sources/regulations.md": "#phap-ly",
            "sources/market_data.md": "#thi-truong", "sources/international_standards.md": "#quoc-te",
            "regulations.md": "#phap-ly", "market_data.md": "#thi-truong", "international_standards.md": "#quoc-te",
            "sources/": "#phap-ly"}


if VOLUME:
    LINK_MAP = LINK_MAP_VOL


def md_to_html(text):
    text = re.sub(r"^# .*\n", "", text, count=1)  # bỏ tiêu đề H1 — đã có tiêu đề section
    h = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    h = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', lambda m: f'<pre class="mermaid">{m.group(1)}</pre>', h, flags=re.S)

    def fix_link(m):
        href, label = m.group(1), m.group(2)
        if href.startswith(("http", "#")):
            return f'<a href="{href}" target="_blank" rel="noopener">{label}</a>' if href.startswith("http") else m.group(0)
        if href in LINK_MAP:
            return f'<a href="{LINK_MAP[href]}">{label}</a>'
        if "Mapping_v2_PIAS" in href:  # tài liệu nội bộ — không gắn link
            return f"<span>{label}</span>"
        return f'<a href="../{href}">{label}</a>'
    h = re.sub(r'<a href="([^"]+)">(.*?)</a>', fix_link, h)
    h = h.replace("<h2>", '<h3 class="h2">').replace("</h2>", "</h3>").replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    return h


def write_html(cols, pk, fk, uq, tables, rows, stats, kpi):
    n_policy, n_txn, n_fact, rev25, n_cust = kpi
    sec_html, toc = [], []
    for sid, ttl, f in SECTIONS:
        sec_html.append(f'<section id="{sid}"><h2>{ttl}</h2>{md_to_html((SRC_DIR / f).read_text(encoding="utf-8"))}</section>')
        toc.append((sid, ttl))

    # sơ đồ quan hệ lớp giao dịch (core) và các danh mục được tham chiếu — dựng từ FK thật
    core_rel = [f'    {ref.rsplit(".", 1)[0].split(".")[1]} ||--o{{ {tbl.split(".")[1]} : "{c}"' for (tbl, c), ref in fk.items() if tbl.startswith("core.")]
    star = "erDiagram\n" + "\n".join(sorted(set(core_rel)))

    by_tbl = defaultdict(list)
    for s, t, pos, c, typ, notnull, ident in cols:
        by_tbl[f"{s}.{t}"].append((pos, c, typ, notnull, ident))
    overview = "".join(
        f'<tr><td><span class="tag l{["Danh mục", "Giao dịch", "Phân tích"].index(TABLES[t][0])}">{TABLES[t][0]}</span></td>'
        f'<td><a href="#t-{t.replace(".", "-")}"><code>{t}</code></a></td><td>{html.escape(TABLES[t][1])}</td>'
        f'<td>{html.escape(TABLES[t][2])}</td><td class="num">{len(by_tbl[t])}</td><td class="num">{rows[t]:,}</td></tr>'
        for t in tables)
    details = []
    for t in tables:
        trs = []
        for pos, c, typ, notnull, ident in by_tbl[t]:
            desc, basis = COLUMNS.get((t, c), ("", ""))
            null_pct, n_dist, sample = stats[(t, c)]
            badges = ("<b class='b pk'>PK</b>" if c in pk[t] else "") + (f"<b class='b fk' title='{fk[(t, c)]}'>FK</b>" if (t, c) in fk else "") \
                + ("<b class='b uq'>UQ</b>" if c in uq[t] else "") + ("" if notnull else "<b class='b nl'>NULL</b>")
            ref = f"<div class='ref'>→ <code>{fk[(t, c)]}</code></div>" if (t, c) in fk else ""
            search = " ".join([t, TABLES[t][1], c, desc, basis]).lower()
            trs.append(f"<tr data-s='{html.escape(search)}'><td class='num'>{pos}</td>"
                       f"<td><code>{c}</code> {badges}{ref}</td><td><code class='ty'>{typ}{' identity' if ident else ''}</code></td>"
                       f"<td>{html.escape(desc)}{f'<div class=basis>{html.escape(basis)}</div>' if basis else ''}</td>"
                       f"<td class='sm'>{html.escape(sample)}</td><td class='num'>{n_dist:,}</td><td class='num'>{null_pct:.0%}</td></tr>")
        layer, desc, grain, basis = TABLES[t]
        details.append(f"""<details id="t-{t.replace('.', '-')}" class="tbl"><summary><code>{t}</code><span>{html.escape(desc)}</span>
<em>{rows[t]:,} dòng · {len(by_tbl[t])} cột</em></summary>
<p class="meta"><b>Grain:</b> {html.escape(grain)} · <b>Căn cứ:</b> {html.escape(basis)}</p>
<div class="tw"><table class="dd"><thead><tr><th>#</th><th>Cột</th><th>Kiểu</th><th>Mô tả</th><th>Giá trị mẫu</th><th>Khác nhau</th><th>NULL</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div></details>""")
    rules = "".join(f"<tr><td><b>{html.escape(a)}</b></td><td>{html.escape(b)}</td><td>{html.escape(c)}</td></tr>" for a, b, c in BUSINESS_RULES)
    scen = "".join(f"<tr><td><b>{html.escape(a)}</b></td><td>{html.escape(b)}</td><td>{html.escape(c)}</td></tr>" for a, b, c in SCENARIOS)
    dd = f"""<section id="data-dictionary"><h2>Data dictionary</h2>
<p>Sinh tự động từ catalog PostgreSQL ngày {TODAY:%d/%m/%Y}{PHYS_NOTE}; bản Excel chi tiết: <a href="{XLSX_NAME}">{XLSX_NAME}</a>.</p>
<h3 class="h2">Sơ đồ quan hệ lớp giao dịch (core)</h3><pre class="mermaid">{html.escape(star)}</pre>
<h3 class="h2">Danh sách bảng</h3>
<div class="tw"><table><thead><tr><th>Lớp</th><th>Bảng</th><th>Mô tả</th><th>Grain</th><th>Cột</th><th>Dòng</th></tr></thead><tbody>{overview}</tbody></table></div>
<h3 class="h2">Quy tắc nghiệp vụ</h3><div class="tw"><table><thead><tr><th>Quy tắc</th><th>Diễn giải</th><th>Căn cứ</th></tr></thead><tbody>{rules}</tbody></table></div>
<h3 class="h2">Kịch bản dữ liệu kiểm thử</h3><div class="tw"><table><thead><tr><th>Tình huống</th><th>Nhận diện</th><th>Xử lý mong đợi</th></tr></thead><tbody>{scen}</tbody></table></div>
<h3 class="h2">Chi tiết cột</h3>
<div class="tools"><input id="q" type="search" placeholder="Lọc cột theo tên, mô tả, căn cứ… (vd: revenue, TT 67, đồng bảo hiểm)" aria-label="Lọc cột">
<button type="button" id="exp">Mở tất cả</button><button type="button" id="col">Thu gọn</button></div>
{''.join(details)}</section>"""
    toc.insert(3, ("data-dictionary", "Data dictionary"))

    appendix = "".join(
        f'<details class="code"><summary><code>{f}</code></summary><pre><code>{html.escape((V2 / f).read_text(encoding="utf-8"))}</code></pre></details>'
        for f in ("01_ddl.sql",))
    if VOLUME:
        appendix = ("<p>Trên <code>reportapi</code>: mọi bảng <code>ref.X</code> / <code>core.X</code> của DDL dưới đây nằm ở "
                    "<code>bronze.ins_X</code>; thêm 3 cột <code>ins_customer.gender</code>, <code>ins_customer.birth_year</code>, "
                    "<code>ins_policy.prev_policy_no</code> (gen_volume.py · EXTRA_DDL).</p>" + appendix)
    sec_html.insert(3, dd)
    sec_html.append(f'<section id="phu-luc"><h2>Phụ lục SQL (PostgreSQL)</h2><p>Dữ liệu (<code>02_data.sql</code>) không nhúng vì dung lượng.</p>{appendix}</section>')
    toc.append(("phu-luc", "Phụ lục SQL"))
    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in toc)

    page = TEMPLATE.format(
        date=f"{TODAY:%d/%m/%Y}", nav=nav, body="".join(sec_html), doc_title=DOC_TITLE, intro=INTRO,
        kpis="".join(f'<div class="kpi"><b>{v}</b><span>{k}</span></div>' for k, v in [
            (KPI_LABEL, f"{rev25:,.0f}"), ("Hợp đồng", f"{n_policy:,}"), ("Giao dịch", f"{n_txn:,}"),
            ("Dòng phí theo SP", f"{n_fact:,}"), ("Khách hàng", f"{n_cust:,}"), ("Bảng / cột", f"{len(tables)} / {len(cols)}")]))
    out = OUT_DIR / HTML_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


PHYS_NOTE = " (reportapi · bronze.ins_*; tên bảng ghi theo mô hình logic ref.X / core.X)" if VOLUME else ""
INTRO = ("Dữ liệu nguồn giả lập ở quy mô vận hành (&gt; 50.000 giao dịch/ngày, 01/08 – 30/09/2026) trên PostgreSQL "
         "<code>reportapi</code>, schema <code>bronze</code>, bảng <code>ins_*</code> — dùng nguyên mô hình v2; mọi tham số thời gian có nhãn căn cứ "
         "([CHÍNH THỨC] / [DATASET] / [NGUỒN THAY THẾ] / [QUY ƯỚC] / [ƯỚC TÍNH])." if VOLUME else
         "Dữ liệu nguồn giả lập cho POC doanh thu bảo hiểm (đủ 6 chiều: Thời gian · Kênh bán · Nghiệp vụ · Sản phẩm · Đơn vị · Khách hàng). "
         "Mô hình 2 lớp <code>ref</code> (danh mục) → <code>core</code> (giao dịch) trên PostgreSQL; mọi quy tắc và con số có căn cứ public.")
TEMPLATE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{doc_title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fbfaf7;--panel:#ffffff;--ink:#1b2430;--muted:#5b6673;--line:#e3e0d8;--accent:#0f5c63;--accent2:#b5651d;--code:#f2efe8;
--l0:#e6eef7;--l1:#fbefdc;--l2:#e4f2e8;--mono:'JetBrains Mono',ui-monospace,Consolas,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#12161b;--panel:#191e25;--ink:#e6e8eb;--muted:#9aa4af;--line:#2a313a;--accent:#5cc3c9;--accent2:#e2a15b;--code:#20262e;--l0:#1d2c3d;--l1:#3a2d18;--l2:#1d3326}}}}
:root[data-theme=dark]{{--bg:#12161b;--panel:#191e25;--ink:#e6e8eb;--muted:#9aa4af;--line:#2a313a;--accent:#5cc3c9;--accent2:#e2a15b;--code:#20262e;--l0:#1d2c3d;--l1:#3a2d18;--l2:#1d3326}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth;scroll-padding-top:16px}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 'Be Vietnam Pro',system-ui,sans-serif}}
a{{color:var(--accent)}}main p,main li,main td,main blockquote{{overflow-wrap:anywhere}}code{{font-family:var(--mono);font-size:.86em;background:var(--code);padding:.1em .35em;border-radius:4px}}
.wrap{{display:grid;grid-template-columns:250px minmax(0,1fr);max-width:1400px;margin:0 auto}}
nav{{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 18px;border-right:1px solid var(--line)}}
nav .brand{{font-weight:700;font-size:15px;line-height:1.3;margin-bottom:4px}}nav .sub{{color:var(--muted);font-size:12px;margin-bottom:20px}}
nav a{{display:block;padding:7px 10px;margin:2px 0;border-radius:6px;color:var(--ink);text-decoration:none;font-size:14px}}
nav a:hover,nav a.on{{background:var(--code);color:var(--accent)}}
nav button{{margin-top:18px;font:inherit;font-size:12px;background:none;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:5px 10px;cursor:pointer}}
main{{padding:36px clamp(16px,4vw,56px) 80px;min-width:0}}
header h1{{font-size:clamp(26px,3.4vw,40px);line-height:1.15;margin:0 0 10px;letter-spacing:-.01em}}
header p{{color:var(--muted);max-width:820px;margin:0 0 22px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin-bottom:12px}}
.kpi{{background:var(--panel);padding:14px 16px}}.kpi b{{display:block;font-size:22px;font-variant-numeric:tabular-nums}}.kpi span{{color:var(--muted);font-size:12.5px}}
.note{{font-size:12.5px;color:var(--muted);margin:0 0 8px}}
section{{border-top:1px solid var(--line);margin-top:44px;padding-top:8px}}
section>h2{{font-size:26px;margin:18px 0 8px;color:var(--accent)}}h3.h2{{font-size:19px;margin:30px 0 8px}}h3{{font-size:16px;margin:22px 0 6px}}
.tw{{overflow-x:auto;margin:10px 0 16px;border:1px solid var(--line);border-radius:8px;background:var(--panel)}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}}th,td{{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:var(--code);font-weight:600;position:sticky;top:0}}tr:last-child td{{border-bottom:0}}td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
pre{{background:var(--code);padding:14px;border-radius:8px;overflow:auto;font-size:12.5px;line-height:1.5}}pre code{{background:none;padding:0}}
pre.mermaid{{background:var(--panel);border:1px solid var(--line);text-align:center}}
blockquote{{margin:12px 0;padding:8px 14px;border-left:3px solid var(--accent2);background:var(--panel);color:var(--muted)}}
.tag{{font-size:11.5px;padding:2px 8px;border-radius:99px;white-space:nowrap}}.l0{{background:var(--l0)}}.l1{{background:var(--l1)}}.l2{{background:var(--l2)}}
.tools{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 14px}}.tools input{{flex:1;min-width:220px;font:inherit;font-size:14px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink)}}
.tools button{{font:inherit;font-size:13px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);cursor:pointer}}
details.tbl{{border:1px solid var(--line);border-radius:8px;margin:8px 0;background:var(--panel)}}
details.tbl summary{{cursor:pointer;padding:10px 14px;display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}}
details.tbl summary span{{flex:1;min-width:200px}}details.tbl summary em{{color:var(--muted);font-style:normal;font-size:12.5px}}
details.tbl .meta{{margin:0 14px;font-size:13px;color:var(--muted)}}details.tbl .tw{{margin:10px 14px 14px}}
table.dd{{min-width:880px}}table.dd td:nth-child(2){{white-space:nowrap}}.b{{font-size:10px;font-weight:600;padding:1px 5px;border-radius:4px;margin-left:3px;vertical-align:1px}}
.pk{{background:var(--accent);color:var(--panel)}}.fk{{background:var(--accent2);color:var(--panel)}}.uq{{border:1px solid var(--accent)}}.nl{{border:1px solid var(--line);color:var(--muted)}}
.ref{{font-size:11.5px;color:var(--muted);margin-top:2px}}.basis{{font-size:12px;color:var(--muted);margin-top:3px}}.sm{{font-size:12px;color:var(--muted);max-width:260px}}
code.ty{{white-space:nowrap}}details.code{{margin:8px 0}}details.code summary{{cursor:pointer;padding:6px 0}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
@media (max-width:960px){{.wrap{{grid-template-columns:1fr}}nav{{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);padding:16px;display:flex;flex-wrap:wrap;gap:4px}}nav .brand,nav .sub{{width:100%;margin:0}}nav a{{padding:5px 9px;font-size:13px}}}}
@media print{{nav,.tools{{display:none}}.wrap{{display:block}}section{{break-inside:auto}}details{{border:0}}body{{font-size:12px}}}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style></head><body><div class="wrap">
<nav aria-label="Mục lục"><div class="brand">{doc_title}</div><div class="sub">Tài liệu tổng hợp · {date}</div>{nav}
<button type="button" id="theme" aria-label="Đổi giao diện sáng/tối">Sáng / Tối</button></nav>
<main><header><h1>Dữ liệu nguồn dummy — POC Doanh thu bảo hiểm</h1>
<p>{intro}</p>
<div class="kpis">{kpis}</div><p class="note">Số liệu tính trên bộ dữ liệu giả lập: Tổng Công ty Bảo hiểm PVI và 47 đơn vị thật, giao dịch giả lập ở đúng quy mô doanh thu PVI.</p></header>
{body}
</main></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
(function(){{
  var root=document.documentElement;
  try{{var t=localStorage.getItem('poc-theme');if(t)root.setAttribute('data-theme',t);}}catch(e){{}}
  var dark=function(){{return root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);}};
  if(window.mermaid){{mermaid.initialize({{startOnLoad:true,theme:dark()?'dark':'neutral',securityLevel:'strict'}});}}
  document.getElementById('theme').onclick=function(){{var n=dark()?'light':'dark';root.setAttribute('data-theme',n);try{{localStorage.setItem('poc-theme',n);}}catch(e){{}}}};
  var q=document.getElementById('q');
  if(q)q.addEventListener('input',function(){{var v=q.value.trim().toLowerCase();
    document.querySelectorAll('details.tbl').forEach(function(d){{var hit=0;d.querySelectorAll('tbody tr').forEach(function(r){{var ok=!v||r.dataset.s.indexOf(v)>-1;r.style.display=ok?'':'none';if(ok)hit++;}});
      d.style.display=hit?'':'none';if(v)d.open=hit>0;}});}});
  var all=function(o){{document.querySelectorAll('details.tbl').forEach(function(d){{d.open=o;}});}};
  document.getElementById('exp').onclick=function(){{all(true);}};document.getElementById('col').onclick=function(){{all(false);}};
  window.addEventListener('beforeprint',function(){{document.querySelectorAll('details').forEach(function(d){{d.open=true;}});}});
  var links=[].slice.call(document.querySelectorAll('nav a'));
  var io=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{links.forEach(function(a){{a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id);}});}}}});}},{{rootMargin:'0px 0px -70% 0px'}});
  document.querySelectorAll('main section').forEach(function(s){{io.observe(s);}});
}})();
</script></body></html>"""


if __name__ == "__main__":
    if VOLUME:
        srv, uri = None, os.environ["PG_URI"]          # đọc trực tiếp, không tạo DB / không ghi 01b
    else:
        write_comments()
        srv, uri = start_db()
    with psycopg.connect(uri) as conn:
        cols, pk, fk, uq, tables, rows, stats, codes, kpi, samples = read_catalog(conn)
    missing = [f"{s}.{t}.{c}" for s, t, _, c, *_ in cols if (f"{s}.{t}", c) not in COLUMNS]
    extra = [f"{t}.{c}" for t, c in COLUMNS if not any(f"{s}.{tt}" == t and cc == c for s, tt, _, cc, *_ in cols)]
    print("cột thiếu mô tả:", missing or "không")
    print("mô tả thừa (không có cột):", extra or "không")
    print("Excel:", write_excel(cols, pk, fk, uq, tables, rows, stats, codes, samples))
    print("HTML :", write_html(cols, pk, fk, uq, tables, rows, stats, kpi))
    print(f"{len(tables)} bảng, {len(cols)} cột, {len(fk)} FK")
