// Sinh deck thuyết trình (9 slide: tiêu đề, nguồn research, 5 bảng, danh mục, giao dịch, cơ chế, phân phối, giả định, kết quả): docs/POC_Logic_Sinh_Du_Lieu.pptx
// Chạy (cần pptxgenjs và apply_theme.js của skill pptx):
//   NODE_PATH=<thư mục node_modules có pptxgenjs> APPLY_THEME=<đường dẫn apply_theme.js> node scripts/build_deck.js
// Số liệu về dữ liệu lấy từ docs/db_snapshot.json (đo trên reportapi bằng measure_db.py) — nạp lại thì đo lại rồi build.
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.APPLY_THEME ||
  "C:/Users/admin/AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/Claude/local-agent-mode-sessions/skills-plugin/b9bbe9c7-6347-46b4-a2bf-f23838a431f8/8fbcd2f7-48a0-4c7f-a976-3330ed6c4ef5/skills/pptx/scripts/apply_theme.js");

const OUT = process.env.DECK_OUT || path.join(__dirname, "..", "docs", "POC_Logic_Sinh_Du_Lieu.pptx");   // DECK_OUT: ghi ra file khác khi bản chính đang mở
const THEME = {
  name: "POC Doanh thu bao hiem",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2430", lt1: "FFFFFF", dk2: "0B3B40", lt2: "EAF2F2",
    accent1: "0F6E75", accent2: "C2551E", accent3: "2E7D4F", accent4: "3E5C99",
    accent5: "7A4E9A", accent6: "9A6A1E", hlink: "0F6E75", folHlink: "7A4E9A",
  },
};
const HX = THEME.colors;
const MUTED = "5B6673";

// ---- số liệu đo trên DB (reportapi, bronze.ins_*) — sinh bởi measure_db.py ----
const DB = require(path.join(__dirname, "..", "docs", "db_snapshot.json"));
const vn = (x, d = 0) => Number(x).toLocaleString("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
const ROWS = Object.fromEntries(DB.rows);
const TXT = Object.fromEntries(DB.txn_type);
const STT = Object.fromEntries(DB.status);
const GROUPS = ["TNDS_BB", "VCX", "HOC_SINH", "DU_LICH", "SINH_MANG", "SUC_KHOE", "TAI_SAN", "CHAY_NO"];
const GNAME = { TNDS_BB: "TNDS BB", VCX: "Vật chất xe", HOC_SINH: "Học sinh", DU_LICH: "Du lịch", SINH_MANG: "Sinh mạng", SUC_KHOE: "Sức khỏe", TAI_SAN: "Tài sản", CHAY_NO: "Cháy nổ" };
const POC = { TNDS_BB: "XE", VCX: "XE", HOC_SINH: "NG", DU_LICH: "NG", SINH_MANG: "NG", SUC_KHOE: "NG", TAI_SAN: "TS", CHAY_NO: "TS" };
const REV = {}; let REV_TOT = 0; const REV_M = { 8: 0, 9: 0 };
DB.rev_group_month.forEach(([g, m, v]) => { REV[g] = (REV[g] || 0) + v; REV_TOT += v; REV_M[m] += v; });
const WRITTEN = Object.fromEntries(DB.written_group); const WRITTEN_TOT = Object.values(WRITTEN).reduce((a, b) => a + b, 0);
const POL = Object.fromEntries(DB.policies_group); const POL_TOT = Object.values(POL).reduce((a, b) => a + b, 0);
const MIX = { TS: 0, NG: 0, XE: 0 }; GROUPS.forEach(g => MIX[POC[g]] += (REV[g] || 0) / REV_TOT * 100);
const SEG = Object.fromEntries(DB.segment.map(([k, n, r]) => [k, { n, r }]));
const SEG_N = DB.segment.reduce((a, r) => a + r[1], 0), SEG_R = DB.segment.reduce((a, r) => a + r[2], 0);
const TPD = Object.fromEntries(DB.txn_per_day.map(([m, mn, mx, av]) => [m, { mn, mx, av }]));
const CH = Object.fromEntries(DB.channel); const CH_TOT = Object.values(CH).reduce((a, b) => a + b, 0);
const BUDGET_PVI = 10377.9 * (5592 + 8002) / 88054;  // quy mô PVI T8 + T9 (tỷ) = mục tiêu năm × tỷ trọng tháng (Bộ Tài chính)
// Không còn hệ số quy mô k: ngân sách trên DB = đúng quy mô PVI; > 50.000 giao dịch/ngày đến từ bảo hiểm vi mô (MV_*)
const PROD = Object.fromEntries(DB.product.map(([c, n, r]) => [c, { n, r }]));
const MICRO = [["MV_XSM_CARE", "Green SM Care", "Green SM · PVI Digital"], ["MV_FOOD_CARE", "Food Care", "Green SM · PVI Digital"],
  ["MV_TBDT_TMDT", "Thiết bị điện tử TMĐT", "Fuse · PVI Digital"], ["MV_DELAYCARE", "DelayCare (từ 20/8)", "ATADI · PVI Thủ Đô"]];
const MIC_N = MICRO.reduce((a, [c]) => a + (PROD[c] || { n: 0 }).n, 0), MIC_R = MICRO.reduce((a, [c]) => a + (PROD[c] || { r: 0 }).r, 0);
const PROD_N = DB.product.reduce((a, r) => a + r[1], 0);
// Biểu đồ tách bảo hiểm vi mô thành cột riêng (khỏi Sinh mạng / Du lịch / Tài sản) để không lẫn với sản phẩm truyền thống
const MIC_GROUP = { MV_XSM_CARE: "SINH_MANG", MV_FOOD_CARE: "SINH_MANG", MV_DELAYCARE: "DU_LICH", MV_TBDT_TMDT: "TAI_SAN" };
const POL_C = { ...POL, VI_MO: 0 }, REV_C = { ...REV, VI_MO: 0 };
Object.entries(MIC_GROUP).forEach(([c, g]) => { const x = PROD[c] || { n: 0, r: 0 };
  POL_C[g] -= x.n; POL_C.VI_MO += x.n; REV_C[g] -= x.r || 0; REV_C.VI_MO += x.r || 0; });
const CGROUPS = [...GROUPS, "VI_MO"];

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "Sinh dữ liệu nguồn cho POC Doanh thu bảo hiểm";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.6, fontSize: 44, bold: true, color: C.background1, fontFace: THEME.headFontFace, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.0, w: 11.7, h: 1.2, fontSize: 20, color: "CFE3E3", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HX.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 30, bold: true, color: C.text2, fontFace: THEME.headFontFace, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "POC Doanh thu bảo hiểm · Logic sinh dữ liệu", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: MUTED, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
});

const content = (section, title, notes) => {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
};
const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 });
const card = (s, x, y, w, h, fill = C.background2, name = "card") =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.12, shadow: shadow(), objectName: name });
const num = (s, n, x, y, d = 0.5, fill = C.accent1) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: `badge ${n}` });
  s.addText(String(n), { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: 16, bold: true, color: C.background1, margin: 0, isTextBox: true });
};
const T = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, margin: 0, valign: "top", fontSize: 15, color: C.text1 }, o));
const src = (s, text, y = 6.45) => T(s, [{ text: "Nguồn: ", options: { bold: true } }, { text }], { x: 0.6, y, w: 12.1, h: 0.45, fontSize: 11, color: MUTED });
const axis = { catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11, dataLabelColor: HX.dk1,
  legendFontFace: "+mn-lt", legendFontSize: 12, titleFontFace: "+mn-lt" };
const hdr = (t) => ({ text: t, options: { bold: true, color: HX.lt1, fill: { color: HX.dk2 }, fontSize: 13 } });
const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 13, color: HX.dk1 }, o) });
const BORDER = { type: "solid", color: "D9DEE2", pt: 0.75 };

// ============ 1. Tiêu đề ============
pres.addSection({ title: "Tổng quan" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Tổng quan" });
s.addText("Sinh dữ liệu nguồn cho POC Doanh thu bảo hiểm", { placeholder: "title" });
s.addText("Tổng Công ty Bảo hiểm PVI · 47 đơn vị · danh mục, giao dịch và căn cứ của từng con số\nDữ liệu trên reportapi (bronze.ins_*), tháng 8–9/2026 — đúng quy mô doanh thu PVI", { placeholder: "body" });
s.addNotes("Mục tiêu: giải thích dữ liệu nguồn gồm những danh mục và giao dịch nào, vì sao thiết kế như vậy, con số doanh thu đến từ đâu, chỗ nào là giả định và vì sao chọn giả định đó.");

// ============ 2. Nguồn research ============
s = content("Tổng quan", "Nguồn research: dùng nguồn nào, cho việc gì",
  "Năm nhóm nguồn: khung nghiệp vụ lấy từ luật; con số lấy từ số công bố; thông tin công khai để định hướng tỷ lệ và giá; dataset mẫu và chuẩn ngành chỉ để chứng minh cấu trúc — không lấy số; nhóm mới là bảo hiểm vi mô và đơn vị PVI (47 đơn vị thật, 4 sản phẩm vi mô có công bố). Nhóm mới được nghiên cứu chéo bằng codex CLI và agy CLI, mọi link kiểm lại bằng curl ngày 19/10/2026; mục không tìm thấy (doanh thu từng đơn vị, số GCN vi mô, phí DelayCare) ghi là ước tính. Một ô có thể gộp 2 nguồn, link trỏ tới nguồn đầu; đủ từng link ở Logic_Sinh_Du_Lieu.html (60 nguồn, mục Nguồn). Không dùng dữ liệu nội bộ của doanh nghiệp nào. Với PDF, số trang là trang theo trình đọc PDF.");
const SRC_GROUPS = [
  ["Văn bản pháp luật", "khung nghiệp vụ", C.accent4, [
    ["Luật KDBH 2022", "nghiệp vụ, kênh, đồng bảo hiểm", "https://vbpl.vn/van-ban/chi-tiet/luat-kinh-doanh-bao-hiem-so-08-2022-qh15--163515"],
    ["NĐ 46/2023", "nghiệp vụ; hoàn, giảm phí là giảm thu", "https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-46-2023-nd-cp-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163441"],
    ["NĐ 67/2023", "biểu phí TNDS, phí cháy nổ bắt buộc", "https://vbpl.vn/van-ban/chi-tiet/nghi-dinh-so-67-2023-nd-cp-quy-dinh-ve-bao-hiem-bat-buoc-trach-nhiem-dan-su-cua-chu-xe-co-gioi-bao-hiem-chay-no-bat-buoc-bao-hiem-bat-buoc-trong-hoat-dong-dau-tu-xay-dung--163442"],
    ["TT 67/2023", "ghi nhận doanh thu, mẫu báo cáo", "https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-67-2023-tt-btc-huong-dan-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem-nghi-dinh-so-46-2023-nd-cp-ngay-01-thang-7-nam-2023-cua-chinh-phu-quy-dinh-chi-tiet-thi-hanh-mot-so-dieu-cua-luat-kinh-doanh-bao-hiem--163439"],
    ["TT 232/2012", "tài khoản doanh thu, đồng BH", "https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-232-2012-tt-btc-huong-dan-ke-toan-ap-dung-doi-voi-doanh-nghiep-bao-hiem-phi-nhan-tho-doanh-nghiep-tai-bao-hiem-va-chi-nhanh-doanh-nghiep-bao-hiem-phi-nhan-tho-nuoc-ngoai--30429"],
    ["NQ 202/2025 · Luật GTGT", "34 tỉnh; VAT 0% bảo hiểm con người", "https://vbpl.vn/van-ban/chi-tiet/nghi-quyet-so-202-2025-qh15-ve-viec-sap-xep-don-vi-hanh-chinh-cap-tinh--179501"],
  ]],
  ["Số liệu công bố", "quy mô, cơ cấu, mùa vụ", C.accent3, [
    ["BCTC kiểm toán PVI 2025 — tr. 45", "phí gốc theo nghiệp vụ → mục tiêu doanh thu", "https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf"],
    ["BCTC quý PVI Holdings — tr. 31", "phí gốc theo quý → mùa vụ", "https://pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/ce6f18e2-7a79-42f3-b6ab-2b79ea1e4077.pdf"],
    ["IAV — thị trường 2024", "tỷ lệ TNDS / vật chất xe", "https://iav.vn/tong-quan,-so-lieu-thi-truong-bao-hiem/254773-254773-mot-so-hoat-dong-noi-bat-cua-thi-truong-bao-hiem-viet-nam-ca-nam-2024"],
    ["Bộ Tài chính — bản tin 01/2026", "thị phần PVI 16,93%; môi giới 13,5%", "https://mof.gov.vn/quan-ly-giam-sat-bao-hiem/ban-tin-thi-truong-bao-hiem-toan-cau/ban-tin-thi-truong-bao-hiem-thang-12026"],
    ["KBNN — tỷ giá hạch toán", "tỷ giá USD theo tháng", "https://thuvienphapluat.vn/van-ban/Tien-te-Ngan-hang/Thong-bao-7727-TB-KBNN-2024-ty-gia-hach-toan-ngoai-te-thang-01-nam-2025-641872.aspx"],
  ]],
  ["Thông tin công khai", "định hướng tỷ lệ, giá", C.accent1, [
    ["BCTN PVI 2024 — tr. 6, 29, 57", "TMĐT ≈ 800 tỷ, 30 chương trình API; nghiệp vụ năng lượng", "https://static2.vietstock.vn/vietstock/2025/3/19/3_pvi_2025_3_19_fb26c59_en_annualreport_2024.pdf"],
    ["FPTS định giá PVI — tr. 7, 13–15", "con người PVI tập trung khách doanh nghiệp", "https://file.fpts.com.vn/FileStore2/File/2025/04/14/DuyenNTM14042025Bao_cao_dinh_gia_lan_dau_PVI_0bef673f.pdf"],
    ["pvn.vn — quý I/2025", "kênh TMĐT tăng 1,8 lần", "https://pvn.vn/khoi-dau-vung-chac-bao-hiem-pvi-huong-toi-moc-doanh-thu-ty-do-la-my-nam-2025-28459"],
    ["Giá niêm yết PVI, Bảo Việt", "phí du lịch, sức khỏe, nhà, vật chất xe", "https://online.pvi.com.vn/san-pham"],
    ["Báo chí: hợp đồng lớn", "Vietnam Airlines, Quảng Trạch, Long Thành, Vinalines", "https://fireant.vn/bai-viet/nha-thau-trung-goi-bao-hiem-hon-500-ty-co-nang-luc-the-nao/29752615"],
    ["Bảo Việt IR 2024 — tr. 127", "mô hình 79 công ty thành viên", "https://static2.vietstock.vn/vietstock/2025/4/22/20250422_bvh_250422_integrated_report_2024.pdf"],
  ]],
  ["Dataset & chuẩn ngành", "chỉ chứng minh cấu trúc", C.accent6, [
    ["CASdatasets fremotor, freMTPL2", "phí theo quyền lợi; TNDS rất nhiều đơn nhỏ", "https://dutangc.github.io/CASdatasets/reference/freMTPL.html"],
    ["Kaggle Travel Insurance", "hoàn phí số âm; đại lý hãng bay / du lịch", "https://www.kaggle.com/datasets/mhdzahier/travel-insurance"],
    ["CAS Schedule P · UCI COIL 2000", "phần giữ lại; phân khúc khách, bán chéo", "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p"],
    ["Synthea · CMS DE-SynPUF", "phương pháp sinh dữ liệu giả lập", "https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary"],
    ["ACORD · Kimball · OMG · MS CDM", "hợp đồng → giao dịch → dòng phí", "https://learn.microsoft.com/en-us/common-data-model/schema/core/industrycommon/financialservices/propertyandcasualtydatamodel/overview"],
    ["Solvency II Annex I", "mã nghiệp vụ đối chiếu quốc tế", "https://www.legislation.gov.uk/eur/2015/35/annex/I/adopted"],
  ]],
  ["Bảo hiểm vi mô & đơn vị PVI", "4 sản phẩm vi mô, 47 đơn vị", C.accent2, [
    ["pvi.com.vn — mạng lưới", "47 đơn vị; tỉnh = địa chỉ trụ sở", "https://www.pvi.com.vn/vi/network"],
    ["BCTN PVI 2024 — tr. 12", "Bảo hiểm PVI = 100% của PVI Holdings", "https://cdn.24hmoney.vn/upload/file/2025-1/2025-03-22/no-name-1742584373.pdf"],
    ["BCTN PVI 2025 — tr. 29, 32–34", "27.258 / 28.923 tỷ; Hanoi Re, PVIAM", "https://www.pviholdings.com.vn/admin/downloadFile?filePath=//pvi.com.vn/data/webho_upload/4f50f1c9-9092-4e0e-b128-1bcfc18922d2.pdf"],
    ["Tin vinh danh · pvisg.net", "trọng số ×1,5 cho 5 đơn vị dẫn đầu", "https://www.pvi.com.vn/vi/news/pvi-thu-do-va-pvi-thang-long-hai-don-vi-tiep-theo-duoc-vinh-danh-hoan-thanh-som-ke-hoach-kinh-doanh-nam-2025"],
    ["Green SM Care · Food Care", "1.000–2.000 đ/GCN; PVI Digital 1/5 nhà BH", "https://www.greensm.com/vn-vi/bao-hiem-khach-hang"],
    ["DelayCare · Shopee/Fuse", "trễ chuyến bay; thiết bị điện tử TMĐT", "https://www.pvi.com.vn/vi/news/bao-hiem-pvi-ra-mat-delaycare-giai-phap-bao-hiem-tre-chuyen-bay-danh-cho-hanh-khach"],
    ["fhsc · OPES 2023", "Green SM > 1 triệu chuyến/ngày; OPES 109,3 triệu HĐ", "https://fhsc.com.vn/co-ca-tram-nghin-xe-chay-tren-duong-day-la-so-cuoc-ma-xanh-sm-nhan-moi-ngay-tai-viet-nam"],
    ["tinnhanhchungkhoan.vn", "Grab = Chubb, Be = OPES → dùng Green SM", "https://www.tinnhanhchungkhoan.vn/bao-hiem-so-don-tin-vui-tu-xe-cong-nghe-post352383.html"],
  ]],
];
SRC_GROUPS.forEach(([head, role, col, items], i) => {
  const x = 0.6 + i * 2.44;
  card(s, x, 1.3, 2.32, 5.5);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.1, y: 1.4, w: 2.12, h: 0.72, fill: { color: col }, line: { color: col }, rectRadius: 0.08, objectName: head });
  T(s, [{ text: head, options: { bold: true, fontSize: 12, breakLine: true } }, { text: role, options: { fontSize: 9.5 } }],
    { x: x + 0.18, y: 1.4, w: 1.96, h: 0.72, color: C.background1, valign: "middle" });
  const runs = [];
  items.forEach(([name, use, url], j) => {
    runs.push({ text: name, options: { hyperlink: { url }, bold: true, color: HX.accent1, fontSize: 10.5, breakLine: true } });
    runs.push({ text: use, options: Object.assign({ fontSize: 9.5, color: "4A5560", paraSpaceAfter: 4 }, j < items.length - 1 ? { breakLine: true } : {}) });
  });
  T(s, runs, { x: x + 0.14, y: 2.22, w: 2.06, h: 4.5 });
});

// ============ 3. Cấu trúc 5 bảng giao dịch ============
pres.addSection({ title: "Danh mục và giao dịch" });
s = content("Danh mục và giao dịch", "Vì sao dữ liệu chia thành 5 bảng giao dịch",
  "Mỗi bảng ứng với một quy tắc nghiệp vụ bắt buộc. Không dùng bảng phẳng vì sẽ lặp thông tin hợp đồng và không cộng đúng doanh thu khi có sửa đổi, hoàn phí (Kimball đặt grain ở giao dịch × coverage). Dataset public có cùng cách tách: fremotor1prem0304 ghi phí theo từng quyền lợi trên một hợp đồng; Synthea tách bên bảo hiểm, thời gian tham gia, giao dịch; CAS Schedule P tách phí toàn bộ và phần giữ lại.");
const box = (label, sub, x, y, w, fill) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.95, fill: { color: fill }, line: { color: fill }, rectRadius: 0.1, objectName: label });
  T(s, [{ text: label, options: { bold: true, fontSize: 15, breakLine: true } }, { text: sub, options: { fontSize: 11 } }],
    { x: x + 0.1, y, w: w - 0.2, h: 0.95, color: C.background1, valign: "middle", align: "center" });
};
const arrow = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color: MUTED, width: 1.5, endArrowType: "triangle" }, objectName: "arrow" });
box("Hợp đồng", `${vn(ROWS.policy)} dòng`, 0.6, 1.6, 2.4, C.accent1);
box("Giao dịch", `${vn(ROWS.policy_transaction)} dòng`, 3.4, 1.6, 2.4, C.accent1);
box("Dòng phí theo SP", `${vn(ROWS.transaction_coverage)} dòng`, 6.2, 1.6, 2.4, C.accent1);
box("Đồng bảo hiểm", `${vn(ROWS.coinsurance_share)} dòng`, 0.6, 3.2, 2.4, C.accent4);
box("Phân bổ doanh thu", `${vn(ROWS.revenue_allocation)} dòng`, 3.4, 3.2, 2.4, C.accent4);
arrow(3.0, 2.07, 3.4, 2.07); arrow(5.8, 2.07, 6.2, 2.07); arrow(1.8, 2.55, 1.8, 3.2); arrow(2.6, 2.55, 4.2, 3.2);
card(s, 6.2, 3.2, 2.4, 0.95);
T(s, [{ text: "16 danh mục", options: { bold: true, fontSize: 15, breakLine: true, color: C.text2 } }, { text: "xem slide sau", options: { fontSize: 11 } }],
  { x: 6.3, y: 3.2, w: 2.2, h: 0.95, align: "center", valign: "middle" });
const why = [
  ["Hợp đồng", "đơn vị giao kết pháp lý", "Luật KDBH 2022"],
  ["Giao dịch", "doanh thu phát sinh theo từng lần cấp mới, tái tục, sửa đổi, hoàn, hủy — mỗi loại một tài khoản", "NĐ 46 Đ49; TT 232"],
  ["Dòng phí theo SP", "1 hợp đồng nhiều sản phẩm (VCX + TNDS); doanh thu phải tách theo nghiệp vụ", "TT 232 Đ12; TT 67 Mẫu 2-PNT"],
  ["Đồng bảo hiểm", "hợp đồng lớn có 3–6 DN, mỗi DN chỉ ghi phần mình; kiểm tra tổng 100%", "TT 232 Đ19"],
  ["Phân bổ doanh thu", "đơn vị cấp đơn ≠ đơn vị ghi doanh thu (mô hình Tổng công ty) — giả định", "PVI 47, Bảo Việt 79 công ty"],
];
why.forEach(([h, b, sc], i) => {
  const y = 1.4 + i * 0.96;
  T(s, [{ text: h + ": ", options: { bold: true, color: C.text2 } }, { text: b }], { x: 9.0, y, w: 3.75, h: 0.62, fontSize: 11.5 });
  T(s, sc, { x: 9.0, y: y + 0.64, w: 3.75, h: 0.26, fontSize: 10.5, italic: true, color: C.accent6 });
});
T(s, "Cấu trúc hợp đồng → giao dịch → dòng phí là chuẩn của ACORD, Microsoft CDM, OMG. Dataset public cùng cách tách: CASdatasets fremotor (phí theo từng quyền lợi), Synthea (bên bảo hiểm / thời gian tham gia / giao dịch), CAS Schedule P (phí toàn bộ / phần giữ lại).",
  { x: 0.6, y: 4.55, w: 8.0, h: 1.0, fontSize: 13, color: MUTED });
src(s, "Luật KDBH 2022; NĐ 46/2023 Đ49; TT 232/2012 Đ12, Đ19; TT 67/2023 Mẫu 2-PNT; Bảo Việt Integrated Report 2024 — trang 127; pvi.com.vn/vi/network.", 6.45);

// ============ 4. Danh mục quan trọng ============
s = content("Danh mục và giao dịch", "Các danh mục quan trọng và căn cứ",
  "Mỗi chiều phân tích của đề bài có danh mục riêng, mã lấy từ văn bản pháp luật. Doanh nghiệp là Tổng Công ty Bảo hiểm PVI (công ty con 100% của PVI Holdings, BCTN 2024 trang PDF 12) với 47 đơn vị thật theo pvi.com.vn/vi/network; Hanoi Re và PVIAM không cấp hợp đồng gốc nên ngoài phạm vi. 4 sản phẩm vi mô là sản phẩm PVI có công bố (Green SM Care, Food Care, DelayCare, thiết bị điện tử trên Shopee/Lazada qua Fuse). Phần giả định: trọng số doanh thu của đơn vị (PVI không công bố doanh thu từng đơn vị); đối tác cũ và DN đồng BH ẩn danh; 6 phân khúc khách do dự án đặt.");
const cat = [[hdr("Danh mục"), hdr("Gồm"), hdr("Vì sao / căn cứ")]];
[["Nghiệp vụ & sản phẩm", "4 nghiệp vụ → 8 nhóm POC → 19 sản phẩm + 4 vi mô (Green SM Care, Food Care, DelayCare, thiết bị điện tử)", "NĐ 46 Đ4–5; TT 67 Mẫu 2-PNT, Đ51; NĐ 67; greensm.com, pvi.com.vn, help.shopee.vn"],
 ["Kênh & đối tác", "7 kênh → 3 nhóm báo cáo; đối tác ẩn danh + 3 đối tác số thật: Green SM, ATADI, Fuse", "Luật KDBH Đ87 k4; TT 67 Mẫu 3-PNT; BCTN PVI 2024 tr.29; tin PVI Digital"],
 ["Đơn vị", "Tổng Công ty Bảo hiểm PVI → Trụ sở chính, PVI Digital + 46 đơn vị (47 đơn vị thật)", "pvi.com.vn/vi/network; BCTN 2024 tr.12; trọng số doanh thu: ước tính"],
 ["Khách hàng", `${vn(ROWS.customer)} khách, 6 phân khúc; 'khách lẻ theo bảng kê' cho đơn lô`, "Phân khúc theo loại chủ thể giao kết — giả định"],
 ["Loại giao dịch", "7 loại, dấu ±, tài khoản 5111 / 5311 / 5321, mã ACORD", "NĐ 46 Đ49 k3; TT 232/2012; ACORD"],
 ["Địa bàn & tỷ giá", "34 tỉnh, 3 miền; tỷ giá USD theo tháng", "NQ 202/2025; KBNN 2025 (2024 nội suy — giả định)"],
 ["Đồng BH & phân bổ", "7 DNBH (Bảo hiểm PVI + 6 DN ẩn danh); 3 kiểu phân bổ", "Luật KDBH Đ4 k29; TT 232 Đ19; thông lệ quản trị"]].forEach(r =>
  cat.push([cell(r[0], { bold: true, color: HX.dk2 }), cell(r[1]), cell(r[2], { fontSize: 12, color: "4A5560" })]));
s.addTable(cat, { x: 0.6, y: 1.4, w: 12.1, colW: [2.4, 5.0, 4.7], rowH: 0.62, border: BORDER, valign: "middle", margin: [0, 0.1, 0, 0.1] });
src(s, "vbpl.vn (Luật KDBH, NĐ 46, NĐ 67, TT 67, TT 232, NQ 202); BCTN PVI 2024 — trang 12, 29; pvi.com.vn/vi/network; greensm.com; help.shopee.vn (bài 79225).", 6.5);

// ============ 5. Giao dịch & doanh thu ============
s = content("Danh mục và giao dịch", "Các loại giao dịch và cách tính doanh thu",
  "Doanh thu tính trên dòng phí của giao dịch đã duyệt, phần của công ty, phần phân bổ cho đơn vị. Hoàn, giảm, hủy là khoản giảm thu nên mang dấu âm. Tỷ lệ tái tục và tần suất SĐBS theo từng sản phẩm là giả định; dấu và tài khoản là quy định. Số hợp đồng năm trước của đơn tái tục lưu ở prev_policy_no (ngoài kỳ dữ liệu). Bảng dưới: GCN vi mô — mỗi GCN là 1 hợp đồng + 1 giao dịch NEW, cấp qua API của đối tác (kênh điện tử), hiệu lực trong ngày (chuyến xe, đồ ăn) hoặc 12 tháng (thiết bị điện tử); DelayCare hủy 3% trước ngày bay, thiết bị điện tử hủy 2% khi trả hàng. Đơn giá theo nguồn công khai (greensm.com, pvi.com.vn, help.shopee.vn); số GCN mỗi ngày là ước tính.");
const tx = [[hdr("Loại"), hdr("Ý nghĩa"), hdr("Dấu · TK"), { text: "Số GD", options: { bold: true, color: HX.lt1, fill: { color: HX.dk2 }, fontSize: 13, align: "right" } }]];
[["NEW", "Cấp mới", "+ · 5111"], ["RENEW", "Tái tục (HĐ cũ ở prev_policy_no)", "+ · 5111"],
 ["END_INC", "Sửa đổi tăng phí", "+ · 5111"], ["END_DEC", "Sửa đổi giảm phí", "− · 5321"],
 ["REFUND", "Hoàn phí", "− · 5311"], ["CANCEL", "Hủy, hoàn phí thời gian còn lại", "− · 5311"],
 ["END_NOCHG", "Sửa đổi không đổi phí", "0"]].map(r => [...r, vn(TXT[r[0]] || 0)]).forEach(r =>
  tx.push([cell(r[0], { bold: true, fontFace: "Consolas", fontSize: 12 }), cell(r[1]), cell(r[2]), cell(r[3], { align: "right" })]));
s.addTable(tx, { x: 0.6, y: 1.4, w: 7.0, colW: [1.5, 3.2, 1.1, 1.2], rowH: 0.4, border: BORDER, valign: "middle", margin: [0, 0.1, 0, 0.1] });
T(s, `Trạng thái: ${vn(STT.APPROVED)} đã duyệt · ${vn(STT.PENDING)} chờ duyệt (dồn 5 ngày cuối kỳ) · ${vn(STT.VOID)} hủy chứng từ — chỉ chứng từ đã duyệt được tính doanh thu.`, { x: 0.6, y: 4.68, w: 7.0, h: 0.42, fontSize: 11, color: MUTED });
const mh = (t, a = "left") => ({ text: t, options: { bold: true, color: HX.lt1, fill: { color: HX.accent2 }, fontSize: 11, align: a } });
const mt = [[mh(`Vi mô: ${vn(MIC_N / PROD_N * 100, 1)}% số HĐ, ${vn(MIC_R / REV_TOT * 100, 2)}% doanh thu`), mh("GCN", "right"), mh("Tỷ đ", "right"), mh("đ/GCN", "right")]];
MICRO.forEach(([c, n, who]) => { const v = PROD[c] || { n: 0, r: 0 };
  mt.push([cell(`${n} · ${who}`, { fontSize: 11 }), cell(vn(v.n), { fontSize: 11, align: "right" }), cell(vn(v.r, 2), { fontSize: 11, align: "right" }), cell(vn(v.n ? v.r * 1e9 / v.n : 0), { fontSize: 11, align: "right" })]); });
s.addTable(mt, { x: 0.6, y: 5.12, w: 7.0, colW: [3.9, 1.2, 0.8, 1.1], rowH: 0.25, border: BORDER, valign: "middle", margin: [0, 0.08, 0, 0.08] });
card(s, 8.0, 1.4, 4.7, 4.75);
T(s, "Doanh thu =", { x: 8.3, y: 1.55, w: 4.1, h: 0.45, fontSize: 17, bold: true, color: C.text2 });
[["Phí 100% hợp đồng", "VND, chưa VAT", C.accent1], ["× phần của công ty", "khi đồng bảo hiểm", C.accent3], ["× tỷ lệ phân bổ", "cho đơn vị", C.accent4]].forEach(([a, b, col], i) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.3, y: 2.05 + i * 0.75, w: 4.1, h: 0.62, fill: { color: col }, line: { color: col }, rectRadius: 0.08, objectName: a });
  T(s, [{ text: a + "  ", options: { bold: true, fontSize: 14 } }, { text: b, options: { fontSize: 12 } }], { x: 8.45, y: 2.05 + i * 0.75, w: 3.8, h: 0.62, color: C.background1, valign: "middle" });
});
T(s, [{ text: "Chỉ chứng từ đã duyệt", options: { bullet: true, breakLine: true } },
  { text: "Ghi nhận khi phát sinh trách nhiệm: ngày muộn hơn giữa ngày cấp và ngày hiệu lực (TT 67 Đ41)", options: { bullet: true, breakLine: true } },
  { text: "Hoàn, giảm, hủy: số âm vào kỳ phát sinh (NĐ 46 Đ49)", options: { bullet: true, breakLine: true } },
  { text: "Đồng BH: chỉ phần của mình (TT 232 Đ19)", options: { bullet: true } }],
  { x: 8.3, y: 4.35, w: 4.2, h: 1.75, fontSize: 12, paraSpaceAfter: 4 });
src(s, "NĐ 46/2023 Đ49 k3; TT 232/2012; TT 67/2023 Đ41; ACORD (NBS / RWL / PCH / XLC); vi mô: greensm.com, pvi.com.vn (DelayCare), help.shopee.vn; số đo: bronze.ins_*.", 6.48);

// ============ 6. Cơ chế & con số doanh thu ============
pres.addSection({ title: "Cơ chế và căn cứ" });
s = content("Cơ chế và căn cứ", `Cơ chế sinh và vì sao doanh thu tháng 8–9 là ${vn(REV_TOT)} tỷ`,
  "Ngân sách = mục tiêu năm theo BCTC PVI 2025 (trang 45) × tỷ trọng tháng 8, 9 của toàn thị trường 2025 (Bộ Tài chính: 5.592 và 8.002 trên 88.054 tỷ) — đúng quy mô PVI, không nhân hệ số quy mô (bản trước nhân k ≈ 3,93, nay đã bỏ). Sản phẩm truyền thống ở quy mô này chỉ cho khoảng 12–18 nghìn giao dịch/ngày; phần còn lại đến từ bảo hiểm vi mô PVI có công bố: Green SM Care 40.000, Food Care 8.000, thiết bị điện tử 3.000, DelayCare 300 GCN/ngày (ước tính có căn cứ: Green SM > 1 triệu chuyến/ngày × 20% mua × 20% về PVI). Phí 1.000–2.000 đ nên vi mô chỉ khoảng 1,3% doanh thu; nó nằm trong ngân sách nhóm và được coi là dòng cố định khi hiệu chỉnh. Đơn doanh nghiệp, nhóm, lô được co giãn để khớp ngân sách từng đợt 7 ngày.");
[["Ngân sách", "BCTC PVI × tỷ trọng tháng"], ["Số đơn", "ngân sách ÷ đơn giá; vi mô theo ngày"], ["Sinh hợp đồng", "theo dáng sản phẩm"], ["Hiệu chỉnh", "khớp ngân sách"], ["Tái tục & SĐBS", "theo sản phẩm"], ["Kiểm tra & nạp", "reportapi"]].forEach(([h, b], i) => {
  const x = 0.6 + i * 2.06;
  card(s, x, 1.4, 1.86, 1.35, i === 3 ? "FBE9DF" : C.background2, `step ${i + 1}`);
  num(s, i + 1, x + 0.12, 1.52, 0.42, i === 3 ? C.accent2 : C.accent1);
  T(s, h, { x: x + 0.6, y: 1.5, w: 1.22, h: 0.55, fontSize: 12.5, bold: true, color: C.text2, valign: "middle" });
  T(s, b, { x: x + 0.15, y: 2.15, w: 1.6, h: 0.45, fontSize: 12, color: MUTED });
});
[["Mục tiêu năm (BCTC PVI)", "10.377,9", C.accent3], ["Tỷ trọng T8 + T9", "15,44%", C.accent4], ["Ngân sách PVI 2 tháng", vn(BUDGET_PVI, 1), C.accent3], ["Phí gốc khai thác trên DB", vn(WRITTEN_TOT, 1), C.accent1], ["GCN vi mô/ngày (≈ 1,3% DT)", "≈ 51.000", C.accent2]].forEach(([l, v, col], i) => {
  const x = 0.6 + i * 2.42;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.1, w: 2.1, h: 1.05, fill: { color: col }, line: { color: col }, rectRadius: 0.1, objectName: l });
  T(s, [{ text: v, options: { bold: true, fontSize: 20, breakLine: true } }, { text: l, options: { fontSize: 12 } }], { x: x + 0.1, y: 3.1, w: 1.9, h: 1.05, color: C.background1, align: "center", valign: "middle" });
  if (i < 3) T(s, ["×", "=", "≈"][i], { x: x + 2.1, y: 3.1, w: 0.32, h: 1.05, fontSize: 22, bold: true, color: C.text2, align: "center", valign: "middle" });
});
[[`${vn(WRITTEN_TOT, 1)} tỷ`, `phí gốc cấp mới + tái tục đã duyệt, lệch ${vn((WRITTEN_TOT / BUDGET_PVI - 1) * 100, 1)}% so với ngân sách PVI — không hệ số k; ngày thấp nhất ${vn(TPD[8].mn)} giao dịch nhờ GCN vi mô`],
 [`− ${vn(DB.spill_after[0][0], 1)} tỷ`, "đơn hiệu lực sau 30/9 (chủ yếu du lịch mua trước chuyến đi) → ghi nhận sau kỳ (TT 67 Đ41)"],
 [`= ${vn(REV_TOT, 1)} tỷ`, `doanh thu ghi nhận tháng 8–9 trên DB, đã gồm ${vn(DB.deductions[0][0], 1)} tỷ sửa đổi giảm phí, hoàn phí, hủy (khoản giảm thu)`]].forEach(([v, d], i) => {
  const y = 4.45 + i * 0.55;
  T(s, v, { x: 0.6, y, w: 1.8, h: 0.45, fontSize: 16, bold: true, color: i === 2 ? C.accent1 : C.accent2, valign: "middle" });
  T(s, d, { x: 2.45, y, w: 10.2, h: 0.45, fontSize: 13, valign: "middle" });
});
src(s, "BCTC kiểm toán 2025 Bảo hiểm PVI, thuyết minh 21 — trang 45 (bản scan); Bộ Tài chính, bản tin tháng 8, 9/2025 và 01/2026; greensm.com, fhsc.com.vn (Green SM > 1 triệu chuyến/ngày); số đo: bronze.ins_* trên reportapi.");

// ============ 7. Phân phối ============
s = content("Cơ chế và căn cứ", "Phân phối: tần suất × độ lớn, và vì sao khách cá nhân ít tiền",
  `Bán lẻ nhiều đơn nhỏ, doanh nghiệp ít đơn nhưng phí lớn. Cá nhân nhiều hợp đồng vì mỗi người mua theo từng xe / chuyến / người; ít tiền vì phí theo biểu phí và giá niêm yết nhỏ. PVI tập trung khách doanh nghiệp (FPTS trang 14). Cột số hợp đồng là kết quả của giả định (ngân sách ÷ đơn giá, cộng GCN vi mô theo ngày); cột doanh thu neo theo BCTC. Biểu đồ tách bảo hiểm vi mô thành cột riêng: vi mô ${vn(POL_C.VI_MO / POL_TOT * 100, 1)}% số hợp đồng nhưng ${vn(REV_C.VI_MO / REV_TOT * 100, 1)}% doanh thu; nếu gộp vào Sinh mạng thì Sinh mạng chiếm ${vn((POL.SINH_MANG || 0) / POL_TOT * 100, 1)}% số hợp đồng. Thêm vi mô làm phân phối lệch hơn: 10% hợp đồng lớn nhất chiếm ${vn(DB.top_share[0][0] * 100, 1)}% doanh thu, 1% chiếm ${vn(DB.top_share[0][1] * 100, 1)}%; quy mô và cơ cấu doanh thu không đổi. Đây là đặc trưng thật của bảo hiểm nhúng (OPES 109,3 triệu hợp đồng năm 2023) — dashboard nên tách số giao dịch và doanh thu. Trên DB: cá nhân định danh ${vn(SEG.CA_NHAN.n / SEG_N * 100, 1)}% hợp đồng, ${vn(SEG.CA_NHAN.r / SEG_R * 100, 1)}% doanh thu; khách lẻ mua qua đối tác ${vn((SEG.KHACH_LE_GOP || { n: 0 }).n / SEG_N * 100, 1)}% hợp đồng, ${vn((SEG.KHACH_LE_GOP || { r: 0 }).r / SEG_R * 100, 1)}% doanh thu.`);
const grp = CGROUPS.map(g => g === "VI_MO" ? "Vi mô" : GNAME[g]);
s.addChart(pres.charts.BAR, [
  { name: "% số hợp đồng", labels: grp, values: CGROUPS.map(g => +((POL_C[g] || 0) / POL_TOT * 100).toFixed(1)) },
  { name: "% doanh thu", labels: grp, values: CGROUPS.map(g => +((REV_C[g] || 0) / REV_TOT * 100).toFixed(1)) },
], Object.assign({ x: 0.5, y: 1.35, w: 7.4, h: 4.95, barDir: "col", barGapWidthPct: 60, chartColors: [HX.accent4, HX.accent2],
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", showLegend: true, legendPos: "t",
  valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showTitle: true, title: "Theo nhóm sản phẩm, tháng 8–9/2026 (%)", titleFontSize: 13, titleColor: HX.dk2 }, axis));
[[`Cháy nổ + tài sản: ${vn(((POL.CHAY_NO || 0) + (POL.TAI_SAN || 0)) / POL_TOT * 100, 1)}% đơn → ${vn(((REV.CHAY_NO || 0) + (REV.TAI_SAN || 0)) / REV_TOT * 100, 1)}% doanh thu`, "1 đơn nhà máy: STBH hàng trăm tỷ × tối thiểu 0,05–0,5% (NĐ 67 PL II) = hàng trăm triệu đến hàng tỷ."],
 [`Cá nhân: ${vn((SEG.CA_NHAN.n + (SEG.KHACH_LE_GOP || { n: 0 }).n) / SEG_N * 100, 1)}% đơn → ${vn((SEG.CA_NHAN.r + (SEG.KHACH_LE_GOP || { r: 0 }).r) / SEG_R * 100, 1)}% doanh thu`, "Gồm cả khách lẻ mua qua đối tác. TNDS ô tô 437.000 đ, xe máy 60.000 đ, du lịch từ 17.000 đ, sức khỏe từ 1,45 triệu — mỗi người một hợp đồng."],
 [`Vi mô: ${vn(MIC_N / PROD_N * 100, 1)}% đơn → ${vn(MIC_R / REV_TOT * 100, 1)}% doanh thu`, `${vn(MIC_N)} GCN, ${vn(MIC_R, 1)} tỷ. Quy mô không đổi; 10% HĐ lớn nhất chiếm ${vn(DB.top_share[0][0] * 100, 1)}% doanh thu. PVI vẫn thiên khách DN (FPTS tr.14).`]].forEach(([h, b], i) => {
  card(s, 8.2, 1.4 + i * 1.62, 4.5, 1.47);
  T(s, [{ text: h, options: { bold: true, fontSize: 14, color: C.accent2, breakLine: true } }, { text: b, options: { fontSize: 12 } }], { x: 8.4, y: 1.5 + i * 1.62, w: 4.1, h: 1.3 });
});
src(s, "NĐ 67/2023 Phụ lục I, II; giá niêm yết online.pvi.com.vn; FPTS định giá PVI 04/2025 — trang 14; greensm.com; opes.com.vn; tỷ lệ % theo phân khúc: giả định.", 6.45);

// ============ 8. Giả định ============
s = content("Cơ chế và căn cứ", "Các giả định: cơ sở là gì, vì sao hợp lý với POC",
  "Tổng từng nghiệp vụ luôn đúng số công bố; giả định chỉ quyết định phần chia chi tiết. Đổi giả định thì chạy lại, bước hiệu chỉnh tự kéo về mục tiêu. Những gì ngẫu nhiên (ngày trong tháng, giá xe, STBH, cỡ lô, tỷ lệ phí trong khoảng, hệ số tái tục, hoa hồng dưới trần, tên khách) chỉ cần một câu: chọn ngẫu nhiên trong khoảng hợp lý, tổng đã hiệu chỉnh nên không đổi doanh thu nhóm.");
const at = [[hdr("Giả định"), hdr("Cơ sở (nguồn, trang)"), hdr("Lý do phạm vi POC"), hdr("Ảnh hưởng")]];
const lv = (t) => ({ text: t, options: { bold: true, color: t === "Cao" ? HX.accent2 : HX.accent6, fontSize: 12 } });
[["Tài sản thuần = 50% dòng Tài sản", "BCTC không tách năng lượng, kỹ thuật (tr.45); PVI có nghiệp vụ năng lượng (BCTN 2024 tr.57)", "Đề bài chỉ có tài sản, cháy nổ", "Cao"],
 ["Con người 75 / 15 / 5 / 5", "Con người PVI tập trung khách DN (FPTS tr.14); du lịch, học sinh phí nhỏ", "PVI không công bố tỷ lệ tách", "Cao"],
 ["TNDS 24% / vật chất xe 76%", "Tỷ lệ toàn thị trường IAV 2024: 4.537 / 18.693 tỷ", "PVI không công bố riêng", "Vừa"],
 ["40.000 GCN chuyến xe/ngày (+ 11.300 vi mô khác)", "Green SM > 1 triệu chuyến/ngày (fhsc) × 20% mua × 20% về PVI (1/5 nhà BH, greensm.com); OPES 109,3 triệu HĐ 2023", "> 50.000 giao dịch/ngày mà giữ doanh thu PVI", "Vừa"],
 ["Trọng số doanh thu 47 đơn vị", "Theo kinh tế địa bàn; ×1,5 đơn vị được vinh danh (tin PVI, pvisg.net); PVI không công bố doanh thu đơn vị", "Có chiều Đơn vị thật để kiểm thử", "Vừa"],
 ["Mùa vụ tháng theo thị trường", "Bộ Tài chính 2025: T8 6,35%, T9 9,09% phí gốc cả năm; năm 2026 dùng quy mô 2025", "Chưa có số tháng của PVI", "Vừa"],
 ["Trọng số kênh theo từng sản phẩm", `Định hướng: TMĐT ≈ 800 tỷ 2024 (BCTN tr.29), môi giới thị trường 13,5%; trên DB điện tử ${vn((CH.DIEN_TU || 0) / CH_TOT * 100, 1)}% doanh thu (thấp hơn ~10% của PVI)`, "Đủ 7 kênh, 3 nhóm Mẫu 3-PNT", "Vừa"],
 ["Đồng BH khi STBH ≥ 300 tỷ", "Liên danh thực tế: Vietnam Airlines 3 DN, Long Thành 6 DN, Vinalines", "Có kịch bản đứng đầu / tham gia", "Vừa"]].forEach(r =>
  at.push([cell(r[0], { bold: true, fontSize: 12 }), cell(r[1], { fontSize: 11 }), cell(r[2], { fontSize: 11 }), { text: [lv(r[3])] }]));
s.addTable(at, { x: 0.6, y: 1.35, w: 12.1, colW: [3.0, 5.4, 2.6, 1.1], rowH: 0.5, border: BORDER, valign: "middle", margin: [0, 0.1, 0, 0.1] });
T(s, [{ text: "Tham số ngẫu nhiên: ", options: { bold: true, color: C.text2 } },
  { text: "chọn ngẫu nhiên trong khoảng hợp lý (ngày, giá xe, STBH, cỡ lô, tỷ lệ phí); tổng đã hiệu chỉnh nên không đổi doanh thu." }],
  { x: 0.6, y: 6.0, w: 12.1, h: 0.4, fontSize: 13 });
src(s, "BCTC kiểm toán PVI 2025 — tr.45; BCTN PVI 2024 — tr.29, 57; FPTS — tr.14; IAV 2024; fhsc.com.vn, greensm.com, opes.com.vn; pvi.com.vn, pvisg.net; fireant.vn, baodauthau.vn.", 6.55);

// ============ 9. Kết quả, giới hạn, nguồn ============
pres.addSection({ title: "Kết quả" });
s = content("Kết quả", "Kết quả, giới hạn và ba con số cần nhớ",
  "Số đo trực tiếp trên reportapi sau lần nạp lại 19/10/2026 (khóa 60.000.001–64.082.637, không dùng lại khóa cũ nhờ bảng watermark). Doanh thu đúng quy mô PVI, không hệ số k; cơ cấu khớp BCTC PVI vì đã hiệu chỉnh theo ngân sách từng nhóm. Vi mô chiếm phần lớn số hợp đồng nhưng khoảng 1,3% doanh thu. Giới hạn cần chủ động nói với khách: số GCN vi mô và doanh thu từng đơn vị PVI là ước tính. Danh mục đầy đủ 60 nguồn và sổ 88 tham số nằm trong Logic_Sinh_Du_Lieu.html; hỏi đáp đầy đủ trong HOI_DAP_TAI_SAO.md.");
card(s, 0.6, 1.4, 3.9, 4.9);
T(s, "Kết quả T8–T9/2026 (trên DB)", { x: 0.85, y: 1.55, w: 3.4, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
T(s, "Dummy · Công bố", { x: 2.3, y: 1.98, w: 2.0, h: 0.3, fontSize: 11, color: MUTED, align: "right" });
[["Tài sản + cháy nổ", vn(MIX.TS, 1) + "%", "51,5%"], ["Con người", vn(MIX.NG, 1) + "%", "31,0%"], ["Xe", vn(MIX.XE, 1) + "%", "17,6%"]].forEach(([a, b, c], i) => {
  T(s, a, { x: 0.85, y: 2.35 + i * 0.5, w: 1.8, h: 0.45, fontSize: 13, valign: "middle" });
  T(s, [{ text: b, options: { bold: true, color: HX.accent1 } }, { text: "  " + c, options: { color: MUTED } }], { x: 2.3, y: 2.35 + i * 0.5, w: 2.0, h: 0.45, fontSize: 15, align: "right", valign: "middle" });
});
T(s, [{ text: "Doanh thu: ", options: { bold: true } }, { text: `${vn(REV_TOT)} tỷ (T8 ${vn(REV_M[8])} · T9 ${vn(REV_M[9])}) = quy mô PVI`, options: { breakLine: true } },
  { text: "Giao dịch/ngày: ", options: { bold: true } }, { text: `T8 ${vn(TPD[8].mn)}–${vn(TPD[8].mx)} · T9 ${vn(TPD[9].mn)}–${vn(TPD[9].mx)}`, options: { breakLine: true } },
  { text: "Kênh điện tử: ", options: { bold: true } }, { text: `${vn((CH.DIEN_TU || 0) / CH_TOT * 100, 1)}% doanh thu (PVI ≈ 6–10%)` }],
  { x: 0.85, y: 4.0, w: 3.45, h: 2.1, fontSize: 13, paraSpaceAfter: 6 });
card(s, 4.7, 1.4, 3.9, 4.9, "FBE9DF");
T(s, "Giới hạn", { x: 4.95, y: 1.55, w: 3.4, h: 0.4, fontSize: 16, bold: true, color: C.accent2 });
T(s, [{ text: "Số GCN vi mô/ngày và doanh thu từng đơn vị PVI là ước tính (PVI không công bố)", options: { bullet: true, breakLine: true } },
  { text: `Vi mô ${vn(MIC_N / PROD_N * 100, 0)}% số hợp đồng nhưng ${vn(MIC_R / REV_TOT * 100, 1)}% doanh thu — tách số giao dịch và doanh thu`, options: { bullet: true, breakLine: true } },
  { text: "Chia con trong nghiệp vụ là giả định; tổng đúng số công bố", options: { bullet: true, breakLine: true } },
  { text: "Tỷ lệ phí cháy nổ theo NĐ 67 bản 2023 (bản thay thế chỉ có scan)", options: { bullet: true } }],
  { x: 4.95, y: 2.05, w: 3.45, h: 4.1, fontSize: 13, paraSpaceAfter: 8 });
card(s, 8.8, 1.4, 3.9, 4.9);
T(s, "Ba con số cần nhớ", { x: 9.05, y: 1.55, w: 3.4, h: 0.4, fontSize: 16, bold: true, color: C.text2 });
[[`${vn(TPD[8].mn)}+`, `giao dịch/ngày thấp nhất (T8 ${vn(TPD[8].mn)}–${vn(TPD[8].mx)}, T9 ${vn(TPD[9].mn)}–${vn(TPD[9].mx)})`, C.accent1],
 [`${vn(MIX.TS, 1)} / ${vn(MIX.NG, 1)} / ${vn(MIX.XE, 1)}`, "% doanh thu tài sản / con người / xe — khớp BCTC PVI 51,5 / 31,0 / 17,6", C.accent3],
 ["88 tham số", "đều có căn cứ; 64 có phần giả định, mỗi giả định có cơ sở", C.accent2]].forEach(([big, lab, col], i) => {
  T(s, big, { x: 9.05, y: 2.1 + i * 1.35, w: 3.4, h: 0.6, fontSize: 28, bold: true, color: col, fontFace: THEME.headFontFace, valign: "middle" });
  T(s, lab, { x: 9.05, y: 2.7 + i * 1.35, w: 3.4, h: 0.6, fontSize: 12, color: MUTED });
});

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("written", OUT);
})();
