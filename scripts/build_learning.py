r"""Sinh tài liệu học 'Logic sinh dữ liệu & căn cứ' từ scripts/learning_meta.py.

Chạy:  python scripts/build_learning.py   →  docs/Logic_Sinh_Du_Lieu.html
Số liệu ở mục 'Kết quả' được ĐO TRỰC TIẾP bằng cách chạy bộ sinh build_v2.py trong bộ nhớ
(không ghi lại 02_data.sql), nên luôn khớp với code hiện tại.
"""
import datetime as dt
import json
import html
import sys
from collections import Counter, defaultdict
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build_v2 as b  # noqa: E402
from learning_meta import DATASETS, LIMITS, NOT_USED, PARAMS, QUIZ, SOURCES, STEPS, TAGS  # noqa: E402
from why_meta import PAGES, WHY  # noqa: E402

MD_OUT = HERE.parent / "HOI_DAP_TAI_SAO.md"
TARGETS_2025 = {k: float(v) / 1e9 for k, v in b.group_targets(2025).items()}

OUT = HERE.parent / "docs" / "Logic_Sinh_Du_Lieu.html"
DB_SNAPSHOT = HERE.parent / "docs" / "db_snapshot.json"   # số đo trên reportapi (measure_db.py)
e = html.escape
SRC = {s[0]: s for s in SOURCES}
GROUP_NAME = {g[0]: g[1] for g in b.PRODUCT_GROUPS}
POC = {"TNDS_BB": "XE", "VCX": "XE", "HOC_SINH": "CON_NGUOI", "DU_LICH": "CON_NGUOI", "SINH_MANG": "CON_NGUOI",
       "SUC_KHOE": "CON_NGUOI", "TAI_SAN": "TAI_SAN", "CHAY_NO": "TAI_SAN"}
QUARTER_PVI = {2024: [31.5, 21.5, 26.6, 20.5], 2025: [29.7, 24.1, 24.8, 21.4]}
CHANNEL_REF = {"DIEN_TU": "≈ 6% (2024, BCTN PVI) → ≈ 10% (2025, suy ra từ quý I tăng 1,8 lần)", "MOI_GIOI": "Thị trường 13,5%; PVI giả định 15–20%",
               "BANCA": "Giả định 5–8%", "TRUC_TIEP": "PVI thiên khách doanh nghiệp", "NULL": "Dữ liệu bẩn có chủ đích (P62)"}


def validate():
    ids = [p["id"] for p in PARAMS]
    assert len(ids) == len(set(ids)), "trùng id tham số"
    for p in PARAMS:
        for t in p["tags"]:
            assert t in TAGS, (p["id"], t)
        for s in p["src"]:
            assert s in SRC, (p["id"], s)
        if "ASSUME" in p["tags"]:
            assert p.get("impact") and p["impact"][1], f"{p['id']}: giả định phải có 'impact'"
    for d in DATASETS:
        assert d in SRC
    ids = {p["id"] for p in PARAMS}
    for w in WHY:
        for r, _ in w["refs"]:
            assert r in SRC, (w["q"], r)
        for p in w["params"]:
            assert p in ids, (w["q"], p)
    for k in PAGES:
        assert k in SRC, k


# ---------------------------------------------------------------- đo trên bộ sinh
def measure():
    g = b.Gen()
    g.run()
    T = g.tables()
    pol = {p["policy_id"]: p for p in g.policies}
    txn = {t["txn_id"]: t for t in T["core.policy_transaction"]}
    grp = {p[0]: p[2] for p in b.PRODUCTS}
    res = {}
    for year in b.YEARS:
        by_g, by_q, by_ch, by_co, per_pol = (defaultdict(D) for _ in range(5))
        cross, sdbs, shift = defaultdict(D), defaultdict(D), defaultdict(D)
        for c in T["core.transaction_coverage"]:
            t = txn[c["txn_id"]]
            p = pol[t["policy_id"]]
            own = next(s for i, r, s in p["_coins"] if i == "OWN") / 100
            rev = D(c["premium_vnd"]) * own
            cg = grp[c["product_code"]]
            if t["txn_type_code"] in ("NEW", "RENEW") and t["txn_date"].year == year and t["accounting_date"].year > year and t["status"] == "APPROVED":
                shift[cg] += rev
            if t["status"] != "APPROVED" or t["accounting_date"].year != year:
                continue
            by_g[cg] += rev
            by_q[(t["accounting_date"].month - 1) // 3] += rev
            by_ch[p["channel_code"] or "NULL"] += rev
            per_pol[p["policy_id"]] += rev
            for co, _, s in p["_alloc"]:
                by_co[co] += rev * s / 100
            if p["_group"] != cg:
                cross[(p["_group"], cg)] += rev
            if t["txn_type_code"] not in ("NEW", "RENEW"):
                sdbs[cg] += rev
        tot = sum(by_g.values())
        vals = sorted(per_pol.values(), reverse=True)
        res[year] = dict(tot=tot, target=b.group_targets(year), group=by_g, quarter=[by_q[i] / tot * 100 for i in range(4)],
                         channel={k: v / tot * 100 for k, v in by_ch.items()}, company=by_co,
                         poc={k: sum(v for g2, v in by_g.items() if POC[g2] == k) / tot * 100 for k in ("TAI_SAN", "CON_NGUOI", "XE")},
                         top10=sum(vals[:len(vals) // 10]) / sum(vals) * 100, top1=sum(vals[:len(vals) // 100]) / sum(vals) * 100,
                         cross=cross, sdbs=sdbs, shift=shift)
    # bán chéo: khách định danh (bỏ 'khách lẻ theo bảng kê') có >= 2 nhóm sản phẩm
    agg = {c["customer_code"] for c in g.customers if c["is_aggregated_retail"]}
    cust_groups = defaultdict(set)
    for p in g.policies:
        if p["customer_code"] not in agg:
            cust_groups[p["customer_code"]].add(p["_group"])
    res["xsell"] = sum(len(v) >= 2 for v in cust_groups.values()) / len(cust_groups) * 100
    # phân khúc khách hàng 2025: % số hợp đồng và % doanh thu
    cust = {c["customer_code"]: c for c in g.customers}
    segkey = lambda p: "KHACH_LE_GOP" if cust[p["customer_code"]]["is_aggregated_retail"] else cust[p["customer_code"]]["segment_code"]
    seg_n, seg_r = defaultdict(int), defaultdict(D)
    for p in g.policies:
        if p["issue_date"].year == 2025:
            seg_n[segkey(p)] += 1
    for c in T["core.transaction_coverage"]:
        t = txn[c["txn_id"]]
        if t["status"] != "APPROVED" or t["accounting_date"].year != 2025:
            continue
        p = pol[t["policy_id"]]
        seg_r[segkey(p)] += D(c["premium_vnd"]) * next(s for i, r, s in p["_coins"] if i == "OWN") / 100
    tn, tr = sum(seg_n.values()), sum(seg_r.values())
    res["seg"] = sorted(((k, seg_n[k] / tn * 100, float(seg_r[k] / tr * 100)) for k in seg_r), key=lambda x: -x[2])
    res["rows"] = {k: len(v) for k, v in T.items() if k.startswith("core.") or k == "ref.customer"}
    res["txn"] = Counter(t["txn_type_code"] for t in T["core.policy_transaction"])
    res["status"] = Counter(t["status"] for t in T["core.policy_transaction"])
    return res


# ---------------------------------------------------------------- render
def ty(v):
    return f"{float(v) / 1e9:,.1f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def pct(v, nd=1):
    return f"{float(v):.{nd}f}".replace(".", ",")


def pill(t):
    return f'<span class="tag t-{t}" title="{e(TAGS[t][1])}">{e(TAGS[t][0])}</span>'


def src_links(ids):
    out = []
    for i in ids:
        _, _, name, url, _ = SRC[i]
        lab = f'<b>{i}</b> {e(name)}'
        out.append(f'<a href="#src-{i}">{lab}</a>')
    return "<br>".join(out)


def target_tree(m):
    p = b.PVI_LOB_PREMIUM
    rows = []
    spec = [
        ("SUC_KHOE", "Con người × 75%", ["FIN", "ASSUME"], "P20, P22"), ("SINH_MANG", "Con người × 15%", ["FIN", "ASSUME"], "P20, P22"),
        ("DU_LICH", "Con người × 5%", ["FIN", "ASSUME"], "P20, P22"), ("HOC_SINH", "Con người × 5%", ["FIN", "ASSUME"], "P20, P22"),
        ("TNDS_BB", "Xe × 24% (IAV)", ["FIN", "DERIVED"], "P20, P23"), ("VCX", "Xe × 76% (IAV)", ["FIN", "DERIVED"], "P20, P23"),
        ("CHAY_NO", "= Cháy nổ", ["FIN"], "P20"), ("TAI_SAN", "Tài sản & thiệt hại × 50%", ["FIN", "ASSUME"], "P20, P21"),
    ]
    for g, f, tags, ref in spec:
        rows.append(f"<tr><td>{e(GROUP_NAME[g])}</td><td>{e(f)}</td><td class=num>{ty(m[2024]['target'][g])}</td>"
                    f"<td class=num>{ty(m[2025]['target'][g])}</td><td>{''.join(pill(t) for t in tags)}</td><td>{ref}</td></tr>")
    t25 = sum(m[2025]["target"].values())
    direct = (p[2025]["CON_NGUOI"] + p[2025]["XE"] + p[2025]["CHAY_NO"]) * D("1e9")
    rows.append(f"<tr class=tot><td>Tổng</td><td></td><td class=num>{ty(sum(m[2024]['target'].values()))}</td><td class=num>{ty(t25)}</td><td></td><td></td></tr>")
    return "".join(rows), direct / t25 * 100


def registry():
    by_step = defaultdict(list)
    for p in PARAMS:
        by_step[p["step"]].append(p)
    out = []
    for sid, title, code, _ in STEPS:
        out.append(f'<tr class="stephead"><th colspan="6">{sid} · {e(title)} <span>build_v2.py:{e(code)}</span></th></tr>')
        for p in by_step[sid]:
            imp = ""
            if p.get("impact"):
                lvl, txt = p["impact"]
                imp = f'<span class="lvl l-{lvl}">{e(lvl)}</span> {e(txt)}'
            text = " ".join([p["id"], p["name"], p["value"], p["why"]]).lower()
            out.append(f'<tr class="pr" data-tags="{" ".join(p["tags"])}" data-text="{e(text)}" id="{p["id"]}">'
                       f'<td class="pid">{p["id"]}</td><td><b>{e(p["name"])}</b><div class="val">{e(p["value"])}</div>'
                       f'<div class="code">build_v2.py:{e(p["code"])}</div></td>'
                       f'<td>{"".join(pill(t) for t in p["tags"])}</td><td class="why">{e(p["why"])}</td>'
                       f'<td class="srcs">{src_links(p["src"]) or "<span class=muted>—</span>"}</td><td class="imp">{imp}</td></tr>')
    return "".join(out)


def results(m):
    g25, g24 = m[2025], m[2024]
    rows = []
    for g in [x[0] for x in b.PRODUCT_GROUPS]:
        cells = []
        for y in (g24, g25):
            a, t = y["group"][g], y["target"][g]
            d = (a / t - 1) * 100
            cls = "bad" if abs(d) > 3 else ""
            cells.append(f"<td class=num>{ty(t)}</td><td class=num>{ty(a)}</td><td class='num {cls}'>{'+' if d >= 0 else ''}{pct(d)}%</td>")
        rows.append(f"<tr><td>{e(GROUP_NAME[g])}</td>{''.join(cells)}</tr>")
    tot = []
    for y in (g24, g25):
        t, a = sum(y["target"].values()), y["tot"]
        tot.append(f"<td class=num>{ty(t)}</td><td class=num>{ty(a)}</td><td class=num>{pct((a / t - 1) * 100)}%</td>")
    rows.append(f"<tr class=tot><td>Tổng</td>{''.join(tot)}</tr>")
    grp_tbl = "".join(rows)

    p = b.PVI_LOB_PREMIUM[2025]
    pub_ts = p["CHAY_NO"] + p["TAI_SAN_THIET_HAI"] * b.PROPERTY_SHARE_OF_PD
    pub_tot = pub_ts + p["CON_NGUOI"] + p["XE"]
    mix = "".join(f"<tr><td>{n}</td><td class=num>{pct(g25['poc'][k])}%</td><td class=num>{pct(v / pub_tot * 100)}%</td><td>{tg}</td></tr>"
                  for k, n, v, tg in [("TAI_SAN", "Tài sản (gồm cháy nổ)", pub_ts, pill("FIN") + pill("ASSUME")),
                                      ("CON_NGUOI", "Con người", p["CON_NGUOI"], pill("FIN")), ("XE", "Xe", p["XE"], pill("FIN"))])
    q = "".join(f"<tr><td>{y}</td>" + "".join(f"<td class=num>{pct(a)}%<small>{pct(r)}%</small></td>" for a, r in zip(m[y]['quarter'], QUARTER_PVI[y])) + "</tr>"
                for y in b.YEARS)
    ch_name = {c[0]: c[1] for c in b.CHANNELS} | {"NULL": "(để trống)"}
    ch = "".join(f"<tr><td>{e(ch_name[k])}</td><td class=num>{pct(g24['channel'].get(k, 0))}%</td><td class=num>{pct(v)}%</td><td>{e(CHANNEL_REF.get(k, ''))}</td></tr>"
                 for k, v in sorted(g25["channel"].items(), key=lambda x: -x[1]))
    # nguyên nhân lệch 2025
    cause = []
    for (pg, cg), v in sorted(g25["cross"].items(), key=lambda x: -x[1]):
        cause.append(f"<li>Bán kèm: hợp đồng {e(GROUP_NAME[pg])} có kèm sản phẩm thuộc {e(GROUP_NAME[cg])} — {ty(v)} tỷ được báo cáo ở {e(GROUP_NAME[cg])}, nhưng khi hiệu chỉnh lại được tính cho {e(GROUP_NAME[pg])} (P59).</li>")
    sd = sum(g25["sdbs"].values())
    sh = sum(g25["shift"].values())
    cause.append(f"<li>SĐBS, hoàn phí, hủy năm 2025 (ròng): {ty(sd)} tỷ (P70–P71).</li>")
    cause.append(f"<li>Đơn cấp năm 2025 nhưng hiệu lực từ 2026, doanh thu chuyển sang 2026: {ty(sh)} tỷ (P66).</li>")
    cause.append("<li>Ngược lại, đơn cấp cuối 2024 hiệu lực 2025 được cộng vào 2025; hiệu chỉnh chạy 1 vòng nên không bù hết.</li>")
    cause.append("<li>Năm 2024 là năm đầu: không có đơn năm trước chuyển sang, trong khi đơn mua trước ngày hiệu lực (du lịch mua trước chuyến đi 0–60 ngày) đẩy doanh thu sang năm sau — vì vậy du lịch 2024 thấp hơn mục tiêu (P61).</li>")
    rows_tbl = "".join(f"<tr><td><code>{k}</code></td><td class=num>{v:,}</td></tr>".replace(",", ".") for k, v in m["rows"].items())
    tx = ", ".join(f"{k} {v:,}".replace(",", ".") for k, v in m["txn"].most_common())
    st = ", ".join(f"{k} {v:,}".replace(",", ".") for k, v in m["status"].most_common())
    kpi = [(pct(g25["top10"]) + "%", "doanh thu 2025 nằm ở 10% hợp đồng lớn nhất"), (pct(g25["top1"]) + "%", "nằm ở 1% hợp đồng lớn nhất"),
           (ty(g25["company"]["HO"]) + " tỷ", "doanh thu Khối Trụ sở 2025"), (ty(g25["company"]["DGT"]) + " tỷ", "doanh thu Trung tâm KD số 2025"),
           (pct(m["xsell"]) + "%", "khách định danh có ≥ 2 nhóm sản phẩm (bán chéo, P38)")]
    kpis = "".join(f"<div class=kpi><b>{a}</b><span>{e(t)}</span></div>" for a, t in kpi)
    segname = {s[0]: s[1] for s in b.SEGMENTS} | {"KHACH_LE_GOP": "Khách lẻ theo bảng kê (cá nhân mua qua đối tác)"}
    seg = "".join(f"<tr><td>{e(segname[k])}</td><td class=num>{pct(n)}%</td><td class=num>{pct(r)}%</td></tr>" for k, n, r in m["seg"])
    return grp_tbl, mix, q, ch, "".join(cause), rows_tbl, tx, st, kpis, seg


KIND_CLS = {"Nghiệp vụ": "FIN", "Giả định": "ASSUME", "Ngẫu nhiên": "BRIEF"}


def ref_label(r, pg):
    return f"{r}" + (f" · {pg}" if pg else "")


def render_why():
    out, cats = [], []
    for w in WHY:
        if w["cat"] not in cats:
            cats.append(w["cat"])
    for c in cats:
        items = [w for w in WHY if w["cat"] == c]
        out.append(f'<h3 class="sub">{e(c)}</h3>')
        if c == "Tham số ngẫu nhiên":
            rows = "".join(f"<tr><td><b>{e(w['q'])}</b></td><td>{e(' '.join(w['a']))}</td><td>{', '.join(f'<a href=#{p}>{p}</a>' for p in w['params'])}</td></tr>" for w in items)
            out.append(f'<p class=muted>Những giá trị chọn ngẫu nhiên trong khoảng — chỉ cần một câu.</p><div class=tw><table><thead><tr><th>Tham số</th><th>Giải thích</th><th>Sổ tham số</th></tr></thead><tbody>{rows}</tbody></table></div>')
            continue
        for w in items:
            paras = "".join(f"<p>{e(x)}</p>" for x in w["a"])
            refs = " ".join(f'<a class="rf" href="#src-{r}" title="{e(SRC[r][2])}">{e(ref_label(r, pg))}</a>' for r, pg in w["refs"])
            prm = ", ".join(f'<a href="#{p}">{p}</a>' for p in w["params"])
            out.append(f'<details class="why" open><summary><span class="tag t-{KIND_CLS[w["kind"]]}">{e(w["kind"])}</span> {e(w["q"])}</summary>{paras}'
                       f'<div class="wref">{("<b>Nguồn:</b> " + refs) if refs else "<b>Nguồn:</b> <span class=muted>không có số công bố — giả định của dự án</span>"}'
                       f'{(" · <b>Tham số:</b> " + prm) if prm else ""}</div></details>')
    return "".join(out)


def render_why_md():
    L = ["# Hỏi đáp: Tại sao dữ liệu nguồn được thiết kế và sinh như vậy", "",
         "Sinh tự động từ `scripts/why_meta.py` bởi `scripts/build_learning.py`. Nhãn: **[Nghiệp vụ]** có căn cứ; **[Giả định]** nêu cơ sở và lý do phạm vi POC; **[Ngẫu nhiên]** chỉ một câu. Mã nguồn (F1, P3…) tra ở bảng Nguồn cuối trang; trang PDF ghi kèm.", ""]
    cat = None
    for w in WHY:
        if w["cat"] != cat:
            cat = w["cat"]
            L += [f"## {cat}", ""]
            if cat == "Tham số ngẫu nhiên":
                L += ["| Tham số | Giải thích |", "|---|---|"]
        if cat == "Tham số ngẫu nhiên":
            L.append(f"| {w['q']} | {' '.join(w['a'])} |")
            continue
        L += [f"**[{w['kind']}] {w['q']}**", ""]
        for x in w["a"]:
            L += ["- " + x[1:].strip()] if x.startswith("•") else ["", x, ""]
        refs = "; ".join(f"[{ref_label(r, pg)}]({SRC[r][3]})" if SRC[r][3] else ref_label(r, pg) for r, pg in w["refs"])
        L += ["", f"*Nguồn:* {refs or 'không có số công bố — giả định của dự án'}", ""]
    L += ["", "## Nguồn và số trang", "", "| Mã | Nguồn | Trang trong PDF |", "|---|---|---|"]
    for i, t, n, u, note in SOURCES:
        if i in PAGES:
            L.append(f"| {i} | [{n}]({u}) | {PAGES[i]} |")
    return "\n".join(L) + "\n"


def db_block():
    """Khối 'Số liệu trên DB' từ db_snapshot.json (dữ liệu thật trên reportapi, bronze.ins_*)."""
    if not DB_SNAPSHOT.exists():
        return "<p class=muted>Chưa có db_snapshot.json — chạy measure_db.py.</p>"
    d = json.loads(DB_SNAPSHOT.read_text(encoding="utf-8"))
    rows = dict(d["rows"])
    rev, rev_m = defaultdict(float), defaultdict(float)
    for g, m, v in d["rev_group_month"]:
        rev[g] += v
        rev_m[int(m)] += v
    tot = sum(rev.values())
    written = dict(d["written_group"])
    share = (5592 + 8002) / 88054
    budget = {g: v * share for g, v in TARGETS_2025.items()}
    pol = dict(d["policies_group"])
    ptot = sum(pol.values())
    tr = "".join(f"<tr><td>{e(GROUP_NAME[g])}</td><td class=num>{ty(budget[g] * 1e9)}</td><td class=num>{ty(written.get(g, 0) * 1e9)}</td>"
                 f"<td class=num>{pct((written.get(g, 0) / budget[g] - 1) * 100)}%</td><td class=num>{ty(rev.get(g, 0) * 1e9)}</td>"
                 f"<td class=num>{pct(pol.get(g, 0) / ptot * 100)}%</td><td class=num>{pct(rev.get(g, 0) / tot * 100)}%</td></tr>"
                 for g in [x[0] for x in b.PRODUCT_GROUPS])
    tr += (f"<tr class=tot><td>Tổng</td><td class=num>{ty(sum(budget.values()) * 1e9)}</td><td class=num>{ty(sum(written.values()) * 1e9)}</td>"
           f"<td class=num>{pct((sum(written.values()) / sum(budget.values()) - 1) * 100)}%</td><td class=num>{ty(tot * 1e9)}</td><td></td><td></td></tr>")
    tpd = "; ".join(f"tháng {int(m)}: {int(a):,}–{int(b_):,} (TB {int(c):,})".replace(",", ".") for m, a, b_, c in d["txn_per_day"])
    seg_n = sum(r[1] for r in d["segment"]); seg_r = sum(r[2] for r in d["segment"])
    segname = {s_[0]: s_[1] for s_ in b.SEGMENTS} | {"KHACH_LE_GOP": "Khách lẻ theo bảng kê (cá nhân mua qua đối tác)"}
    seg = "".join(f"<tr><td>{e(segname.get(k, k))}</td><td class=num>{pct(n / seg_n * 100)}%</td><td class=num>{pct(r / seg_r * 100)}%</td></tr>" for k, n, r in d["segment"])
    top10, top1 = d["top_share"][0]
    kp = [(f"{ty(tot * 1e9)} tỷ", "doanh thu ghi nhận T8–T9/2026"), (f"{rows['policy']:,}".replace(",", "."), "hợp đồng"),
          (f"{rows['policy_transaction']:,}".replace(",", "."), "giao dịch"), (f"{pct(top10 * 100)}%", "doanh thu ở 10% hợp đồng lớn nhất")]
    kpis = "".join(f"<div class=kpi><b>{a}</b><span>{e(t_)}</span></div>" for a, t_ in kp)
    return (f"<p>Số đo trực tiếp trên <code>reportapi</code>, schema <code>bronze</code>, bảng <code>ins_*</code> (bộ volume, sinh bằng "
            f"<code>gen_volume.py</code>, cùng logic và mục tiêu với v2). Đo lúc {e(d['measured_at'])}.</p><div class=kpis>{kpis}</div>"
            f"<h3 class=sub>Ngân sách T8–T9 và doanh thu theo nhóm (tỷ đồng)</h3><p class=muted>Ngân sách = mục tiêu năm 2025 (BCTC PVI) × tỷ trọng tháng 8 + 9 của toàn thị trường (Bộ Tài chính) = {pct(share * 100, 2)}%. "
            f"Phí gốc khai thác = cấp mới + tái tục đã duyệt (thước đo dùng để hiệu chỉnh). Doanh thu ghi nhận = theo accounting_date trong tháng 8–9, đã trừ giảm thu; phần du lịch hiệu lực sau 30/9 ghi nhận sau kỳ ({ty(d['spill_after'][0][0] * 1e9)} tỷ).</p>"
            f"<div class=tw><table><thead><tr><th>Nhóm</th><th class=num>Ngân sách</th><th class=num>Phí gốc khai thác</th><th class=num>Lệch</th><th class=num>Ghi nhận T8–T9</th><th class=num>% số hợp đồng</th><th class=num>% doanh thu</th></tr></thead><tbody>{tr}</tbody></table></div>"
            f"<p class=muted>Theo tháng: T8 {ty(rev_m[8] * 1e9)} · T9 {ty(rev_m[9] * 1e9)} tỷ. Giao dịch/ngày — {tpd}.</p>"
            f"<h3 class=sub>Theo phân khúc khách hàng (T8–T9/2026)</h3><div class=tw><table><thead><tr><th>Phân khúc</th><th class=num>% số hợp đồng</th><th class=num>% doanh thu</th></tr></thead><tbody>{seg}</tbody></table></div>")


def build():
    validate()
    m = measure()
    tree, direct_pct = target_tree(m)
    cnt = Counter(t for p in PARAMS for t in p["tags"])
    n_ass = sum("ASSUME" in p["tags"] for p in PARAMS)
    n_pure = sum("ASSUME" not in p["tags"] for p in PARAMS)
    cards = "".join(f'<button type="button" class="card t-{k}" data-f="{k}" aria-pressed="false"><b>{cnt.get(k, 0)}</b><span>{e(v[0])}</span><em>{e(v[1])}</em></button>'
                    for k, v in TAGS.items())
    steps = "".join(f'<li><b>{sid} · {e(t)}</b> <span class="code">build_v2.py:{e(c)}</span>' + "".join(f"<p>{e(x)}</p>" for x in paras) + "</li>"
                    for sid, t, c, paras in STEPS)
    used = defaultdict(list)
    for p in PARAMS:
        for s in p["src"]:
            used[s].append(p["id"])
    srcs = "".join(
        f'<tr id="src-{i}"><td><b>{i}</b></td><td>{pill(t)}</td><td>{f"<a href={chr(34)}{e(u)}{chr(34)} target=_blank rel=noopener>{e(n)}</a>" if u else e(n)}'
        f'<div class=muted>{e(note)}</div></td><td class=pg>{e(PAGES.get(i, "—"))}</td><td>{", ".join(f"<a href=#{x}>{x}</a>" for x in used.get(i, [])) or "<span class=muted>—</span>"}</td></tr>'
        for i, t, n, u, note in SOURCES)
    ds = []
    for did, (proves, notuse) in DATASETS.items():
        _, _, name, url, note = SRC[did]
        li = "".join(f"<li>{e(a)} <span class=ref>→ {e(r)}</span></li>" for a, r in proves)
        ds.append(f'<article class="ds"><h3><a href="{e(url)}" target=_blank rel=noopener>{e(name)}</a></h3><p class=muted>{e(note)}</p>'
                  f'<div class=dsgrid><div><h4>Chứng minh được</h4><ul>{li}</ul></div><div class=no><h4>Không dùng vào</h4><p>{e(notuse)}</p></div></div></article>')
    notused = "".join(f"<tr><td>{f'<a href={chr(34)}{e(u)}{chr(34)} target=_blank rel=noopener>{e(n)}</a>' if u else e(n)}</td><td>{e(r)}</td></tr>"
                      for n, u, r in NOT_USED)
    ds.append(f'<h3 class="sub">Đã xem xét nhưng không dùng</h3><div class="tw"><table><thead><tr><th>Nguồn</th><th>Lý do</th></tr></thead><tbody>{notused}</tbody></table></div>')
    limits = "".join(f"<tr><td><b>{e(a)}</b></td><td>{e(c)}</td><td>{e(d)}</td></tr>" for a, c, d in LIMITS)
    quiz = "".join(f"<details class=q><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in QUIZ)
    grp_tbl, mix, q, ch, cause, rows_tbl, tx, st, kpis, seg = results(m)
    why_html = render_why()
    MD_OUT.write_text(render_why_md(), encoding="utf-8")
    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in [("tong-quan", "Tổng quan"), ("tai-sao", "Tại sao?"), ("co-che", "Cơ chế sinh"), ("muc-tieu", "Mục tiêu"),
                                                      ("so-tham-so", "Sổ tham số"), ("dataset", "Dataset mẫu"), ("ket-qua", "Kết quả"),
                                                      ("nguon", "Nguồn"), ("gioi-han", "Giới hạn"), ("tu-kiem-tra", "Tự kiểm tra")])
    return PAGE.format(date=f"{dt.date.today():%d/%m/%Y}", nav=nav, cards=cards, total=len(PARAMS), n_ass=n_ass, n_pure=n_pure,
                       direct=pct(direct_pct), assumed=pct(100 - direct_pct), direct_css=f"{float(direct_pct):.1f}", steps=steps, tree=tree, registry=registry(), ds="".join(ds),
                       grp=grp_tbl, mix=mix, q=q, ch=ch, cause=cause, rows=rows_tbl, tx=tx, st=st, kpis=kpis, srcs=srcs, limits=limits, quiz=quiz, why=why_html, seg=seg, db=db_block(),
                       pipeline=e(PIPELINE))


PIPELINE = """flowchart TD
  A["B1 · Mục tiêu doanh thu 8 nhóm<br/>BCTC PVI × tỷ lệ chia"] --> B["B2 · Số hợp đồng / nhóm<br/>rải 12 tháng theo mùa vụ"]
  B --> C["B3 · Sinh từng hợp đồng<br/>sản phẩm → chế độ đơn → kênh → đơn vị → khách<br/>→ định phí → bán kèm → Trụ sở → ngày → đồng BH → phân bổ"]
  C --> D["B4 · Giao dịch gốc NEW / RENEW<br/>trạng thái, ngày ghi nhận, tỷ giá"]
  D --> E{"B5 · Hiệu chỉnh<br/>f = (mục tiêu − cố định) / co giãn"}
  E -->|"năm tiếp theo"| F["B6 · Tái tục 55%"]
  F --> B
  E -->|"năm cuối"| G["B7 · SĐBS 7%<br/>tăng / giảm / hoàn / hủy"]
  G --> H["B8 · Xuất bảng<br/>quy đổi VND, VAT, hoa hồng → 02_data.sql"]
  R["B0 · Danh mục ref<br/>luật, chuẩn ngành"] -.-> C"""

PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Logic sinh dữ liệu</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fbfaf7;--panel:#fff;--ink:#1b2430;--muted:#5b6673;--line:#e3e0d8;--accent:#0f5c63;--code:#f2efe8;--bad:#b4441b;--mono:'JetBrains Mono',ui-monospace,Consolas,monospace;
--LAW:#1f5f99;--LAWb:#e4eef8;--FIN:#1f7a4d;--FINb:#e3f3ea;--PUB:#0f6f6a;--PUBb:#def1ef;--STD:#7a3e8f;--STDb:#f1e6f4;
--SAMPLE:#8a4b14;--SAMPLEb:#f6eadc;--BRIEF:#45526b;--BRIEFb:#e8ebf0;--DERIVED:#4a4fb0;--DERIVEDb:#e8e9f8;--ASSUME:#b4441b;--ASSUMEb:#fbe5da}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#12161b;--panel:#191e25;--ink:#e6e8eb;--muted:#9aa4af;--line:#2a313a;--accent:#5cc3c9;--code:#20262e;--bad:#f08a64;
--LAW:#7db7ec;--LAWb:#172636;--FIN:#6fd3a0;--FINb:#173127;--PUB:#62d0c6;--PUBb:#142f2d;--STD:#d59ae6;--STDb:#2e2034;
--SAMPLE:#e2a15b;--SAMPLEb:#33261a;--BRIEF:#aab6cc;--BRIEFb:#252b35;--DERIVED:#a3a7f5;--DERIVEDb:#24264a;--ASSUME:#f39a73;--ASSUMEb:#3a2118}}}}
:root[data-theme=dark]{{--bg:#12161b;--panel:#191e25;--ink:#e6e8eb;--muted:#9aa4af;--line:#2a313a;--accent:#5cc3c9;--code:#20262e;--bad:#f08a64;
--LAW:#7db7ec;--LAWb:#172636;--FIN:#6fd3a0;--FINb:#173127;--PUB:#62d0c6;--PUBb:#142f2d;--STD:#d59ae6;--STDb:#2e2034;
--SAMPLE:#e2a15b;--SAMPLEb:#33261a;--BRIEF:#aab6cc;--BRIEFb:#252b35;--DERIVED:#a3a7f5;--DERIVEDb:#24264a;--ASSUME:#f39a73;--ASSUMEb:#3a2118}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 'Be Vietnam Pro',system-ui,sans-serif}}
a{{color:var(--accent)}}code,.code{{font-family:var(--mono);font-size:.82em}}code{{background:var(--code);padding:.1em .35em;border-radius:4px}}.code{{color:var(--muted)}}
.muted{{color:var(--muted);font-size:12.5px}}
.top{{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}}.top nav{{max-width:1360px;margin:0 auto;padding:10px 16px;display:flex;gap:4px;flex-wrap:wrap;align-items:center}}
.top nav b{{margin-right:10px}}.top nav a{{padding:5px 10px;border-radius:6px;text-decoration:none;color:var(--ink);font-size:14px}}.top nav a:hover{{background:var(--code)}}
.top nav button{{margin-left:auto;font:inherit;font-size:12px;background:none;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:5px 10px;cursor:pointer}}
main{{max-width:1360px;margin:0 auto;padding:28px 16px 80px}}h1{{font-size:clamp(24px,3vw,36px);margin:0 0 8px;line-height:1.2}}
.lead{{color:var(--muted);max-width:920px;margin:0 0 14px}}
section{{margin-top:44px}}section>h2{{font-size:22px;margin:0 0 6px;color:var(--accent)}}section>p{{color:var(--muted);margin:0 0 12px;max-width:920px}}
.big{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:0 0 18px}}
.big div{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}.big b{{display:block;font-size:28px;font-variant-numeric:tabular-nums}}.big span{{color:var(--muted);font-size:13px}}
.big .a b{{color:var(--ASSUME)}}.big .f b{{color:var(--FIN)}}
.split{{display:flex;height:14px;border-radius:99px;overflow:hidden;margin:8px 0 4px}}.split i{{display:block}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}}
.card{{text-align:left;font:inherit;color:inherit;cursor:pointer;background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--c);border-radius:10px;padding:10px 12px}}
.card b{{display:block;font-size:24px;color:var(--c);font-variant-numeric:tabular-nums}}.card span{{font-weight:600}}.card em{{display:block;font-style:normal;color:var(--muted);font-size:12px}}
.card[aria-pressed=true]{{outline:2px solid var(--accent);outline-offset:1px}}
.t-LAW{{--c:var(--LAW);--cb:var(--LAWb)}}.t-FIN{{--c:var(--FIN);--cb:var(--FINb)}}.t-PUB{{--c:var(--PUB);--cb:var(--PUBb)}}.t-STD{{--c:var(--STD);--cb:var(--STDb)}}
.t-SAMPLE{{--c:var(--SAMPLE);--cb:var(--SAMPLEb)}}.t-BRIEF{{--c:var(--BRIEF);--cb:var(--BRIEFb)}}.t-DERIVED{{--c:var(--DERIVED);--cb:var(--DERIVEDb)}}.t-ASSUME{{--c:var(--ASSUME);--cb:var(--ASSUMEb)}}
.tag{{display:inline-block;white-space:nowrap;font-size:11px;font-weight:600;padding:1px 7px;border-radius:99px;color:var(--c);background:var(--cb);margin:0 4px 4px 0}}
.tag.t-ASSUME{{outline:1px solid var(--c)}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}}table{{border-collapse:collapse;width:100%;font-size:13.5px}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--code);font-weight:600}}tr:last-child td{{border-bottom:0}}td{{overflow-wrap:anywhere}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}td.num small{{display:block;color:var(--muted);font-size:11.5px}}td.bad{{color:var(--bad);font-weight:600}}tr.tot td{{font-weight:700;background:var(--code)}}
.formula{{font-family:var(--mono);font-size:13.5px;background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:12px 16px;white-space:pre-wrap;overflow-x:auto}}
ol.steps{{padding-left:20px}}ol.steps li{{margin:0 0 10px}}ol.steps p{{margin:2px 0;color:var(--muted)}}
pre.mermaid{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px;text-align:center;overflow:auto}}
.tools{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0}}.tools input{{font:inherit;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);min-width:260px;flex:1;max-width:420px}}
.tools label{{font-size:13px;color:var(--muted);display:flex;gap:6px;align-items:center}}#finfo{{font-size:13px;color:var(--muted)}}
#reg td.pid{{font-family:var(--mono);font-size:12px;color:var(--muted);white-space:nowrap}}#reg .val{{font-size:12.5px;margin-top:2px}}#reg .code{{font-size:11.5px;margin-top:4px}}
#reg td.why{{font-size:13px;min-width:260px}}#reg td.srcs{{font-size:12px;min-width:170px}}#reg td.srcs a{{text-decoration:none}}#reg td.imp{{font-size:12.5px;min-width:170px;color:var(--muted)}}
#reg tr.stephead th{{background:color-mix(in srgb,var(--accent) 12%,var(--panel));color:var(--accent)}}#reg tr.stephead span{{font-weight:400;font-family:var(--mono);font-size:12px;color:var(--muted);margin-left:8px}}
#reg tr.pr:target{{background:color-mix(in srgb,var(--accent) 10%,var(--panel))}}
.lvl{{display:inline-block;font-size:11px;font-weight:700;padding:0 6px;border-radius:4px;border:1px solid}}.l-Cao{{color:var(--bad)}}.l-Vừa{{color:var(--SAMPLE)}}.l-Thấp{{color:var(--muted)}}
.ds{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 12px}}.ds h3{{margin:0;font-size:16px}}.ds h4{{margin:8px 0 4px;font-size:13px}}
.dsgrid{{display:grid;grid-template-columns:2fr 1fr;gap:16px}}.dsgrid ul{{margin:0;padding-left:18px;font-size:13.5px}}.dsgrid .ref{{color:var(--muted);font-family:var(--mono);font-size:11.5px}}
.dsgrid .no{{border-left:3px solid var(--ASSUME);padding-left:12px;font-size:13px;color:var(--muted)}}.dsgrid .no p{{margin:0}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:12px 0}}.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 14px}}.kpi b{{display:block;font-size:22px}}.kpi span{{font-size:12.5px;color:var(--muted)}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}h3.sub{{font-size:15px;margin:22px 0 8px}}
details.q{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:0 0 8px}}details.q summary{{cursor:pointer;font-weight:600}}details.q p{{margin:8px 0 0}}
details.why{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:0 0 8px}}details.why summary{{cursor:pointer;font-weight:600}}details.why p{{margin:6px 0 0;max-width:980px}}.wref{{margin-top:8px;font-size:12.5px;color:var(--muted)}}a.rf{{display:inline-block;font-family:var(--mono);font-size:11.5px;background:var(--code);border-radius:4px;padding:0 6px;margin:0 4px 2px 0;text-decoration:none}}td.pg{{font-size:12px;color:var(--muted);min-width:180px}}
.callout{{background:var(--ASSUMEb);border-left:4px solid var(--ASSUME);border-radius:8px;padding:10px 14px;font-size:14px;max-width:920px}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
@media (max-width:800px){{.dsgrid,.grid2{{grid-template-columns:1fr}}.top nav{{flex-wrap:nowrap;overflow-x:auto}}.top nav a,.top nav b,.top nav button{{white-space:nowrap;flex:none}}}}
@media print{{.top{{position:static}}.top nav button,.tools{{display:none}}}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style></head><body>
<div class="top"><nav aria-label="Mục lục"><b>Logic sinh dữ liệu</b>{nav}<button type="button" id="theme">Sáng / Tối</button></nav></div>
<main>
<section id="tong-quan" style="margin-top:0"><h1>Logic sinh dữ liệu, cơ chế và căn cứ</h1>
<p class="lead">Tài liệu học cho bộ sinh dữ liệu nguồn <code>build_v2.py</code>. Mỗi tham số đều ghi rõ giá trị, vị trí trong code, căn cứ (văn bản pháp luật, số liệu công bố, dataset mẫu public…) và <b>phần nào là giả định</b>. Chỉ dùng nguồn public; không dùng dữ liệu nội bộ của doanh nghiệp nào làm căn cứ. Số liệu ở mục Kết quả được đo trực tiếp từ bộ sinh. Cập nhật {date}.</p>
<div class="big">
 <div class="f"><b>{direct}%</b><span>doanh thu mục tiêu 2025 lấy thẳng từ số công bố (Con người, Xe, Cháy nổ của BCTC PVI)</span></div>
 <div class="a"><b>{assumed}%</b><span>phụ thuộc giả định "tài sản thuần = 50%" (P21)</span></div>
 <div><b>{total}</b><span>tham số trong sổ: {n_pure} có căn cứ đầy đủ, {n_ass} có phần giả định</span></div>
</div>
<div class="split" aria-hidden="true"><i style="width:{direct_css}%;background:var(--FIN)"></i><i style="flex:1;background:var(--ASSUME)"></i></div>
<h3 class="sub">Nhãn căn cứ — bấm để lọc sổ tham số</h3>
<div class="cards" role="group" aria-label="Lọc theo nhãn căn cứ">{cards}</div>
<p class="callout" style="margin-top:14px"><b>Cách đọc:</b> một tham số có thể mang nhiều nhãn. Ví dụ biểu phí TNDS 437.000 đ là <b>Văn bản pháp luật</b>, nhưng tỷ lệ xe dưới 6 chỗ chiếm 50% là <b>Giả định</b>. Cột "Căn cứ / giải thích" nói rõ phần nào thuộc nhãn nào. Mọi dòng có nhãn Giả định đều ghi kèm mức ảnh hưởng nếu giả định sai.</p>
</section>

<section id="tai-sao"><h2>Hỏi đáp: Tại sao?</h2><p>Các câu hỏi “tại sao” khách hàng hay hỏi, trả lời theo nghiệp vụ. <span class="tag t-FIN">Nghiệp vụ</span> có căn cứ; <span class="tag t-ASSUME">Giả định</span> nêu cơ sở và lý do phạm vi POC; tham số ngẫu nhiên chỉ một câu. Nguồn PDF ghi kèm số trang (trang theo trình đọc PDF).</p>{why}</section>

<section id="co-che"><h2>Cơ chế sinh dữ liệu</h2><p>Bộ sinh không chia đều tiền cho các đơn. Nó đặt <b>đích doanh thu</b> trước, sinh hợp đồng theo "dáng" của từng sản phẩm (tần suất × độ lớn), rồi <b>hiệu chỉnh</b> quy mô đơn nhóm/lô hoặc STBH để khớp đích.</p>
<pre class="mermaid">{pipeline}</pre>
<ol class="steps">{steps}</ol>
<h3 class="sub">Công thức doanh thu (dùng để đo và để hiệu chỉnh)</h3>
<div class="formula">doanh thu = transaction_coverage.premium_vnd          phí 100% hợp đồng, VND, chưa VAT         (TT 232; Luật GTGT)
          × coinsurance_share.share_pct('OWN') / 100   phần của công ty khi đồng bảo hiểm       (TT 232 Đ19; Luật KDBH Đ4 k29)
          × revenue_allocation.allocation_pct / 100    phần phân bổ cho đơn vị                  (giả định quản trị — P19)
chỉ tính status = 'APPROVED'; kỳ = accounting_date = max(ngày cấp, ngày hiệu lực); SĐBS mang dấu âm/dương   (TT 67 Đ41; NĐ 46 Đ49)</div>
</section>

<section id="muc-tieu"><h2>Từ số công bố đến doanh thu mục tiêu</h2><p>Bước B1. Tổng của từng nghiệp vụ là số công bố; phần chia xuống nhóm sản phẩm có chỗ là giả định (tỷ đồng).</p>
<div class="tw"><table><thead><tr><th>Nhóm sản phẩm</th><th>Công thức</th><th class=num>2024</th><th class=num>2025</th><th>Căn cứ</th><th>Tham số</th></tr></thead><tbody>{tree}</tbody></table></div>
</section>

<section id="so-tham-so"><h2>Sổ tham số</h2><p>Toàn bộ tham số của <code>build_v2.py</code>, theo thứ tự các bước sinh. Lọc theo nhãn ở trên, hoặc gõ từ khóa.</p>
<div class="tools"><input type="search" id="q" placeholder="Tìm: TNDS, mùa vụ, đồng bảo hiểm, P21…" aria-label="Tìm trong sổ tham số">
<label><input type="checkbox" id="onlyA"> Chỉ dòng có giả định</label><span id="finfo"></span></div>
<div class="tw"><table id="reg"><thead><tr><th>#</th><th>Tham số · giá trị · code</th><th>Nhãn</th><th>Căn cứ / giải thích</th><th>Nguồn</th><th>Ảnh hưởng nếu giả định sai</th></tr></thead><tbody>{registry}</tbody></table></div>
</section>

<section id="dataset"><h2>Dataset mẫu public</h2><p>Dataset mẫu là các bộ dữ liệu bảo hiểm công khai trên internet. Chúng dùng để <b>chứng minh cấu trúc</b> (dữ liệu bảo hiểm thật trông như thế nào), <b>không</b> dùng để lấy con số. Mọi con số đều lấy từ nguồn Việt Nam ở trên.</p>{ds}</section>

<section id="ket-qua"><h2>Kết quả đo trên dữ liệu đã sinh</h2>
<h3 class="sub">A. Dữ liệu trên DB (reportapi) — bộ đang dùng cho dashboard</h3>{db}
<h3 class="sub">B. Bộ v2 (2024–2025) — dùng kiểm chứng logic theo năm</h3><p>Chỉ giao dịch APPROVED, phần của công ty, theo năm của <code>accounting_date</code>. Đo trực tiếp từ bộ sinh v2 (seed 2026) khi build tài liệu này.</p>
<div class="kpis">{kpis}</div>
<h3 class="sub">Doanh thu theo nhóm so với mục tiêu (tỷ đồng)</h3>
<div class="tw"><table><thead><tr><th rowspan=2>Nhóm</th><th colspan=3 class=num>2024</th><th colspan=3 class=num>2025</th></tr>
<tr><th class=num>Mục tiêu</th><th class=num>Dummy</th><th class=num>Lệch</th><th class=num>Mục tiêu</th><th class=num>Dummy</th><th class=num>Lệch</th></tr></thead><tbody>{grp}</tbody></table></div>
<h3 class="sub">Vì sao lệch</h3><ul>{cause}</ul>
<div class="grid2">
<div><h3 class="sub">Cơ cấu 3 nhóm POC 2025</h3><div class="tw"><table><thead><tr><th>Nhóm</th><th class=num>Dummy</th><th class=num>Số công bố</th><th>Căn cứ</th></tr></thead><tbody>{mix}</tbody></table></div></div>
<div><h3 class="sub">Theo quý — dummy (dòng nhỏ: PVI)</h3><div class="tw"><table><thead><tr><th>Năm</th><th class=num>Q1</th><th class=num>Q2</th><th class=num>Q3</th><th class=num>Q4</th></tr></thead><tbody>{q}</tbody></table></div></div>
</div>
<h3 class="sub">Theo phân khúc khách hàng (2025)</h3><div class="tw"><table><thead><tr><th>Phân khúc</th><th class=num>% số hợp đồng</th><th class=num>% doanh thu</th></tr></thead><tbody>{seg}</tbody></table></div>
<h3 class="sub">Theo kênh</h3><div class="tw"><table><thead><tr><th>Kênh</th><th class=num>2024</th><th class=num>2025</th><th>Định hướng</th></tr></thead><tbody>{ch}</tbody></table></div>
<div class="grid2">
<div><h3 class="sub">Số dòng</h3><div class="tw"><table><tbody>{rows}</tbody></table></div></div>
<div><h3 class="sub">Giao dịch</h3><p class=muted>Loại: {tx}</p><p class=muted>Trạng thái: {st}</p></div>
</div>
</section>

<section id="nguon"><h2>Danh mục nguồn</h2><p>Mỗi nguồn kèm danh sách tham số dùng nó. Bấm mã tham số để nhảy tới dòng trong sổ.</p>
<div class="tw"><table><thead><tr><th>Mã</th><th>Nhãn</th><th>Nguồn</th><th>Trang (PDF)</th><th>Dùng cho</th></tr></thead><tbody>{srcs}</tbody></table></div></section>

<section id="gioi-han"><h2>Giới hạn đã biết</h2>
<div class="tw"><table><thead><tr><th>Vấn đề</th><th>Chi tiết</th><th>Cách hiểu / xử lý</th></tr></thead><tbody>{limits}</tbody></table></div></section>

<section id="tu-kiem-tra"><h2>Tự kiểm tra</h2><p>Câu hỏi khách hàng hay hỏi. Thử tự trả lời trước khi mở đáp án.</p>{quiz}</section>
</main>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>
(function(){{
  var root=document.documentElement;
  try{{var t=localStorage.getItem('poc-theme');if(t)root.setAttribute('data-theme',t);}}catch(e){{}}
  var dark=function(){{return root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);}};
  if(window.mermaid){{mermaid.initialize({{startOnLoad:true,theme:dark()?'dark':'neutral',securityLevel:'strict',flowchart:{{htmlLabels:true}}}});}}
  document.getElementById('theme').onclick=function(){{var n=dark()?'light':'dark';root.setAttribute('data-theme',n);try{{localStorage.setItem('poc-theme',n);}}catch(e){{}}}};
  var cur=null,cards=[].slice.call(document.querySelectorAll('.card')),q=document.getElementById('q'),onlyA=document.getElementById('onlyA'),info=document.getElementById('finfo');
  var rows=[].slice.call(document.querySelectorAll('#reg tr.pr')),heads=[].slice.call(document.querySelectorAll('#reg tr.stephead'));
  function apply(){{
    var s=q.value.trim().toLowerCase(),n=0;
    rows.forEach(function(r){{var tg=r.dataset.tags.split(' ');var ok=(!cur||tg.indexOf(cur)>=0)&&(!onlyA.checked||tg.indexOf('ASSUME')>=0)&&(!s||r.dataset.text.indexOf(s)>=0);r.style.display=ok?'':'none';if(ok)n++;}});
    heads.forEach(function(h){{var x=h.nextElementSibling,vis=false;while(x&&!x.classList.contains('stephead')){{if(x.style.display!=='none')vis=true;x=x.nextElementSibling;}}h.style.display=vis?'':'none';}});
    info.textContent=n+' / '+rows.length+' tham số'+(cur?' · nhãn: '+document.querySelector('.card[data-f='+cur+'] span').textContent:'');
  }}
  cards.forEach(function(c){{c.addEventListener('click',function(){{cur=(cur===c.dataset.f)?null:c.dataset.f;cards.forEach(function(x){{x.setAttribute('aria-pressed',String(x.dataset.f===cur));}});apply();document.getElementById('so-tham-so').scrollIntoView();}});}});
  q.addEventListener('input',apply);onlyA.addEventListener('change',apply);apply();
}})();
</script></body></html>"""

if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("HTML:", OUT)
