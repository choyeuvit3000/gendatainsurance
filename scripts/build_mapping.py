r"""Sinh tài liệu mapping v2 ↔ PIAS dạng HTML trực quan từ scripts/mapping_meta.py.

Chạy:  python scripts/build_mapping.py   →  docs/Mapping_v2_PIAS.html   (TÀI LIỆU NỘI BỘ)
"""
import datetime as dt
import html
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mapping_meta import CODE_MAPS, CORRECTIONS, DECISIONS, FLOW, SAMPLE, TABLE_MAP  # noqa: E402

OUT = Path(__file__).parent.parent / "docs" / "Mapping_v2_PIAS.html"
STATUS = {  # mã -> (nhãn, mô tả)
    "OK": ("Khớp", "Khớp trực tiếp, đã kiểm chứng trên dữ liệu"),
    "TF": ("Biến đổi", "Biến đổi theo quy tắc, đã kiểm chứng"),
    "STD": ("Quy ước chuẩn", "Dự án chốt khi nguồn mơ hồ — có căn cứ dữ liệu / quy định"),
    "GAP": ("PIAS không có", "v2 sinh mới / suy ra"),
    "OUT": ("Không dùng", "PIAS có, ngoài phạm vi v2"),
}
e = html.escape


def pill(code):
    return f'<span class="pill s-{code}" title="{e(STATUS[code][1])}">{e(STATUS[code][0])}</span>'


def build():
    counts = Counter(st for _, (_, _, rows) in TABLE_MAP.items() for *_, st, _ in rows)
    cards = "".join(f'<button type="button" class="card s-{k}" data-f="{k}" aria-pressed="false"><b>{counts.get(k, 0)}</b><span>{e(v[0])}</span><em>{e(v[1])}</em></button>'
                    for k, v in STATUS.items())
    corr = "".join(f"<tr><td><b>{e(a)}</b></td><td class='old'>{e(b)}</td><td class='new'>{e(c)}</td><td>{e(d)}</td></tr>" for a, b, c, d in CORRECTIONS)
    tables = []
    for v2, (src, note, rows) in TABLE_MAP.items():
        trs = "".join(
            f"<tr data-s='{st}'><td><code>{e(col)}</code></td><td class='arrow' aria-hidden='true'>←</td><td><code class='src'>{e(s)}</code>"
            f"{f'<div class=rule>{e(rule)}</div>' if rule else ''}</td><td>{pill(st)}</td><td class='ev'>{e(ev)}</td></tr>"
            for col, s, rule, st, ev in rows)
        tables.append(f"""<article class="tm"><header><div class="side v2"><span>v2</span><code>{e(v2)}</code></div>
<div class="side pias"><span>PIAS</span><code>{e(src)}</code></div></header>{f'<p class="note">{e(note)}</p>' if note else ''}
<div class="tw"><table><thead><tr><th>Cột v2</th><th></th><th>Nguồn PIAS · quy tắc</th><th>Trạng thái</th><th>Bằng chứng kiểm chứng</th></tr></thead>
<tbody>{trs}</tbody></table></div></article>""")
    codes = []
    for name, (desc, cols, rows) in CODE_MAPS.items():
        head = "".join(f"<th>{e(c)}</th>" for c in cols[:-1]) + "<th>Trạng thái</th>"
        body = "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in r[:-1]) + f"<td>{pill(r[-1])}</td></tr>" for r in rows)
        codes.append(f'<details class="cm" open><summary>{e(name)}<span>{e(desc)}</span></summary><div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></details>')
    ba = "".join(f"<tr><td><b>{e(a)}</b></td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in DECISIONS)
    nav = "".join(f'<a href="#{i}">{t}</a>' for i, t in [("tong-quan", "Tổng quan"), ("luong", "Luồng dữ liệu"), ("dinh-chinh", "Đính chính"),
                                                      ("bang", "Mapping theo bảng"), ("ma", "Bảng mã"), ("quy-uoc", "Quy ước chuẩn")])
    return PAGE.format(date=f"{dt.date.today():%d/%m/%Y}", sample=e(SAMPLE), cards=cards, flow=e(FLOW), corr=corr,
                       tables="".join(tables), codes="".join(codes), ba=ba, nav=nav, total=sum(counts.values()))


PAGE = """<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapping v2 ↔ PIAS</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fbfaf7;--panel:#fff;--ink:#1b2430;--muted:#5b6673;--line:#e3e0d8;--accent:#0f5c63;--code:#f2efe8;--v2:#0f5c63;--pias:#8a4b14;
--ok:#1f7a4d;--okb:#e3f3ea;--tf:#1f5f99;--tfb:#e4eef8;--chk:#9a5b00;--chkb:#fbefd9;--gap:#5b6673;--gapb:#eceae4;--new:#7a3e8f;--newb:#f1e6f4;--mono:'JetBrains Mono',ui-monospace,Consolas,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#12161b;--panel:#191e25;--ink:#e6e8eb;--muted:#9aa4af;--line:#2a313a;--accent:#5cc3c9;--code:#20262e;--v2:#5cc3c9;--pias:#e2a15b;
--ok:#6fd3a0;--okb:#173127;--tf:#7db7ec;--tfb:#172636;--chk:#f0b65a;--chkb:#35290f;--gap:#a9b2bc;--gapb:#262b31;--new:#d59ae6;--newb:#2e2034}}}}
:root[data-theme=dark]{{--bg:#12161b;--panel:#191e25;--ink:#e6e8eb;--muted:#9aa4af;--line:#2a313a;--accent:#5cc3c9;--code:#20262e;--v2:#5cc3c9;--pias:#e2a15b;
--ok:#6fd3a0;--okb:#173127;--tf:#7db7ec;--tfb:#172636;--chk:#f0b65a;--chkb:#35290f;--gap:#a9b2bc;--gapb:#262b31;--new:#d59ae6;--newb:#2e2034}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 'Be Vietnam Pro',system-ui,sans-serif}}
a{{color:var(--accent)}}code{{font-family:var(--mono);font-size:.85em;background:var(--code);padding:.1em .35em;border-radius:4px;overflow-wrap:anywhere}}
.top{{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}}.top nav{{max-width:1300px;margin:0 auto;padding:10px 16px;display:flex;gap:4px;flex-wrap:wrap;align-items:center}}
.top nav b{{margin-right:10px}}.top nav a{{padding:5px 10px;border-radius:6px;text-decoration:none;color:var(--ink);font-size:14px}}.top nav a:hover{{background:var(--code)}}
.top nav button{{margin-left:auto;font:inherit;font-size:12px;background:none;border:1px solid var(--line);color:var(--muted);border-radius:6px;padding:5px 10px;cursor:pointer}}
main{{max-width:1300px;margin:0 auto;padding:28px 16px 80px}}h1{{font-size:clamp(24px,3vw,36px);margin:0 0 8px;line-height:1.2}}
.lead{{color:var(--muted);max-width:900px;margin:0 0 6px}}.warn{{display:inline-block;font-size:12.5px;padding:4px 10px;border-radius:6px;background:var(--chkb);color:var(--chk);margin:6px 0 18px}}
section{{margin-top:40px}}section>h2{{font-size:22px;margin:0 0 6px;color:var(--accent)}}section>p{{color:var(--muted);margin:0 0 12px;max-width:900px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}}
.card{{text-align:left;font:inherit;color:inherit;cursor:pointer;background:var(--panel);border:1px solid var(--line);border-left:5px solid;border-radius:10px;padding:12px 14px}}
.card b{{display:block;font-size:26px;font-variant-numeric:tabular-nums}}.card span{{font-weight:600}}.card em{{display:block;font-style:normal;color:var(--muted);font-size:12.5px}}
.card[aria-pressed=true]{{outline:2px solid var(--accent);outline-offset:1px}}
.s-OK{{--c:var(--ok);--cb:var(--okb)}}.s-TF{{--c:var(--tf);--cb:var(--tfb)}}.s-STD{{--c:var(--chk);--cb:var(--chkb)}}.s-GAP{{--c:var(--gap);--cb:var(--gapb)}}.s-OUT{{--c:var(--new);--cb:var(--newb)}}
.card{{border-left-color:var(--c)}}.card b{{color:var(--c)}}
.pill{{display:inline-block;white-space:nowrap;font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:99px;color:var(--c);background:var(--cb)}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}}table{{border-collapse:collapse;width:100%;font-size:13.5px}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:var(--code);font-weight:600}}tr:last-child td{{border-bottom:0}}
td{{overflow-wrap:anywhere}}td.arrow{{color:var(--muted);width:20px;padding-left:0;padding-right:0;text-align:center}}
code.src{{background:none;color:var(--pias);padding:0}}.rule{{font-size:12.5px;color:var(--muted);margin-top:3px}}.ev{{font-size:12.5px;color:var(--muted);min-width:220px}}
.old{{color:var(--muted);text-decoration:line-through;text-decoration-color:color-mix(in srgb,var(--chk) 60%,transparent)}}.new{{color:var(--ok);font-weight:500}}
pre.mermaid{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px;text-align:center;overflow:auto}}
.tm{{margin:14px 0 18px}}.tm header{{display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid var(--line);border-bottom:0;border-radius:8px 8px 0 0;overflow:hidden}}
.side{{padding:10px 14px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}}.side span{{font-size:11px;font-weight:700;letter-spacing:.06em;padding:2px 7px;border-radius:4px;color:var(--panel)}}
.side.v2{{background:color-mix(in srgb,var(--v2) 10%,var(--panel))}}.side.v2 span{{background:var(--v2)}}.side.v2 code{{color:var(--v2);background:none;font-size:15px;font-weight:600}}
.side.pias{{background:color-mix(in srgb,var(--pias) 10%,var(--panel))}}.side.pias span{{background:var(--pias)}}.side.pias code{{color:var(--pias);background:none}}
.tm .tw{{border-radius:0 0 8px 8px}}.tm .note{{margin:0;padding:6px 14px;font-size:12.5px;color:var(--muted);border-left:1px solid var(--line);border-right:1px solid var(--line);background:var(--panel)}}
details.cm{{margin:10px 0}}details.cm summary{{cursor:pointer;font-weight:600;padding:6px 0;display:flex;gap:12px;flex-wrap:wrap;align-items:baseline}}details.cm summary span{{font-weight:400;color:var(--muted);font-size:13px}}
ol.ba li{{margin:6px 0}}.filterinfo{{font-size:13px;color:var(--muted);margin:8px 0 0}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
@media (max-width:700px){{.tm header{{grid-template-columns:1fr}}}}
@media print{{.top{{position:static}}.top nav button{{display:none}}}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style></head><body>
<div class="top"><nav aria-label="Mục lục"><b>Mapping v2 ↔ PIAS</b>{nav}<button type="button" id="theme">Sáng / Tối</button></nav></div>
<main>
<section id="tong-quan" style="margin-top:0"><h1>Mapping mô hình v2 ↔ hệ thống nguồn PIAS</h1>
<p class="lead">Mỗi cột của dữ liệu nguồn v2 được đối chiếu với bảng/cột PIAS tương ứng, kèm quy tắc biến đổi và <b>bằng chứng kiểm chứng trên dữ liệu thật</b> (chỉ đọc). Mẫu kiểm chứng: {sample}. Cập nhật {date}.</p>
<span class="warn">Tài liệu nội bộ dự án — chỉ ghi số lượng / tỷ lệ, không ghi số tiền của khách hàng.</span>
<div class="cards" role="group" aria-label="Lọc theo trạng thái">{cards}</div>
<p class="filterinfo" id="finfo">Tổng {total} dòng mapping. Bấm một thẻ để lọc các bảng mapping theo trạng thái.</p></section>
<section id="luong"><h2>Luồng dữ liệu</h2><p>Bảng PIAS nào đổ vào bảng v2 nào.</p><pre class="mermaid">{flow}</pre></section>
<section id="dinh-chinh"><h2>Đính chính so với bản mapping trước</h2><p>Những điểm bản trước ghi sai hoặc thiếu, nay đã kiểm chứng lại.</p>
<div class="tw"><table><thead><tr><th>Nội dung</th><th>Bản trước</th><th>Đúng là</th><th>Bằng chứng</th></tr></thead><tbody>{corr}</tbody></table></div></section>
<section id="bang"><h2>Mapping theo bảng</h2><p>Trái: cột v2. Phải: nguồn PIAS và quy tắc. Cột cuối là bằng chứng đo trên dữ liệu.</p>{tables}</section>
<section id="ma"><h2>Bảng đối chiếu mã</h2><p>Giá trị mã PIAS → giá trị v2, kèm số lượng thực tế.</p>{codes}</section>
<section id="quy-uoc"><h2>Quy ước chuẩn đã chốt</h2><p>Những điểm nguồn PIAS không tự nói rõ. Dự án chốt theo bằng chứng dữ liệu và quy định; các quy ước này là chuẩn cho ETL.</p>
<div class="tw"><table><thead><tr><th>Vấn đề</th><th>Quy ước chuẩn</th><th>Căn cứ</th></tr></thead><tbody>{ba}</tbody></table></div></section>
</main>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
(function(){{
  var root=document.documentElement;
  try{{var t=localStorage.getItem('poc-theme');if(t)root.setAttribute('data-theme',t);}}catch(e){{}}
  var dark=function(){{return root.getAttribute('data-theme')==='dark'||(!root.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);}};
  if(window.mermaid){{mermaid.initialize({{startOnLoad:true,theme:dark()?'dark':'neutral',securityLevel:'strict',flowchart:{{htmlLabels:true}}}});}}
  document.getElementById('theme').onclick=function(){{var n=dark()?'light':'dark';root.setAttribute('data-theme',n);try{{localStorage.setItem('poc-theme',n);}}catch(e){{}}}};
  var cur=null, cards=[].slice.call(document.querySelectorAll('.card')), info=document.getElementById('finfo'), base=info.textContent;
  cards.forEach(function(c){{c.addEventListener('click',function(){{
    cur=(cur===c.dataset.f)?null:c.dataset.f;
    cards.forEach(function(x){{x.setAttribute('aria-pressed',String(x.dataset.f===cur));}});
    var shown=0;
    document.querySelectorAll('.tm').forEach(function(t){{var vis=0;t.querySelectorAll('tbody tr').forEach(function(r){{var ok=!cur||r.dataset.s===cur;r.style.display=ok?'':'none';if(ok)vis++;}});t.style.display=vis?'':'none';shown+=vis;}});
    info.textContent=cur?('Đang lọc: '+c.querySelector('span').textContent+' — '+shown+' dòng. Bấm lại để bỏ lọc.'):base;
    if(cur)document.getElementById('bang').scrollIntoView();
  }});}});
}})();
</script></body></html>"""

if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("HTML:", OUT)
