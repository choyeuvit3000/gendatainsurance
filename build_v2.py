r"""
POC Doanh thu bảo hiểm — v2: sinh dữ liệu dummy từ danh mục chuẩn hóa theo nguồn PUBLIC.
Không kết nối / không dùng dữ liệu nội bộ của khách hàng.

Chạy:   python build_v2.py
Ra:     02_data.sql (INSERT, PostgreSQL)
Căn cứ: DESIGN_RATIONALE.md, sources/*.md
"""
import datetime as dt
import math
import random
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

OUT = Path(__file__).parent
rnd = random.Random(2026)
YEARS = [2024, 2025]
D = Decimal

# ============================================================================
# 1. DANH MỤC (REF) — dựng từ nguồn public
# ============================================================================
REGIONS = [("BAC", "Miền Bắc"), ("TRUNG", "Miền Trung"), ("NAM", "Miền Nam")]

# 34 tỉnh/thành sau sắp xếp ĐVHC 2025 (Nghị quyết 202/2025/QH15)
PROVINCES = [
    ("HNI", "Thành phố Hà Nội", "BAC"), ("HPG", "Thành phố Hải Phòng", "BAC"), ("QNH", "Tỉnh Quảng Ninh", "BAC"),
    ("BNH", "Tỉnh Bắc Ninh", "BAC"), ("HYN", "Tỉnh Hưng Yên", "BAC"), ("NBH", "Tỉnh Ninh Bình", "BAC"),
    ("PTO", "Tỉnh Phú Thọ", "BAC"), ("TNN", "Tỉnh Thái Nguyên", "BAC"), ("TQG", "Tỉnh Tuyên Quang", "BAC"),
    ("LCI", "Tỉnh Lào Cai", "BAC"), ("LSN", "Tỉnh Lạng Sơn", "BAC"), ("CBG", "Tỉnh Cao Bằng", "BAC"),
    ("DBN", "Tỉnh Điện Biên", "BAC"), ("LCU", "Tỉnh Lai Châu", "BAC"), ("SLA", "Tỉnh Sơn La", "BAC"),
    ("THA", "Tỉnh Thanh Hóa", "TRUNG"), ("NAN", "Tỉnh Nghệ An", "TRUNG"), ("HTH", "Tỉnh Hà Tĩnh", "TRUNG"),
    ("QTR", "Tỉnh Quảng Trị", "TRUNG"), ("HUE", "Thành phố Huế", "TRUNG"), ("DNG", "Thành phố Đà Nẵng", "TRUNG"),
    ("QNG", "Tỉnh Quảng Ngãi", "TRUNG"), ("GLI", "Tỉnh Gia Lai", "TRUNG"), ("KHA", "Tỉnh Khánh Hòa", "TRUNG"),
    ("DLK", "Tỉnh Đắk Lắk", "TRUNG"), ("LDG", "Tỉnh Lâm Đồng", "TRUNG"),
    ("HCM", "Thành phố Hồ Chí Minh", "NAM"), ("DNI", "Tỉnh Đồng Nai", "NAM"), ("TNH", "Tỉnh Tây Ninh", "NAM"),
    ("CTO", "Thành phố Cần Thơ", "NAM"), ("VLG", "Tỉnh Vĩnh Long", "NAM"), ("DTP", "Tỉnh Đồng Tháp", "NAM"),
    ("CMU", "Tỉnh Cà Mau", "NAM"), ("AGG", "Tỉnh An Giang", "NAM"),
]

CORP = ("DEMO", "Tổng công ty Bảo hiểm DEMO (doanh nghiệp giả lập)")
# (code, name, type, province, trọng số khai thác)
COMPANIES = [
    ("HO", "Khối Trụ sở chính – Ban Kinh doanh trực tiếp", "HEAD_OFFICE", "HNI", 0),
    ("DGT", "Trung tâm Kinh doanh số", "DIGITAL", None, 0),
    ("HN1", "Công ty Bảo hiểm DEMO Hà Nội", "MEMBER", "HNI", 10), ("HN2", "Công ty Bảo hiểm DEMO Bắc Hà Nội", "MEMBER", "HNI", 7),
    ("HN3", "Công ty Bảo hiểm DEMO Tây Hà Nội", "MEMBER", "HNI", 6), ("HPG", "Công ty Bảo hiểm DEMO Hải Phòng", "MEMBER", "HPG", 5),
    ("QNH", "Công ty Bảo hiểm DEMO Quảng Ninh", "MEMBER", "QNH", 3), ("BNH", "Công ty Bảo hiểm DEMO Bắc Ninh", "MEMBER", "BNH", 4),
    ("THA", "Công ty Bảo hiểm DEMO Thanh Hóa", "MEMBER", "THA", 3), ("NAN", "Công ty Bảo hiểm DEMO Nghệ An", "MEMBER", "NAN", 3),
    ("HUE", "Công ty Bảo hiểm DEMO Huế", "MEMBER", "HUE", 2), ("DNG", "Công ty Bảo hiểm DEMO Đà Nẵng", "MEMBER", "DNG", 5),
    ("KHA", "Công ty Bảo hiểm DEMO Khánh Hòa", "MEMBER", "KHA", 3), ("DLK", "Công ty Bảo hiểm DEMO Đắk Lắk", "MEMBER", "DLK", 2),
    ("HC1", "Công ty Bảo hiểm DEMO TP. Hồ Chí Minh", "MEMBER", "HCM", 10), ("HC2", "Công ty Bảo hiểm DEMO Đông TP. Hồ Chí Minh", "MEMBER", "HCM", 7),
    ("HC3", "Công ty Bảo hiểm DEMO Bình Dương", "MEMBER", "HCM", 5), ("DNI", "Công ty Bảo hiểm DEMO Đồng Nai", "MEMBER", "DNI", 4),
    ("CTO", "Công ty Bảo hiểm DEMO Cần Thơ", "MEMBER", "CTO", 3), ("AGG", "Công ty Bảo hiểm DEMO An Giang", "MEMBER", "AGG", 2),
]
MEMBERS = [c for c in COMPANIES if c[2] == "MEMBER"]

LAW = "Luật KDBH 2022 (08/2022/QH15)"
ND46 = "NĐ 46/2023/NĐ-CP"
TT67 = "TT 67/2023/TT-BTC"
LOBS = [
    # code, name, loại hình (Luật KDBH Đ7 k1), poc group, poc name, legal basis
    ("SUC_KHOE", "Bảo hiểm sức khỏe", "Bảo hiểm sức khỏe", "CON_NGUOI", "Con người",
     f"{LAW} Điều 4 k15, Điều 7 k1 điểm b; {ND46} Điều 5"),
    ("XE_CO_GIOI", "Bảo hiểm xe cơ giới", "Bảo hiểm phi nhân thọ", "XE", "Xe cơ giới", f"{LAW} Điều 7 k1 điểm c; {ND46} Điều 4"),
    ("CHAY_NO", "Bảo hiểm cháy, nổ", "Bảo hiểm phi nhân thọ", "TAI_SAN", "Tài sản", f"{LAW} Điều 7 k1 điểm c; {ND46} Điều 4"),
    ("TAI_SAN", "Bảo hiểm tài sản", "Bảo hiểm phi nhân thọ", "TAI_SAN", "Tài sản", f"{LAW} Điều 7 k1 điểm c; {ND46} Điều 4"),
]
PL6 = f"{TT67} Phụ lục VI – Mẫu 1-PNT/2-PNT"
REG_LINES = [  # code, name, parent
    ("A", "Bảo hiểm sức khỏe", None), ("A.1", "Bảo hiểm sức khỏe, thân thể", "A"), ("A.2", "Bảo hiểm chi phí y tế", "A"),
    ("B", "Bảo hiểm phi nhân thọ", None),
    ("B.1", "Bảo hiểm tài sản", "B"), ("B.1b", "Bảo hiểm tài sản khác", "B.1"),
    ("B.4", "Bảo hiểm xe cơ giới", "B"), ("B.4a", "Bảo hiểm bắt buộc TNDS của chủ xe cơ giới", "B.4"),
    ("B.4a.1", "TNDS bắt buộc – mô tô, xe gắn máy", "B.4a"), ("B.4a.2", "TNDS bắt buộc – ô tô", "B.4a"),
    ("B.4b", "Bảo hiểm vật chất xe cơ giới", "B.4"),
    ("B.5", "Bảo hiểm cháy, nổ", "B"), ("B.5a", "Bảo hiểm cháy, nổ bắt buộc", "B.5"), ("B.5b", "Bảo hiểm cháy, nổ khác", "B.5"),
]
PRODUCT_GROUPS = [
    ("TNDS_BB", "BH bắt buộc TNDS chủ xe", "XE_CO_GIOI", 1), ("VCX", "BH vật chất xe", "XE_CO_GIOI", 2),
    ("HOC_SINH", "BH học sinh – sinh viên", "SUC_KHOE", 3), ("DU_LICH", "BH du lịch", "SUC_KHOE", 4),
    ("SINH_MANG", "BH sinh mạng – tai nạn", "SUC_KHOE", 5), ("SUC_KHOE", "BH sức khỏe", "SUC_KHOE", 6),
    ("TAI_SAN", "BH tài sản", "TAI_SAN", 7), ("CHAY_NO", "BH cháy nổ", "CHAY_NO", 8),
]
ND67 = "NĐ 67/2023/NĐ-CP Phụ lục I (biểu phí TNDS bắt buộc)"
ND67_CN = "NĐ 67/2023/NĐ-CP Phụ lục II; thay thế bởi NĐ 105/2025/NĐ-CP Phụ lục VI từ 01/7/2025"
VAT0 = "Không chịu thuế GTGT – Luật Thuế GTGT 48/2024/QH15 Điều 5 k8"
# code, name, group, report line, compulsory, pricing basis, vat, max commission % (TT 67 Đ51), legal basis
PRODUCTS = [
    ("XE_TNDS_OTO", "Bảo hiểm bắt buộc trách nhiệm dân sự của chủ xe ô tô", "TNDS_BB", "B.4a.2", 1, "TARIFF", 10, 5, ND67),
    ("XE_TNDS_MOTO", "Bảo hiểm bắt buộc trách nhiệm dân sự của chủ xe mô tô, xe gắn máy", "TNDS_BB", "B.4a.1", 1, "TARIFF", 10, 20, ND67),
    ("XE_VCX_OTO", "Bảo hiểm vật chất xe ô tô", "VCX", "B.4b", 0, "RATE_ON_SI", 10, 10, None),
    ("XE_VCX_MOTO", "Bảo hiểm vật chất xe mô tô, xe máy", "VCX", "B.4b", 0, "RATE_ON_SI", 10, 10, None),
    ("NG_HSSV_TN", "Bảo hiểm tai nạn học sinh, sinh viên", "HOC_SINH", "A.1", 0, "PER_PERSON", 0, 20, VAT0),
    ("NG_HSSV_SK", "Bảo hiểm sức khỏe toàn diện học sinh, sinh viên", "HOC_SINH", "A.2", 0, "PER_PERSON", 0, 20, VAT0),
    ("NG_DL_ND", "Bảo hiểm du lịch trong nước", "DU_LICH", "A.2", 0, "PER_PERSON", 0, 20, VAT0),
    ("NG_DL_QT", "Bảo hiểm du lịch quốc tế", "DU_LICH", "A.2", 0, "PER_PERSON", 0, 20, VAT0),
    ("NG_SM_CN", "Bảo hiểm sinh mạng cá nhân", "SINH_MANG", "A.1", 0, "RATE_ON_SI", 0, 20, VAT0),
    ("NG_NVV", "Bảo hiểm người vay vốn", "SINH_MANG", "A.1", 0, "RATE_ON_SI", 0, 20, VAT0),
    ("NG_TN24", "Bảo hiểm tai nạn con người 24/24", "SINH_MANG", "A.1", 0, "RATE_ON_SI", 0, 20, VAT0),
    ("NG_SK_CN", "Bảo hiểm sức khỏe cá nhân", "SUC_KHOE", "A.2", 0, "PER_PERSON", 0, 20, VAT0),
    ("NG_SK_NHOM", "Bảo hiểm sức khỏe nhóm doanh nghiệp", "SUC_KHOE", "A.2", 0, "PER_PERSON", 0, 20, VAT0),
    ("NG_SK_BHN", "Bảo hiểm bệnh hiểm nghèo – ung thư", "SUC_KHOE", "A.1", 0, "PER_PERSON", 0, 20, VAT0),
    ("TS_NHA", "Bảo hiểm nhà tư nhân", "TAI_SAN", "B.1b", 0, "RATE_ON_SI", 10, 5, None),
    ("TS_MRR", "Bảo hiểm mọi rủi ro tài sản", "TAI_SAN", "B.1b", 0, "RATE_ON_SI", 10, 5, None),
    ("TS_MRRCN", "Bảo hiểm mọi rủi ro công nghiệp", "TAI_SAN", "B.1b", 0, "RATE_ON_SI", 10, 5, None),
    ("CHN_BB", "Bảo hiểm cháy, nổ bắt buộc", "CHAY_NO", "B.5a", 1, "RATE_ON_SI", 10, 5, ND67_CN),
    ("CHN_TN", "Bảo hiểm cháy và các rủi ro đặc biệt (tự nguyện)", "CHAY_NO", "B.5b", 0, "RATE_ON_SI", 10, 10, None),
]
PROD = {p[0]: p for p in PRODUCTS}
# Đối chiếu quốc tế — Solvency II non-life LoB (Delegated Reg. 2015/35 Annex I). (*) = suy luận theo bản chất rủi ro
S2_MED, S2_INC = "1 Medical expense insurance", "2 Income protection insurance"
S2_MTPL, S2_MOTH, S2_FIRE = "4 Motor vehicle liability insurance", "5 Other motor insurance", "7 Fire and other damage to property insurance"
SOLVENCY2 = {
    "XE_TNDS_OTO": S2_MTPL, "XE_TNDS_MOTO": S2_MTPL, "XE_VCX_OTO": S2_MOTH, "XE_VCX_MOTO": S2_MOTH,
    "NG_HSSV_TN": S2_INC + " (*)", "NG_HSSV_SK": S2_MED, "NG_DL_ND": S2_MED + " (*)", "NG_DL_QT": S2_MED + " (*)",
    "NG_SM_CN": S2_INC + " (*)", "NG_NVV": S2_INC + " (*)", "NG_TN24": S2_INC + " (*)",
    "NG_SK_CN": S2_MED, "NG_SK_NHOM": S2_MED, "NG_SK_BHN": S2_INC + " (*)",
    "TS_NHA": S2_FIRE, "TS_MRR": S2_FIRE, "TS_MRRCN": S2_FIRE, "CHN_BB": S2_FIRE, "CHN_TN": S2_FIRE,
}
# Đối chiếu ACORD P&C BusinessPurposeTypeCd
ACORD_TXN = {"NEW": "NBS", "RENEW": "RWL", "END_INC": "PCH", "END_DEC": "PCH", "REFUND": "PCH", "CANCEL": "XLC", "END_NOCHG": "PCH"}

TCTD, MANG, KHAC = "Qua tổ chức tín dụng", "Qua môi trường mạng", "Qua kênh phân phối khác"  # nhóm kênh Mẫu 3-PNT
CHANNELS = [
    ("TRUC_TIEP", "Bán trực tiếp", KHAC, f"{LAW} Điều 87 k4 điểm a", 1),
    ("DAI_LY_CN", "Đại lý cá nhân", KHAC, f"{LAW} Điều 87 k4 điểm b; Điều 124", 2),
    ("DAI_LY_TC", "Đại lý tổ chức", KHAC, f"{LAW} Điều 87 k4 điểm b; Điều 124", 3),
    ("BANCA", "Bancassurance (đại lý là tổ chức tín dụng)", TCTD, f"{LAW} Điều 87 k4 điểm b, Điều 125 k2; {ND46} Điều 62; {TT67} Điều 53", 4),
    ("MOI_GIOI", "Môi giới bảo hiểm", KHAC, f"{LAW} Điều 87 k4 điểm b", 5),
    ("DAU_THAU", "Đấu thầu", KHAC, f"{LAW} Điều 87 k4 điểm c", 6),
    ("DIEN_TU", "Giao dịch điện tử (website/app, nền tảng đối tác)", MANG, f"{LAW} Điều 87 k4 điểm d; {TT67} Điều 4–5", 7),
]
# Đối tác ẩn danh: (code, name, type, channel)
PARTNERS = (
    [(f"NH_{x}", f"Ngân hàng TMCP {x}", "NGAN_HANG", "BANCA") for x in "ABCDEF"]
    + [(f"CTTC_{x}", f"Công ty tài chính {x}", "CTY_TAI_CHINH", "BANCA") for x in "AB"]
    + [(f"DK_{x}", f"Trung tâm đăng kiểm {x}", "DANG_KIEM", "DAI_LY_TC") for x in "ABCD"]
    + [(f"SR_{x}", f"Đại lý ô tô chính hãng {x}", "SHOWROOM_OTO", "DAI_LY_TC") for x in "ABCD"]
    + [(f"GA_{x}", f"Garage ô tô {x}", "GARAGE", "DAI_LY_TC") for x in "AB"]
    + [(f"OTA_{x}", f"Đại lý du lịch trực tuyến {x}", "OTA_DU_LICH", "DAI_LY_TC") for x in "AB"]
    + [(f"LH_{x}", f"Công ty lữ hành {x}", "CTY_LU_HANH", "DAI_LY_TC") for x in "ABC"]
    + [(f"MG_{x}", f"Công ty môi giới bảo hiểm {x}", "CTY_MOI_GIOI", "MOI_GIOI") for x in "ABCD"]
    + [(f"VI_{x}", f"Ví điện tử {x}", "VI_DIEN_TU", "DIEN_TU") for x in "AB"]
    + [("TMDT_A", "Sàn thương mại điện tử A", "SAN_TMDT", "DIEN_TU"), ("HK_A", "Hãng hàng không A", "HANG_HANG_KHONG", "DIEN_TU"),
       ("VT_A", "Nhà mạng viễn thông A", "VIEN_THONG", "DIEN_TU")]
)
PARTNERS_BY_TYPE = defaultdict(list)
for p in PARTNERS:
    PARTNERS_BY_TYPE[p[2]].append(p[0])

SEGMENTS = [("CA_NHAN", "Cá nhân", 0), ("HO_GIA_DINH", "Hộ gia đình", 0), ("DN_TRONG_NUOC", "Doanh nghiệp trong nước", 1),
            ("DN_FDI", "Doanh nghiệp có vốn đầu tư nước ngoài", 1), ("CO_QUAN_NN", "Cơ quan, đơn vị sự nghiệp nhà nước", 1),
            ("CO_SO_GD", "Cơ sở giáo dục", 1)]

TXN_TYPES = [  # code, name, sign, is deduction, gl account (TT 232/2012), note
    ("NEW", "Cấp mới", 1, 0, "5111", "Doanh thu phí bảo hiểm gốc"),
    ("RENEW", "Tái tục", 1, 0, "5111", "Hợp đồng nối tiếp hợp đồng hết hạn"),
    ("END_INC", "Sửa đổi bổ sung – tăng phí", 1, 0, "5111", "Tăng số tiền BH / mở rộng phạm vi"),
    ("END_DEC", "Sửa đổi bổ sung – giảm phí", -1, 1, "5321", "Giảm phí bảo hiểm gốc – khoản giảm thu (NĐ 46/2023 Đ49 k3)"),
    ("REFUND", "Hoàn phí", -1, 1, "5311", "Hoàn phí bảo hiểm gốc – khoản giảm thu (NĐ 46/2023 Đ49 k3)"),
    ("CANCEL", "Hủy hợp đồng (hoàn phí thời gian còn lại)", -1, 1, "5311", "Hoàn phí do chấm dứt hợp đồng trước hạn"),
    ("END_NOCHG", "Sửa đổi bổ sung – không đổi phí", 0, 0, None, "Thay đổi thông tin, không phát sinh phí"),
]
# Nhóm cơ sở & tỷ lệ phí tối thiểu cháy nổ bắt buộc (%/năm) — NĐ 67/2023 Phụ lục II (bản 2023)
FIRE_RATES = [(.05, 10), (.10, 10), (.06, 8), (.08, 8), (.15, 10), (.20, 18), (.25, 10), (.35, 6), (.15, 8), (.20, 8), (.35, 2), (.50, 1), (.50, 1)]
INSURERS = [("OWN", CORP[1], 1)] + [(f"CO_{x}", f"Doanh nghiệp bảo hiểm phi nhân thọ {x}", 0) for x in "ABCDEF"]
ALLOC_TYPES = [
    ("TU_KHAI_THAC", "Tự khai thác", "100% doanh thu cho đơn vị cấp đơn"),
    ("HO_TRO_CHEO", "Hợp tác khai thác giữa các đơn vị", "Chia doanh thu theo tỷ lệ đóng góp khai thác"),
    ("CHUYEN_GIAO", "Chuyển giao doanh thu", "Đơn vị cấp đơn chuyển doanh thu cho đơn vị quản lý khách hàng/địa bàn"),
]

# Tỷ giá hạch toán USD (KBNN). 2025: công bố; 2024: ước tính nội suy theo tỷ giá trung tâm NHNN
FX_USD = {
    2024: [23880, 23910, 23960, 24000, 24180, 24240, 24250, 24240, 24220, 24230, 24250, 24260],
    2025: [24283, 24334, 24539, 24786, 24901, 24954, 25007, 25151, 25252, 25214, 25120, 25118],
}

# ============================================================================
# 2. THAM SỐ HIỆU CHỈNH (sources/market_data.md, GENERATION_LOGIC.md)
# ============================================================================
# Mục tiêu doanh thu phí bảo hiểm gốc (tỷ VND) — neo vào CÔNG BỐ CÔNG KHAI của Bảo hiểm PVI:
# BCTC kiểm toán 2025 của Tổng công ty Bảo hiểm PVI, thuyết minh 21 (phí gốc theo nghiệp vụ, 2024 và 2025)
# https://adminweb.pvi.com.vn/wp-content/uploads/2026/05/2025Q4_Audited_FSs_En.pdf
PVI_LOB_PREMIUM = {
    2024: {"CON_NGUOI": D("2220.7"), "XE": D("1662.2"), "CHAY_NO": D("3005.9"), "TAI_SAN_THIET_HAI": D("4138.0")},
    2025: {"CON_NGUOI": D("3213.4"), "XE": D("1822.7"), "CHAY_NO": D("3451.2"), "TAI_SAN_THIET_HAI": D("3781.2")},
}
# [ƯỚC TÍNH] BCTC gộp 'Tài sản & thiệt hại' gồm cả kỹ thuật, năng lượng — phạm vi POC chỉ lấy phần tài sản thuần
PROPERTY_SHARE_OF_PD = D("0.50")
# Chia nhỏ trong nhóm — không có số công bố của PVI:
SUB_SPLIT = {
    # [ƯỚC TÍNH] sức khỏe PVI chủ yếu bảo hiểm nhóm doanh nghiệp (FPTS 04/2025); du lịch, học sinh là sản phẩm bán lẻ nhỏ
    "CON_NGUOI": {"SUC_KHOE": D(".75"), "SINH_MANG": D(".15"), "DU_LICH": D(".05"), "HOC_SINH": D(".05")},
    # IAV 2024: TNDS bắt buộc 4.537 / xe cơ giới 18.693 tỷ ≈ 24%
    "XE": {"TNDS_BB": D(".24"), "VCX": D(".76")},
}


def group_targets(year):
    """Doanh thu mục tiêu (VND) theo nhóm SP của năm."""
    p = PVI_LOB_PREMIUM[year]
    t = {g: p["CON_NGUOI"] * s for g, s in SUB_SPLIT["CON_NGUOI"].items()}
    t.update({g: p["XE"] * s for g, s in SUB_SPLIT["XE"].items()})
    t["CHAY_NO"] = p["CHAY_NO"]
    t["TAI_SAN"] = p["TAI_SAN_THIET_HAI"] * PROPERTY_SHARE_OF_PD
    return {g: v * D("1e9") for g, v in t.items()}


# Số hợp đồng năm 2025 theo nhóm (năm 2024 co theo tăng trưởng doanh thu từng nhóm).
# Quy tắc "tần suất × độ lớn": nhóm bán lẻ nhiều đơn nhỏ; nhóm doanh nghiệp ít đơn nhưng phí lớn (xem GENERATION_LOGIC.md)
POLICIES_2025 = {"TNDS_BB": 2500, "VCX": 3800, "HOC_SINH": 350, "DU_LICH": 1600,
                 "SINH_MANG": 1500, "SUC_KHOE": 2600, "CHAY_NO": 2200, "TAI_SAN": 1200}
# Mùa vụ — phí gốc hợp nhất PVI theo quý 2025: Q1 29,7% · Q2 24,1% · Q3 24,8% · Q4 21,4% (BCTC quý PVI Holdings)
# → nhóm doanh nghiệp tái tục dồn đầu năm; học sinh đỉnh đầu năm học (T8–T10)
SEASON = {
    "TNDS_BB":  [1.15, .85, 1.05, 1, 1, 1, 1, 1, 1, .95, .95, 1.0],
    "VCX":      [1.15, .85, 1.05, 1, 1, 1, 1, 1, 1, .95, .95, 1.0],
    "HOC_SINH": [.3, .2, .3, .3, .3, .4, .6, 2.6, 3.4, 2.0, .5, .3],
    "DU_LICH":  [1.4, 1.5, .8, 1.0, 1.3, 1.8, 1.9, 1.6, .8, .7, .7, 1.1],
    "SINH_MANG": [1.1, .9, 1.05, 1, 1, 1, 1, 1, 1, .95, .95, 1.0],
    "SUC_KHOE": [1.9, 1.0, 1.1, .95, .95, .95, 1.0, .95, .95, .85, .85, .85],
    "TAI_SAN":  [1.6, 1.0, 1.15, 1, 1, 1.05, 1.05, 1, 1, .9, .85, .9],
    "CHAY_NO":  [1.6, 1.0, 1.15, 1, 1, 1.05, 1.05, 1, 1, .9, .85, .9],
}
PRODUCT_MIX = {
    "TNDS_BB": [("XE_TNDS_OTO", .55), ("XE_TNDS_MOTO", .45)],
    "VCX": [("XE_VCX_OTO", .85), ("XE_VCX_MOTO", .15)],
    "HOC_SINH": [("NG_HSSV_TN", .6), ("NG_HSSV_SK", .4)],
    "DU_LICH": [("NG_DL_ND", .55), ("NG_DL_QT", .45)],
    "SINH_MANG": [("NG_SM_CN", .35), ("NG_NVV", .45), ("NG_TN24", .20)],
    "SUC_KHOE": [("NG_SK_CN", .45), ("NG_SK_NHOM", .45), ("NG_SK_BHN", .10)],
    "TAI_SAN": [("TS_NHA", .45), ("TS_MRR", .35), ("TS_MRRCN", .20)],
    "CHAY_NO": [("CHN_BB", .7), ("CHN_TN", .3)],
}
# (channel, trọng số, [loại đối tác]); [] = không qua đối tác; None trong list = kênh điện tử của chính công ty
# Định hướng: kênh TMĐT PVI ≈ 6% phí gốc 2024 (≈800 tỷ, BCTN 2024) → ≈10% năm 2025 (suy ra: TMĐT quý I/2025 tăng 1,8 lần, pvn.vn);
# bancassurance của PVI mới mở rộng (hợp tác Nam A Bank, pvi.com.vn) [ƯỚC TÍNH ≈5–8%];
# môi giới cao hơn thị trường (13,5%) do PVI thiên về khách hàng doanh nghiệp lớn [ƯỚC TÍNH ≈15–20%]
CHANNEL_MIX = {
    "TNDS_BB": [("TRUC_TIEP", 18, []), ("DAI_LY_CN", 27, []), ("DAI_LY_TC", 28, ["DANG_KIEM", "SHOWROOM_OTO", "GARAGE"]),
                ("DIEN_TU", 25, [None, "VI_DIEN_TU", "SAN_TMDT", "VIEN_THONG"]), ("BANCA", 2, ["NGAN_HANG"])],
    "VCX": [("TRUC_TIEP", 25, []), ("DAI_LY_CN", 18, []), ("DAI_LY_TC", 25, ["SHOWROOM_OTO", "GARAGE"]),
            ("BANCA", 5, ["NGAN_HANG", "CTY_TAI_CHINH"]), ("MOI_GIOI", 10, ["CTY_MOI_GIOI"]), ("DIEN_TU", 12, [None, "SAN_TMDT"])],
    "HOC_SINH": [("TRUC_TIEP", 58, []), ("DAI_LY_CN", 34, []), ("DIEN_TU", 8, [None])],
    "DU_LICH": [("DAI_LY_TC", 35, ["OTA_DU_LICH", "CTY_LU_HANH"]), ("DIEN_TU", 42, [None, "HANG_HANG_KHONG", "VI_DIEN_TU"]),
                ("TRUC_TIEP", 12, []), ("DAI_LY_CN", 11, [])],
    "SINH_MANG": [("BANCA", 45, ["NGAN_HANG", "CTY_TAI_CHINH"]), ("DAI_LY_CN", 30, []), ("TRUC_TIEP", 13, []), ("DIEN_TU", 12, [None, "VIEN_THONG"])],
    "SUC_KHOE": [("TRUC_TIEP", 27, []), ("DAI_LY_CN", 27, []), ("MOI_GIOI", 18, ["CTY_MOI_GIOI"]),
                 ("BANCA", 4, ["NGAN_HANG"]), ("DIEN_TU", 20, [None, "VI_DIEN_TU"]), ("DAU_THAU", 3, [])],
    "CHAY_NO": [("TRUC_TIEP", 50, []), ("DAI_LY_CN", 21, []), ("BANCA", 4, ["NGAN_HANG"]), ("MOI_GIOI", 22, ["CTY_MOI_GIOI"]),
                ("DAU_THAU", 3, [])],
    "TAI_SAN": [("TRUC_TIEP", 40, []), ("MOI_GIOI", 25, ["CTY_MOI_GIOI"]), ("BANCA", 4, ["NGAN_HANG"]),
                ("DAI_LY_CN", 10, []), ("DIEN_TU", 15, [None, "SAN_TMDT"]), ("DAU_THAU", 3, [])],
}
DIGITAL_FACTOR = {2024: 0.5, 2025: 1.0}  # tăng trưởng kênh điện tử 2024 → 2025 (TMĐT quý I/2025 tăng 1,8 lần, pvn.vn)
GROUP_ABBR = {"TNDS_BB": "XTN", "VCX": "XVC", "HOC_SINH": "HSS", "DU_LICH": "DLC",
              "SINH_MANG": "SMG", "SUC_KHOE": "SKH", "TAI_SAN": "TSN", "CHAY_NO": "CNO"}
ANNUAL_GROUPS = {"TNDS_BB", "VCX", "SINH_MANG", "SUC_KHOE", "TAI_SAN", "CHAY_NO"}

# ============================================================================
# 3. HÀM TIỆN ÍCH
# ============================================================================
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
DEM = {True: ["Văn", "Hữu", "Đức", "Minh", "Quang", "Thành", "Công", "Xuân", "Gia"], False: ["Thị", "Ngọc", "Thu", "Thanh", "Mai", "Kim", "Phương", "Hồng", "Diệu"]}
TEN = {True: ["An", "Bình", "Cường", "Dũng", "Hải", "Hùng", "Khoa", "Long", "Nam", "Phong", "Quân", "Sơn", "Tuấn", "Việt", "Hiếu", "Trung"],
       False: ["Anh", "Châu", "Dung", "Giang", "Hà", "Hạnh", "Hương", "Lan", "Linh", "My", "Ngân", "Nhung", "Oanh", "Thảo", "Trang", "Yến"]}
CTY_TU = ["Hưng Thịnh", "Phát Đạt", "Thành Công", "Minh Long", "An Khang", "Đại Việt", "Hoàng Gia", "Sao Mai", "Tân Tiến",
          "Phú Quý", "Toàn Cầu", "Bình Minh", "Nam Việt", "Kim Ngân", "Trường Sơn", "Hồng Hà", "Đông Á", "Thái Bình Dương"]
LINH_VUC = ["Thương mại Dịch vụ", "Xây dựng", "Đầu tư", "Sản xuất", "Vận tải", "Logistics", "Công nghệ", "Thực phẩm",
            "Bất động sản", "Cơ khí", "Dệt may", "Dược phẩm", "Điện tử", "Nhựa", "Thép"]
FDI_TEN = ["Sunrise Vina", "Hanam Electronics Việt Nam", "Pacific Textile Việt Nam", "Nippon Parts Việt Nam", "Golden Bridge Vina",
           "Evergreen Manufacturing Việt Nam", "K-Tech Vina", "Asia Packaging Việt Nam"]
CQ_TEN = ["Sở Giao thông Vận tải", "Bệnh viện Đa khoa", "Trung tâm Y tế", "Ban Quản lý dự án", "Sở Tài chính", "Viện Nghiên cứu"]
TRUONG = ["Trường THPT", "Trường THCS", "Trường Tiểu học", "Trường Đại học", "Trường Cao đẳng"]


def wchoice(items, weights):
    return rnd.choices(items, weights=weights, k=1)[0]


def logu(lo, hi):
    return math.exp(rnd.uniform(math.log(lo), math.log(hi)))


def r0(x):
    return D(x).quantize(D("1"), ROUND_HALF_UP)


def r2(x):
    return D(x).quantize(D("0.01"), ROUND_HALF_UP)


def fx(cur, d):
    if cur == "VND":
        return D(1)
    if d.year > max(FX_USD):  # chưa có số công bố -> dùng tỷ giá gần nhất
        return D(FX_USD[max(FX_USD)][-1])
    return D(FX_USD[d.year][d.month - 1])


def rand_day(year, month):
    start = dt.date(year, month, 1)
    end = dt.date(year + (month == 12), month % 12 + 1, 1)
    return start + dt.timedelta(days=rnd.randrange((end - start).days))


def add_year(d):
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        return d + dt.timedelta(days=365)


# ============================================================================
# 4. SINH GIAO DỊCH
# ============================================================================
class Gen:
    def __init__(self):
        self.customers, self.policies, self.txns, self.coverages = [], [], [], []
        self.coins, self.allocs = [], []
        self.cust_pool = defaultdict(list)
        self.cust_seq = 0
        self.policy_seq = defaultdict(int)
        self.pid = 100000
        self.tid = 500000
        self.cid = 900000
        self.generic_customers = {}

    # ---------- khách hàng ----------
    def new_customer(self, segment, company, created):
        self.cust_seq += 1
        code = f"KH{self.cust_seq:07d}"
        male = rnd.random() < .5
        person = f"{rnd.choice(HO)} {rnd.choice(DEM[male])} {rnd.choice(TEN[male])}"
        name = {
            "CA_NHAN": person,
            "HO_GIA_DINH": f"Hộ gia đình {person}",
            "DN_TRONG_NUOC": f"Công ty {rnd.choice(['TNHH', 'Cổ phần'])} {rnd.choice(LINH_VUC)} {rnd.choice(CTY_TU)}",
            "DN_FDI": f"Công ty TNHH {rnd.choice(FDI_TEN)}",
            "CO_QUAN_NN": f"{rnd.choice(CQ_TEN)} {rnd.choice(CTY_TU)}",
            "CO_SO_GD": f"{rnd.choice(TRUONG)} {rnd.choice(HO)} {rnd.choice(TEN[True])}",
        }[segment]
        org = segment not in ("CA_NHAN", "HO_GIA_DINH")
        comp = next(c for c in COMPANIES if c[0] == company)
        self.customers.append({
            "customer_code": code, "customer_name": name, "segment_code": segment,
            "tax_code": f"0{rnd.randint(100000000, 999999999)}" if org else None,
            "province_code": comp[3] or rnd.choice(PROVINCES)[0], "home_company_code": company,
            "is_aggregated_retail": 0, "created_date": created - dt.timedelta(days=rnd.randint(0, 2000)),
        })
        self.cust_pool[(company, segment)].append(code)
        return code

    def customer(self, segment, company, created):
        pool = self.cust_pool[(company, segment)]
        if pool and rnd.random() < .2:
            return rnd.choice(pool)
        return self.new_customer(segment, company, created)

    def generic_retail_customer(self, company):
        """Khách lẻ theo bảng kê — đơn theo lô GCN qua đối tác: chủ hợp đồng không phải từng cá nhân"""
        if company not in self.generic_customers:
            self.cust_seq += 1
            code = f"KH{self.cust_seq:07d}"
            comp = next(c for c in COMPANIES if c[0] == company)
            self.customers.append({
                "customer_code": code, "customer_name": f"Khách lẻ theo bảng kê – {comp[1]}", "segment_code": "CA_NHAN",
                "tax_code": None, "province_code": comp[3], "home_company_code": company,
                "is_aggregated_retail": 1, "created_date": dt.date(2020, 1, 1)})
            self.generic_customers[company] = code
        return self.generic_customers[company]

    # ---------- định phí 1 dòng sản phẩm (đơn giá + số lượng) ----------
    def price(self, product, mode):
        """mode: SINGLE | GROUP | BATCH -> dict(unit fields)"""
        cur, n, si, rate, unit = "VND", 1, D(0), None, None
        if product == "XE_TNDS_OTO":  # NĐ 67/2023 Phụ lục I: biểu phí theo loại xe (chưa VAT)
            unit = D(wchoice([437000, 794000, 1270000, 1825000, 756000, 933000, 1080000, 853000, 1660000, 2746000, 3200000],
                             [50, 12, 3, 2, 8, 3, 4, 10, 5, 2, 1]))
            si, n = D(150_000_000), (rnd.randint(20, 300) if mode == "BATCH" else 1)
        elif product == "XE_TNDS_MOTO":
            unit = D(wchoice([55000, 60000, 290000], [24, 75, 1]))
            si, n = D(150_000_000), (rnd.randint(50, 1500) if mode == "BATCH" else 1)
        elif product == "XE_VCX_OTO":
            si = r0(logu(400e6, 3e9) // 1_000_000 * 1_000_000)
            rate = round(rnd.uniform(1.1, 2.0), 4)
            n = rnd.randint(5, 60) if mode == "GROUP" else 1
        elif product == "XE_VCX_MOTO":
            si = D(rnd.randrange(15, 90) * 1_000_000); rate = round(rnd.uniform(1.5, 2.5), 4)
            n = rnd.randint(20, 400) if mode == "BATCH" else 1
        elif product == "NG_HSSV_TN":
            unit = D(wchoice([100000, 120000, 150000], [60, 25, 15])); si = D(20_000_000)
            n = rnd.randint(200, 3000) if mode == "GROUP" else 1
        elif product == "NG_HSSV_SK":
            unit = D(rnd.randrange(200, 520, 10) * 1000); si = D(50_000_000)
            n = rnd.randint(150, 2500) if mode == "GROUP" else 1
        elif product == "NG_DL_ND":
            unit = D(rnd.randrange(17, 80) * 1000); si = D(wchoice([30e6, 50e6, 100e6], [40, 40, 20]))
            n = {"SINGLE": rnd.randint(1, 4), "GROUP": rnd.randint(10, 45), "BATCH": rnd.randint(200, 3000)}[mode]
        elif product == "NG_DL_QT":
            cur = "USD" if rnd.random() < .7 else "VND"
            usd = round(rnd.uniform(4, 45), 2)
            unit = D(str(usd)) if cur == "USD" else r0(usd * 25000 / 1000) * 1000
            si = D(50_000) if cur == "USD" else D(1_000_000_000)
            n = {"SINGLE": rnd.randint(1, 4), "GROUP": rnd.randint(10, 40), "BATCH": rnd.randint(100, 1500)}[mode]
        elif product == "NG_SM_CN":
            si = D(rnd.randrange(50, 500, 10) * 1_000_000); rate = round(rnd.uniform(.25, .5), 4)
            n = rnd.randint(20, 400) if mode == "GROUP" else 1
        elif product == "NG_NVV":  # tỷ lệ phí trên dư nợ — [ƯỚC TÍNH]
            si = r0(logu(100e6, 3e9) // 1_000_000 * 1_000_000); rate = round(rnd.uniform(.3, 1.0), 4)
            n = rnd.randint(20, 400) if mode == "BATCH" else 1
        elif product == "NG_TN24":
            si = D(rnd.randrange(20, 200, 10) * 1_000_000); rate = round(rnd.uniform(.1, .3), 4)
            n = rnd.randint(20, 500) if mode == "GROUP" else 1
        elif product == "NG_SK_CN":
            unit = D(rnd.randrange(1450, 15000, 50) * 1000); si = D(rnd.randrange(100, 1000, 50) * 1_000_000)
        elif product == "NG_SK_NHOM":
            unit = D(rnd.randrange(2000, 8000, 50) * 1000); si = D(rnd.randrange(100, 600, 50) * 1_000_000)
            n = rnd.randint(20, 1500)
        elif product == "NG_SK_BHN":
            unit = D(rnd.randrange(135, 3000, 5) * 1000); si = D(rnd.randrange(100, 1000, 100) * 1_000_000)
        elif product == "TS_NHA":
            si = D(rnd.randrange(300, 5000, 50) * 1_000_000); rate = round(rnd.uniform(.05, .1), 4)
        elif product in ("TS_MRR", "TS_MRRCN", "CHN_BB", "CHN_TN"):
            lo, hi = {"TS_MRR": (10e9, 2e12), "TS_MRRCN": (50e9, 5e12), "CHN_BB": (3e9, 8e11), "CHN_TN": (2e9, 5e11)}[product]
            si = r0(logu(lo, hi) // 1_000_000 * 1_000_000)
            if product in ("CHN_BB", "CHN_TN"):  # tỷ lệ tối thiểu theo nhóm cơ sở, DN có thể thu cao hơn
                base = wchoice([r for r, _ in FIRE_RATES], [w for _, w in FIRE_RATES])
                rate = round(base * rnd.uniform(1.0, 1.25 if product == "CHN_BB" else 1.6), 4)
            else:
                rate = round(rnd.uniform(*{"TS_MRR": (.07, .2), "TS_MRRCN": (.05, .15)}[product]), 4)
            if product in ("TS_MRR", "TS_MRRCN") and rnd.random() < (.2 if product == "TS_MRR" else .4):
                cur = "USD"; si = r2(si / D(25000))
        else:
            raise ValueError(product)
        return {"product_code": product, "currency": cur, "count": n, "si_unit": si, "rate": rate, "unit": unit}

    @staticmethod
    def premium_of(cv):
        if cv["rate"] is not None:
            p = cv["si_unit"] * cv["count"] * D(str(cv["rate"])) / 100
        else:
            p = cv["unit"] * cv["count"]
        return r2(p) if cv["currency"] == "USD" else r0(p / 1000) * 1000 if cv["rate"] is not None else r0(p)

    # ---------- 1 hợp đồng ----------
    def make_policy(self, year, month, group, renewal_of=None):
        if renewal_of:
            base = renewal_of
            issue = base["expiry_date"] - dt.timedelta(days=rnd.randint(0, 10))
            company, customer, channel, partner = base["issuing_company_code"], base["customer_code"], base["channel_code"], base["partner_code"]
        else:
            issue = rand_day(year, month)
            company, customer, channel, partner = None, None, None, None
        product = wchoice(*zip(*PRODUCT_MIX[group])) if not renewal_of else renewal_of["_main_product"]

        # chế độ đơn: lẻ / nhóm / lô GCN
        mode = "SINGLE"
        if group == "TNDS_BB" and rnd.random() < .6: mode = "BATCH"
        if product == "XE_VCX_OTO" and rnd.random() < .2: mode = "GROUP"
        if product == "XE_VCX_MOTO" and rnd.random() < .5: mode = "BATCH"
        if group == "HOC_SINH" and rnd.random() < .85: mode = "GROUP"
        if group == "DU_LICH": mode = wchoice(["SINGLE", "GROUP", "BATCH"], [60, 25, 15])
        if product in ("NG_SM_CN", "NG_TN24") and rnd.random() < .25: mode = "GROUP"
        if product == "NG_SK_NHOM": mode = "GROUP"
        if renewal_of: mode = renewal_of["_mode"]

        if not renewal_of:
            mix = CHANNEL_MIX[group]
            ch, _, ptypes = wchoice(mix, [c[1] * (DIGITAL_FACTOR[year] if c[0] == "DIEN_TU" else 1) for c in mix])
            channel = ch
            ptype = rnd.choice(ptypes) if ptypes else None
            partner = rnd.choice(PARTNERS_BY_TYPE[ptype]) if ptype else None
            if product == "NG_NVV" and channel == "BANCA" and rnd.random() < .85:
                mode = "BATCH"  # hợp đồng bao: ngân hàng gửi bảng kê người vay theo kỳ
            if mode == "BATCH" and channel in ("TRUC_TIEP", "DAI_LY_CN"):  # lô GCN luôn đi qua đối tác/đại lý tổ chức
                channel, ptype = ("DAI_LY_TC", "OTA_DU_LICH") if group == "DU_LICH" else ("DAI_LY_TC", "DANG_KIEM")
                partner = rnd.choice(PARTNERS_BY_TYPE[ptype])
            # đơn vị cấp đơn
            if channel == "DIEN_TU":
                company = "DGT" if rnd.random() < .7 else wchoice([c[0] for c in MEMBERS], [c[4] for c in MEMBERS])
            else:
                company = wchoice([c[0] for c in MEMBERS], [c[4] for c in MEMBERS])
            # khách hàng
            if mode == "BATCH":
                customer = self.generic_retail_customer(company)
            else:
                seg = {
                    "TNDS_BB": wchoice(["CA_NHAN", "DN_TRONG_NUOC"], [85, 15]),
                    "VCX": "DN_TRONG_NUOC" if mode == "GROUP" else wchoice(["CA_NHAN", "DN_TRONG_NUOC", "DN_FDI"], [78, 18, 4]),
                    "HOC_SINH": "CO_SO_GD" if mode == "GROUP" else "CA_NHAN",
                    "DU_LICH": "DN_TRONG_NUOC" if mode == "GROUP" else "CA_NHAN",
                    "SINH_MANG": wchoice(["DN_TRONG_NUOC", "CO_QUAN_NN"], [80, 20]) if mode == "GROUP" else "CA_NHAN",
                    "SUC_KHOE": wchoice(["DN_TRONG_NUOC", "DN_FDI", "CO_QUAN_NN"], [65, 25, 10]) if product == "NG_SK_NHOM" else "CA_NHAN",
                    "TAI_SAN": wchoice(["HO_GIA_DINH", "CA_NHAN"], [70, 30]) if product == "TS_NHA" else wchoice(["DN_TRONG_NUOC", "DN_FDI", "CO_QUAN_NN"], [65, 28, 7]),
                    "CHAY_NO": wchoice(["DN_TRONG_NUOC", "DN_FDI", "CO_QUAN_NN", "HO_GIA_DINH"], [68, 17, 7, 8]),
                }[group]
                home = company
                if company == "DGT":  # khách online thuộc địa bàn công ty thành viên
                    home = wchoice([c[0] for c in MEMBERS], [c[4] for c in MEMBERS])
                customer = self.customer(seg, home, issue)

        cv_main = self.price(product, mode)
        if renewal_of:  # tái tục: giữ đối tượng, điều chỉnh phí ±
            old = renewal_of["_main_cov"]
            cv_main.update(currency=old["currency"], count=old["count"], si_unit=old["si_unit"], unit=old["unit"])
            factor = D(str(round(rnd.uniform(.95, 1.12), 4)))
            if cv_main["rate"] is not None and old["rate"] is not None:
                cv_main["rate"] = round(old["rate"] * float(factor), 4)
            elif cv_main["unit"] is not None and product not in ("XE_TNDS_OTO", "XE_TNDS_MOTO"):
                cv_main["unit"] = r0(old["unit"] * factor) if cv_main["currency"] == "VND" else r2(old["unit"] * factor)
        covs = [cv_main]
        if product == "XE_VCX_OTO" and mode == "SINGLE" and rnd.random() < .7:  # VCX bán kèm TNDS bắt buộc
            covs.append(dict(self.price("XE_TNDS_OTO", "SINGLE"), currency=cv_main["currency"]))
        if product == "CHN_BB" and rnd.random() < .15:
            extra = self.price("TS_MRR", "SINGLE"); extra.update(currency="VND", si_unit=cv_main["si_unit"], rate=round(rnd.uniform(.03, .08), 4))
            covs.append(extra)

        # rủi ro lớn do Khối Trụ sở trực tiếp khai thác (thường có hợp tác với công ty thành viên quản lý khách)
        si_vnd = cv_main["si_unit"] * cv_main["count"] * (D(25000) if cv_main["currency"] == "USD" else 1)
        to_head_office = not renewal_of and channel != "DIEN_TU" and (
            (group in ("TAI_SAN", "CHAY_NO") and si_vnd >= D("500e9") and rnd.random() < .6)
            or (product == "NG_SK_NHOM" and cv_main["count"] > 800 and rnd.random() < .4))
        if to_head_office:
            company = "HO"

        eff = issue + dt.timedelta(days=rnd.randint(0, 60 if group == "DU_LICH" else 10))
        exp = eff + dt.timedelta(days=rnd.randint(2, 20)) if group == "DU_LICH" else add_year(eff) - dt.timedelta(days=1)
        if group == "HOC_SINH":
            exp = eff + dt.timedelta(days=364)

        self.pid += 1
        self.policy_seq[(issue.year, company, group)] += 1
        pol = {
            "policy_id": self.pid,
            "policy_no": f"{issue.year}-{company}-{GROUP_ABBR[group]}-{self.policy_seq[(issue.year, company, group)]:06d}",
            "issuing_company_code": company, "customer_code": customer,
            "channel_code": None if rnd.random() < .005 else channel, "partner_code": partner,
            "currency_code": cv_main["currency"], "issue_date": issue, "effective_date": eff, "expiry_date": exp,
            "is_group_policy": int(mode != "SINGLE"), "renewal_of_policy_id": renewal_of["policy_id"] if renewal_of else None,
            "_group": group, "_mode": mode, "_main_product": product, "_covs": covs, "_main_cov": cv_main,
        }
        if pol["channel_code"] is None:
            pol["partner_code"] = None
        # đồng bảo hiểm: rủi ro tài sản lớn
        shares = [("OWN", "SOLE", D(100))]
        if (group in ("TAI_SAN", "CHAY_NO") and si_vnd >= D("300e9") and rnd.random() < .55) or \
           (product == "NG_SK_NHOM" and cv_main["count"] > 1000 and rnd.random() < .3):
            if renewal_of and renewal_of["_coins"]:
                shares = renewal_of["_coins"]
            else:
                lead = rnd.random() < .4
                own = D(rnd.choice([40, 50, 60, 70])) if lead else D(rnd.choice([10, 15, 20, 25, 30, 40]))
                others = rnd.sample([i[0] for i in INSURERS[1:]], k=rnd.randint(1, 3))
                rest, parts = D(100) - own, []
                for i, o in enumerate(others):
                    s = rest if i == len(others) - 1 else r0(rest * D(str(rnd.uniform(.3, .7))))
                    rest -= s if i < len(others) - 1 else 0
                    parts.append(s)
                shares = [("OWN", "LEADER" if lead else "FOLLOWER", own)]
                shares += [(o, "FOLLOWER" if (lead or i > 0) else "LEADER", s) for i, (o, s) in enumerate(zip(others, parts))]
        pol["_coins"] = shares
        # phân bổ doanh thu
        home = next(c["home_company_code"] for c in reversed(self.customers) if c["customer_code"] == customer)
        if company == "HO" and home != "HO" and rnd.random() < .6:
            mine = D(rnd.choice([50, 60, 70]))
            alloc = [("HO", "HO_TRO_CHEO", mine), (home, "HO_TRO_CHEO", D(100) - mine)]
        elif company == "HO":
            alloc = [("HO", "TU_KHAI_THAC", D(100))]
        elif company == "DGT" and rnd.random() < .5:
            alloc = [(home, "CHUYEN_GIAO", D(100))]
        elif company != "DGT" and rnd.random() < .10:
            other = wchoice([c[0] for c in MEMBERS if c[0] != company], [c[4] for c in MEMBERS if c[0] != company])
            mine = D(rnd.choice([50, 60, 70, 80]))
            alloc = [(company, "HO_TRO_CHEO", mine), (other, "HO_TRO_CHEO", D(100) - mine)]
        elif company != "DGT" and rnd.random() < .01:
            other = rnd.choice([c[0] for c in MEMBERS if c[0] != company])
            alloc = [(other, "CHUYEN_GIAO", D(100))]
        else:
            alloc = [(company, "TU_KHAI_THAC", D(100))]
        if renewal_of:
            alloc = renewal_of["_alloc"]
        pol["_alloc"] = alloc
        self.policies.append(pol)
        return pol

    def add_txn(self, pol, txn_type, txn_date, covs, status="APPROVED", seq=0):
        self.tid += 1
        acc = max(txn_date, pol["effective_date"]) if txn_type in ("NEW", "RENEW") else txn_date
        t = {"txn_id": self.tid, "policy_id": pol["policy_id"], "txn_no": f"{pol['policy_no']}/{seq:02d}",
             "txn_type_code": txn_type, "txn_date": txn_date, "accounting_date": acc, "status": status,
             "fx_rate": fx(pol["currency_code"], acc), "created_by": f"{pol['issuing_company_code']}.NV{rnd.randint(1, 25):02d}",
             "created_at": dt.datetime.combine(txn_date, dt.time(rnd.randint(8, 17), rnd.randint(0, 59), rnd.randint(0, 59))),
             "_covs": covs, "_pol": pol}
        self.txns.append(t)
        return t

    # ---------- chạy ----------
    def run(self):
        prev_year = []
        for year in YEARS:
            year_policies = []
            # tái tục từ năm trước
            for p in prev_year:
                if p["_group"] in ANNUAL_GROUPS and p["_mode"] != "BATCH" and p["expiry_date"].year == year and rnd.random() < .55:
                    np_ = self.make_policy(year, None, p["_group"], renewal_of=p)
                    year_policies.append(np_)
            renew_count = defaultdict(int)
            for p in year_policies:
                renew_count[p["_group"]] += 1
            t_year, t_2025 = group_targets(year), group_targets(2025)
            for group, total in POLICIES_2025.items():
                growth = float(t_year[group] / t_2025[group])
                n_new = max(0, round(total * growth) - renew_count[group])
                w = SEASON[group]
                for m in range(1, 13):
                    for _ in range(round(n_new * w[m - 1] / sum(w))):
                        year_policies.append(self.make_policy(year, m, group))
            # giao dịch gốc
            for p in year_policies:
                st = wchoice(["APPROVED", "PENDING", "VOID"], [985, 10, 5])
                self.add_txn(p, "RENEW" if p["renewal_of_policy_id"] else "NEW", p["issue_date"], p["_covs"], st)
                p["_status"] = st
            self.calibrate(year, year_policies)
            prev_year = year_policies
        self.endorsements()

    def calibrate(self, year, pols):
        """Co giãn số lượng đối tượng (đơn lô/nhóm) hoặc STBH (đơn tính theo % STBH) để doanh thu
        phần công ty của từng nhóm SP khớp mục tiêu neo theo số liệu công khai (group_targets)."""
        for group, target in group_targets(year).items():
            gp = [p for p in pols if p["_group"] == group and p["_status"] == "APPROVED"]

            def own_rev(p):
                own = next(s for i, r, s in p["_coins"] if i == "OWN") / 100
                return sum(self.premium_of(c) * fx(c["currency"], max(p["issue_date"], p["effective_date"])) for c in p["_covs"]) * own

            fixed = sum(own_rev(p) for p in gp if not self.scalable(p))
            scal = sum(own_rev(p) for p in gp if self.scalable(p))
            if scal <= 0:
                continue
            f = max(D("0.05"), (target - fixed) / scal)
            for p in gp:
                if not self.scalable(p):
                    continue
                for c in p["_covs"]:
                    if p["_mode"] in ("GROUP", "BATCH") and c is p["_main_cov"]:
                        c["count"] = max(1, int(r0(c["count"] * f)))
                    elif c["rate"] is not None:
                        c["si_unit"] = r0(c["si_unit"] * f / 1_000_000) * 1_000_000 if c["currency"] == "VND" else r2(c["si_unit"] * f)

    @staticmethod
    def scalable(p):
        return p["_mode"] in ("GROUP", "BATCH") or p["_group"] in ("TAI_SAN", "CHAY_NO")

    def endorsements(self):
        end_limit = dt.date(YEARS[-1], 12, 31)
        approved = [p for p in self.policies if p["_status"] == "APPROVED" and p["_group"] != "DU_LICH"]
        for p in rnd.sample(approved, k=int(len(approved) * .07)):
            span = (min(p["expiry_date"], end_limit) - p["effective_date"]).days
            if span < 30:
                continue
            d = p["effective_date"] + dt.timedelta(days=rnd.randint(15, span))
            kind = wchoice(["END_INC", "END_DEC", "REFUND", "CANCEL", "END_NOCHG"], [30, 15, 15, 25, 15])
            main = p["_main_cov"]
            base = self.premium_of(main)
            remain = D((p["expiry_date"] - d).days) / D(max(1, (p["expiry_date"] - p["effective_date"]).days))
            amt = {"END_INC": base * D(str(rnd.uniform(.05, .3))), "END_DEC": -base * D(str(rnd.uniform(.05, .2))),
                   "REFUND": -base * D(str(rnd.uniform(.05, .3))), "CANCEL": -base * remain * D(".9"), "END_NOCHG": D(0)}[kind]
            amt = r2(amt) if main["currency"] == "USD" else r0(amt / 1000) * 1000
            cv = dict(main, _fixed_premium=amt)
            if kind == "CANCEL":
                cv["_si_override"] = D(0)
            seq = sum(1 for t in self.txns if t["policy_id"] == p["policy_id"])
            self.add_txn(p, kind, d, [cv], seq=seq)

    # ---------- xuất bảng ----------
    def tables(self):
        T = {}
        T["ref.region"] = [{"region_code": c, "region_name": n} for c, n in REGIONS]
        T["ref.province"] = [{"province_code": c, "province_name": n, "region_code": r} for c, n, r in PROVINCES]
        T["ref.company"] = [{"company_code": CORP[0], "company_name": CORP[1], "company_type": "CORPORATION",
                             "parent_company_code": None, "province_code": "HNI", "established_date": dt.date(2005, 1, 1)}]
        T["ref.company"] += [{"company_code": c, "company_name": n, "company_type": t, "parent_company_code": CORP[0],
                              "province_code": p, "established_date": dt.date(2005 + i % 15, 1 + i % 12, 1)}
                             for i, (c, n, t, p, _) in enumerate(COMPANIES)]
        T["ref.line_of_business"] = [dict(zip(["lob_code", "lob_name", "legal_category", "poc_group_code", "poc_group_name", "legal_basis"], l)) for l in LOBS]
        T["ref.regulatory_line"] = [{"report_line_code": c, "report_line_name": n, "parent_line_code": p, "legal_basis": PL6} for c, n, p in REG_LINES]
        T["ref.product_group"] = [dict(zip(["product_group_code", "product_group_name", "lob_code", "sort_order"], g)) for g in PRODUCT_GROUPS]
        T["ref.product"] = [dict(zip(["product_code", "product_name", "product_group_code", "report_line_code", "is_compulsory",
                                      "pricing_basis", "vat_rate", "max_commission_pct", "legal_basis"], p), solvency2_lob=SOLVENCY2[p[0]])
                            for p in PRODUCTS]
        T["ref.channel"] = [dict(zip(["channel_code", "channel_name", "report_channel_group", "legal_basis", "sort_order"], c)) for c in CHANNELS]
        T["ref.partner"] = [dict(zip(["partner_code", "partner_name", "partner_type", "channel_code"], p)) for p in PARTNERS]
        T["ref.customer_segment"] = [dict(zip(["segment_code", "segment_name", "is_organization"], s)) for s in SEGMENTS]
        T["ref.customer"] = self.customers
        T["ref.currency"] = [{"currency_code": "VND", "currency_name": "Đồng Việt Nam"}, {"currency_code": "USD", "currency_name": "Đô la Mỹ"}]
        T["ref.fx_rate"] = [{"currency_code": "USD", "rate_month": dt.date(y, m + 1, 1), "rate_to_vnd": D(v),
                             "source_note": "Tỷ giá hạch toán KBNN" if y == 2025 else "Ước tính nội suy tỷ giá trung tâm NHNN"}
                            for y, vals in FX_USD.items() for m, v in enumerate(vals)]
        T["ref.transaction_type"] = [dict(zip(["txn_type_code", "txn_type_name", "premium_sign", "is_revenue_deduction", "gl_account"], t[:5]),
                                          acord_business_purpose_cd=ACORD_TXN[t[0]], note=t[5]) for t in TXN_TYPES]
        T["ref.insurer"] = [dict(zip(["insurer_code", "insurer_name", "is_own_company"], i)) for i in INSURERS]
        T["ref.allocation_type"] = [dict(zip(["allocation_type_code", "allocation_type_name", "note"], a)) for a in ALLOC_TYPES]

        pol_cols = ["policy_id", "policy_no", "issuing_company_code", "customer_code", "channel_code", "partner_code", "currency_code",
                    "issue_date", "effective_date", "expiry_date", "is_group_policy", "renewal_of_policy_id"]
        T["core.policy"] = [{k: p[k] for k in pol_cols} for p in self.policies]
        tx_cols = ["txn_id", "policy_id", "txn_no", "txn_type_code", "txn_date", "accounting_date", "status", "fx_rate", "created_by", "created_at"]
        T["core.policy_transaction"] = [{k: t[k] for k in tx_cols} for t in self.txns]
        covs = []
        comm_cache = {}
        for t in self.txns:
            pol = t["_pol"]
            for c in t["_covs"]:
                self.cid += 1
                prem = c.get("_fixed_premium", None)
                if prem is None:
                    prem = self.premium_of(c)
                vnd = r0(prem * t["fx_rate"])
                vat = r0(vnd * PROD[c["product_code"]][6] / 100)
                # hoa hồng: chỉ kênh trung gian, ≤ trần TT 67/2023 Đ51; giữ nguyên tỷ lệ cho mọi giao dịch của cùng hợp đồng
                key = (pol["policy_id"], c["product_code"])
                if key not in comm_cache:
                    cap = PROD[c["product_code"]][7]
                    comm_cache[key] = 0 if pol["channel_code"] in (None, "TRUC_TIEP", "DAU_THAU") else round(cap * rnd.uniform(.5, 1.0), 2)
                covs.append({"coverage_id": self.cid, "txn_id": t["txn_id"], "product_code": c["product_code"],
                             "sum_insured": c.get("_si_override", c["si_unit"] * c["count"]),
                             "premium_rate_pct": c["rate"], "insured_count": c["count"], "premium_orig": prem,
                             "premium_vnd": vnd, "vat_vnd": vat, "commission_rate_pct": comm_cache[key]})
        T["core.transaction_coverage"] = covs
        T["core.coinsurance_share"] = [{"policy_id": p["policy_id"], "insurer_code": i, "role": r, "share_pct": s} for p in self.policies for i, r, s in p["_coins"]]
        T["core.revenue_allocation"] = [{"policy_id": p["policy_id"], "company_code": c, "allocation_type_code": a, "allocation_pct": s}
                                        for p in self.policies for c, a, s in p["_alloc"]]
        return T


# ============================================================================
# 5. GHI FILE
# ============================================================================
BOOL_COLS = {"is_compulsory", "is_organization", "is_own_company", "is_revenue_deduction", "is_group_policy", "is_aggregated_retail"}


def lit(v, col):
    """Literal PostgreSQL"""
    if v is None:
        return "NULL"
    if col in BOOL_COLS:
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float, D)):
        return str(v)
    if isinstance(v, dt.datetime):
        return f"'{v:%Y-%m-%d %H:%M:%S}'"
    if isinstance(v, dt.date):
        return f"'{v:%Y-%m-%d}'"
    return "'" + str(v).replace("'", "''") + "'"


def write(T):
    sql = ["/* DỮ LIỆU DUMMY v2 (PostgreSQL) — sinh bởi build_v2.py. Chạy sau 01_ddl.sql:  psql -d <db> -f 02_data.sql */",
           "SET client_encoding = 'UTF8';", "BEGIN;", ""]
    for name, rows in T.items():
        cols = list(rows[0].keys())
        sql.append(f"-- {name}: {len(rows):,} dòng")
        for i in range(0, len(rows), 1000):
            sql.append(f"INSERT INTO {name} ({', '.join(cols)}) VALUES")
            sql.append(",\n".join("(" + ", ".join(lit(r[c], c) for c in cols) + ")" for r in rows[i:i + 1000]) + ";")
        sql.append("")
    sql.append("COMMIT;")
    (OUT / "02_data.sql").write_text("\n".join(sql), encoding="utf-8")


if __name__ == "__main__":
    g = Gen()
    g.run()
    T = g.tables()
    write(T)
    for k, v in T.items():
        print(f"{k:28s} {len(v):>7,}")
