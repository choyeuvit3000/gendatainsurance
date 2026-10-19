"""
SINH DỮ LIỆU DUMMY KHỐI LƯỢNG LỚN — POC Doanh thu bảo hiểm (PostgreSQL)
-----------------------------------------------------------------------
Dùng NGUYÊN mô hình v2 (schema ref + core, 01_ddl.sql, danh mục 02_data.sql)
nhưng sinh giao dịch ở quy mô vận hành: mỗi ngày > 50.000 giao dịch,
trải đều 01/08/2026 – 30/09/2026.

Công thức doanh thu không đổi so với v2:
    doanh thu = transaction_coverage.premium_vnd
              × coinsurance_share.share_pct ('OWN') / 100
              × revenue_allocation.allocation_pct / 100
    (chỉ chứng từ APPROVED, theo accounting_date)

Chạy:
    PG_URI=postgresql://user:pass@host:5432/db  python gen_volume.py --reset
    python gen_volume.py --dry-run            # chỉ sinh + in thống kê, không nạp
    python gen_volume.py --local --days 3     # nạp thử vào PostgreSQL nhúng (pgserver)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

HERE = Path(__file__).resolve().parent
V2 = Path(os.environ.get("V2_DIR", HERE))   # cần 01_ddl.sql, 01b_column_comments.sql, 02_data.sql (phần ref)

SEED = 20260930
START = dt.date(2026, 8, 1)
END = dt.date(2026, 9, 30)
HOLIDAYS = {dt.date(2026, 9, 1), dt.date(2026, 9, 2)}   # [QUY ƯỚC] Quốc khánh nghỉ 2 ngày (BLLĐ 2019 Đ112); ngày liền kề giả định 01/9
SCHOOL_START = dt.date(2026, 9, 5)                      # [QUY ƯỚC] khai giảng 5/9 (khung kế hoạch năm học Bộ GD&ĐT)

# Tham số hiệu chỉnh từ nguồn công khai (calibration/build_calibration.py → calibration.json)
CAL_PATH = Path(os.environ.get("CALIBRATION", HERE / "calibration" / "calibration.json"))
CAL = __import__("json").loads(CAL_PATH.read_text(encoding="utf-8"))

# USD: 2024–2025 lấy từ v2; 2026 trở đi là ước tính (doanh thu du lịch có thể ghi nhận tới 2028)
FX_2026 = {1: 25150, 2: 25200, 3: 25300, 4: 25450, 5: 25600, 6: 25750, 7: 25900,
           8: 26050, 9: 26150, 10: 26200, 11: 26250, 12: 26300}
FX_YM = {(2026, m): v for m, v in FX_2026.items()} | {(y, m): FX_2026[12] for y in (2027, 2028) for m in range(1, 13)}
FX_NOTE_2026 = "Ước tính (bám xu hướng tỷ giá hạch toán KBNN)"


# ---------------------------------------------------------------------------
# QUY MÔ DOANH THU — neo theo BCTC PVI, giống hệt v2 (xem GENERATION_LOGIC.md, scripts/why_meta.py)
# ---------------------------------------------------------------------------
# Mục tiêu năm theo nhóm sản phẩm (tỷ đồng) = v2 build_v2.group_targets(2025):
#   [CHÍNH THỨC] phí gốc 4 nghiệp vụ, BCTC kiểm toán 2025 Bảo hiểm PVI, thuyết minh 21 (trang 45 của PDF)
#   × tỷ lệ chia: Con người 75/15/5/5 [ƯỚC TÍNH]; Xe 24/76 (IAV 2024) [SUY RA]; Tài sản & thiệt hại × 50% [ƯỚC TÍNH]
TARGET_YEAR_2025 = {"SUC_KHOE": 2410.05, "SINH_MANG": 482.01, "DU_LICH": 160.67, "HOC_SINH": 160.67,
                    "TNDS_BB": 437.448, "VCX": 1385.252, "CHAY_NO": 3451.2, "TAI_SAN": 1890.6}
# [CHÍNH THỨC] tỷ trọng tháng: phí gốc phi nhân thọ toàn thị trường 2025 (Bộ Tài chính): tháng 8 = 5.592, tháng 9 = 8.002,
#   cả năm 88.054 tỷ (bản tin 01/2026). Giả định PVI có mùa vụ tháng giống toàn thị trường [ƯỚC TÍNH].
MOF_YEAR_2025 = 88_054
MONTH_SHARE = {8: CAL["mof_nonlife_2025"]["aug_2025"] / MOF_YEAR_2025, 9: CAL["mof_nonlife_2025"]["sep_2025"] / MOF_YEAR_2025}
# [QUY ƯỚC] yêu cầu dự án: > 50.000 giao dịch/ngày. Ở đúng quy mô PVI với giá niêm yết chỉ được ~13–25 nghìn/ngày,
#   nên nhân ĐỀU ngân sách mọi nhóm với cùng hệ số k (volume_scale) → cơ cấu doanh thu giữ nguyên như PVI,
#   đơn giá giữ nguyên biểu phí / giá niêm yết, chỉ số hợp đồng và doanh thu tuyệt đối tăng k lần.
MIN_DAILY = 52_000           # sàn cấp mới/tái tục ở ngày thấp nhất (SĐBS cộng thêm)
_SCALE = []


def month_budget_pvi(group, month):
    """Ngân sách doanh thu phí gốc (VND) theo đúng quy mô PVI 2025 (dùng cho năm 2026 — chưa có BCTC 2026)."""
    return TARGET_YEAR_2025[group] * 1e9 * MONTH_SHARE[month]


def volume_scale():
    """Hệ số quy mô k: ngày có số hợp đồng kỳ vọng thấp nhất trong cả kỳ đạt MIN_DAILY × 1,03."""
    if not _SCALE:
        days = [START + dt.timedelta(i) for i in range((END - START).days + 1)]
        exp = np.zeros(len(days))
        for code, _, prof, _ in PRODUCTS:
            for m in sorted({d.month for d in days}):
                w_month = sum(day_profile_mult(prof, d) for d in month_days(m))
                n_month = month_budget_pvi(PGROUP[code], m) * REV_SHARE[code] / mean_premium(code)
                for i, d in enumerate(days):
                    if d.month == m:
                        exp[i] += n_month * day_profile_mult(prof, d) / w_month
        _SCALE.append(MIN_DAILY * 1.03 / exp.min())
    return _SCALE[0]


def month_budget(group, month):
    """Ngân sách doanh thu phí gốc (VND) của nhóm sản phẩm trong tháng = quy mô PVI × hệ số k."""
    return month_budget_pvi(group, month) * volume_scale()


# Nhóm sản phẩm của từng sản phẩm (= ref.product.product_group_code của v2)
PGROUP = {"XE_TNDS_MOTO": "TNDS_BB", "XE_TNDS_OTO": "TNDS_BB", "XE_VCX_OTO": "VCX", "XE_VCX_MOTO": "VCX",
          "NG_HSSV_TN": "HOC_SINH", "NG_HSSV_SK": "HOC_SINH", "NG_DL_ND": "DU_LICH", "NG_DL_QT": "DU_LICH",
          "NG_SM_CN": "SINH_MANG", "NG_NVV": "SINH_MANG", "NG_TN24": "SINH_MANG", "NG_SK_CN": "SUC_KHOE",
          "NG_SK_NHOM": "SUC_KHOE", "NG_SK_BHN": "SUC_KHOE", "TS_NHA": "TAI_SAN", "TS_MRR": "TAI_SAN",
          "TS_MRRCN": "TAI_SAN", "CHN_BB": "CHAY_NO", "CHN_TN": "CHAY_NO"}
# [ƯỚC TÍNH] tỷ trọng DOANH THU của sản phẩm trong nhóm (PVI không công bố). Số hợp đồng = ngân sách × tỷ trọng ÷ phí bình quân
REV_SHARE = {"XE_TNDS_MOTO": .65, "XE_TNDS_OTO": .35, "XE_VCX_OTO": .80, "XE_VCX_MOTO": .20,
             "NG_HSSV_TN": .60, "NG_HSSV_SK": .40, "NG_DL_ND": .55, "NG_DL_QT": .45,
             "NG_SM_CN": .25, "NG_NVV": .35, "NG_TN24": .40, "NG_SK_CN": .30, "NG_SK_NHOM": .60, "NG_SK_BHN": .10,
             "TS_NHA": .20, "TS_MRR": .50, "TS_MRRCN": .30, "CHN_BB": .70, "CHN_TN": .30}
# Sản phẩm doanh nghiệp: được co giãn STBH / số người ở bước hiệu chỉnh (đơn bán lẻ giữ nguyên giá niêm yết)
SCALABLE_PRODUCTS = {"NG_SK_NHOM", "TS_MRR", "TS_MRRCN", "CHN_BB", "CHN_TN"}
# Sản phẩm đơn giá cố định theo xe / người: co giãn số lượng, không đổi đơn giá
UNIT_PRICED = {"XE_TNDS_MOTO", "XE_TNDS_OTO", "NG_HSSV_TN", "NG_HSSV_SK", "NG_DL_ND", "NG_DL_QT",
               "NG_SK_CN", "NG_SK_NHOM", "NG_SK_BHN"}


def sample_q(rng, q, n):
    """Lấy mẫu theo phân vị thực nghiệm (101 điểm p0..p100), nội suy tuyến tính."""
    return np.round(np.interp(rng.random(n) * 100, np.arange(101), np.asarray(q, dtype=float))).astype(np.int64)

# ---------------------------------------------------------------------------
# Sản phẩm: mã, viết tắt trên số đơn, hồ sơ mùa vụ, (cột 4 cũ: tỷ trọng số đơn — không còn dùng; số đơn suy ra từ ngân sách doanh thu)
# ---------------------------------------------------------------------------
PRODUCTS = [
    ("XE_TNDS_MOTO", "TXM", "digital",   0.3000),
    ("XE_TNDS_OTO",  "TXO", "agency",    0.0600),
    ("XE_VCX_OTO",   "VXO", "agency",    0.0180),
    ("XE_VCX_MOTO",  "VXM", "agency",    0.0200),
    ("NG_HSSV_TN",   "HTN", "school",    0.0400),
    ("NG_HSSV_SK",   "HSK", "school",    0.0150),
    ("NG_DL_ND",     "DLN", "travel_nd", 0.1500),
    ("NG_DL_QT",     "DLQ", "travel_qt", 0.0450),
    ("NG_SM_CN",     "SMC", "agency",    0.0120),
    ("NG_NVV",       "NVV", "bank",      0.0350),
    ("NG_TN24",      "T24", "digital",   0.1200),
    ("NG_SK_CN",     "SKC", "agency",    0.0450),
    ("NG_SK_NHOM",   "SKN", "corp",      0.0004),
    ("NG_SK_BHN",    "BHN", "agency",    0.0200),
    ("TS_NHA",       "TSN", "bank",      0.0220),
    ("TS_MRR",       "MRR", "corp",      0.0016),
    ("TS_MRRCN",     "MRC", "corp",      0.0004),
    ("CHN_BB",       "CBB", "corp",      0.0040),
    ("CHN_TN",       "CTN", "corp",      0.0020),
]
PCODE = [p[0] for p in PRODUCTS]
PIDX = {p: i for i, p in enumerate(PCODE)}

# Biểu phí TNDS bắt buộc (NĐ 67/2023 Phụ lục I, chưa VAT) và tỷ trọng loại xe [ƯỚC TÍNH]
TNDS_OTO = [(437_000, .45), (794_000, .12), (1_270_000, .02), (1_825_000, .01), (756_000, .10), (929_000, .04),
            (1_080_000, .04), (853_000, .10), (1_660_000, .07), (2_746_000, .03), (3_200_000, .02)]
TNDS_MOTO = [(55_000, .18), (60_000, .81), (290_000, .01)]

# Du lịch — [DATASET] Travel Insurance (bán qua trung gian): hãng bay online / đại lý online / đại lý offline;
#   [ƯỚC TÍNH] 20% bán qua kênh của công ty (web/app 12%, đại lý cá nhân 5%, trực tiếp 3%) — dataset không có nhóm này.
_AG = CAL["travel_insurance"]["agency_channel_share"]
_AIR = _AG.get("Airlines|Online", 0) + _AG.get("Airlines|Offline", 0)
_TA_ON, _TA_OFF = _AG.get("Travel Agency|Online", 0), _AG.get("Travel Agency|Offline", 0)
_MID = .80 / (_AIR + _TA_ON + _TA_OFF)
TRAVEL_CHANNEL_MIX = {"DIEN_TU": .12 + _AIR * _MID, "DAI_LY_TC": (_TA_ON + _TA_OFF) * _MID, "DAI_LY_CN": .05, "TRUC_TIEP": .03}
TRAVEL_DIGITAL_PARTNER_SHARE = _AIR * _MID / TRAVEL_CHANNEL_MIX["DIEN_TU"]        # phần kênh điện tử qua hãng bay
TRAVEL_AGENT_WEIGHTS = {"OTA_A": _TA_ON * .6, "OTA_B": _TA_ON * .4, "LH_A": _TA_OFF / 3, "LH_B": _TA_OFF / 3, "LH_C": _TA_OFF / 3}

# Kênh theo sản phẩm (tỷ trọng số đơn) — căn cứ thực tế phân phối từng sản phẩm
CHANNEL_MIX = {
    "XE_TNDS_MOTO": {"DIEN_TU": .45, "DAI_LY_TC": .25, "DAI_LY_CN": .20, "TRUC_TIEP": .10},
    "XE_TNDS_OTO":  {"DAI_LY_TC": .40, "DAI_LY_CN": .25, "DIEN_TU": .20, "TRUC_TIEP": .10, "BANCA": .05},
    "XE_VCX_OTO":   {"DAI_LY_TC": .35, "DAI_LY_CN": .25, "BANCA": .15, "TRUC_TIEP": .12, "DIEN_TU": .08, "MOI_GIOI": .05},
    "XE_VCX_MOTO":  {"DAI_LY_CN": .40, "DIEN_TU": .30, "BANCA": .15, "TRUC_TIEP": .15},
    "NG_HSSV_TN":   {"DAI_LY_CN": .45, "DIEN_TU": .30, "TRUC_TIEP": .25},
    "NG_HSSV_SK":   {"DAI_LY_CN": .45, "DIEN_TU": .30, "TRUC_TIEP": .25},
    "NG_DL_ND":     TRAVEL_CHANNEL_MIX,
    "NG_DL_QT":     TRAVEL_CHANNEL_MIX,
    "NG_SM_CN":     {"DAI_LY_CN": .60, "BANCA": .20, "DIEN_TU": .10, "TRUC_TIEP": .10},
    "NG_NVV":       {"BANCA": .90, "TRUC_TIEP": .10},
    "NG_TN24":      {"DIEN_TU": .60, "DAI_LY_CN": .30, "TRUC_TIEP": .10},
    "NG_SK_CN":     {"DAI_LY_CN": .50, "DIEN_TU": .20, "BANCA": .15, "TRUC_TIEP": .10, "MOI_GIOI": .05},
    "NG_SK_NHOM":   {"TRUC_TIEP": .50, "MOI_GIOI": .40, "DAU_THAU": .10},
    "NG_SK_BHN":    {"DAI_LY_CN": .50, "BANCA": .30, "DIEN_TU": .20},
    "TS_NHA":       {"BANCA": .50, "DAI_LY_CN": .30, "DIEN_TU": .10, "TRUC_TIEP": .10},
    "TS_MRR":       {"TRUC_TIEP": .50, "MOI_GIOI": .35, "DAI_LY_CN": .10, "DAU_THAU": .05},
    "TS_MRRCN":     {"TRUC_TIEP": .45, "MOI_GIOI": .50, "DAU_THAU": .05},
    "CHN_BB":       {"TRUC_TIEP": .45, "DAI_LY_CN": .30, "MOI_GIOI": .15, "BANCA": .05, "DAU_THAU": .05},
    "CHN_TN":       {"TRUC_TIEP": .45, "MOI_GIOI": .30, "DAI_LY_CN": .15, "BANCA": .10},
}
# Đối tác theo (sản phẩm, kênh). Trọng số lệch (đối tác lớn chiếm phần lớn).
PARTNERS_BY = {
    ("XE_TNDS_MOTO", "DIEN_TU"): ["VI_A", "VI_B", "TMDT_A", "VT_A"],
    ("XE_TNDS_MOTO", "DAI_LY_TC"): ["XM_A", "XM_B", "XM_C", "BC_A"],   # đại lý xe máy, bưu cục
    ("XE_TNDS_OTO", "DAI_LY_TC"): ["DK_A", "DK_B", "DK_C", "DK_D", "SR_A", "SR_B", "SR_C", "SR_D", "GA_A", "GA_B"],
    ("XE_TNDS_OTO", "DIEN_TU"): ["VI_A", "VI_B", "TMDT_A"],
    ("XE_TNDS_OTO", "BANCA"): ["CTTC_A", "CTTC_B"],
    ("XE_VCX_OTO", "DAI_LY_TC"): ["SR_A", "SR_B", "SR_C", "SR_D", "GA_A", "GA_B"],
    ("XE_VCX_OTO", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D", "CTTC_A", "CTTC_B"],
    ("XE_VCX_OTO", "DIEN_TU"): ["VI_A", "TMDT_A"],
    ("XE_VCX_MOTO", "DIEN_TU"): ["VI_A", "VI_B", "TMDT_A"],
    ("XE_VCX_MOTO", "BANCA"): ["CTTC_A", "CTTC_B"],
    ("NG_HSSV_TN", "DIEN_TU"): ["VI_A", "VI_B"],
    ("NG_HSSV_SK", "DIEN_TU"): ["VI_A", "VI_B"],
    ("NG_DL_ND", "DIEN_TU"): ["HK_A"],
    ("NG_DL_ND", "DAI_LY_TC"): ["OTA_A", "OTA_B", "LH_A", "LH_B", "LH_C"],
    ("NG_DL_QT", "DIEN_TU"): ["HK_A"],
    ("NG_DL_QT", "DAI_LY_TC"): ["OTA_A", "OTA_B", "LH_A", "LH_B", "LH_C"],
    ("NG_SM_CN", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D", "NH_E", "NH_F"],
    ("NG_SM_CN", "DIEN_TU"): ["VI_A", "VT_A"],
    ("NG_NVV", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D", "NH_E", "NH_F", "CTTC_A", "CTTC_B"],
    ("NG_TN24", "DIEN_TU"): ["VT_A", "VI_A", "VI_B", "TMDT_A"],
    ("NG_SK_CN", "DIEN_TU"): ["VI_A", "VI_B", "TMDT_A"],
    ("NG_SK_CN", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D", "NH_E", "NH_F"],
    ("NG_SK_BHN", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D", "NH_E", "NH_F"],
    ("NG_SK_BHN", "DIEN_TU"): ["VI_A", "VI_B"],
    ("TS_NHA", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D", "NH_E", "NH_F"],
    ("TS_NHA", "DIEN_TU"): ["VI_A", "TMDT_A"],
    ("CHN_BB", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D"],
    ("CHN_TN", "BANCA"): ["NH_A", "NH_B", "NH_C", "NH_D"],
}
BROKERS = ["MG_A", "MG_B", "MG_C", "MG_D"]

# Đối tác bổ sung ngoài danh mục v2: kênh bán TNDS xe máy qua đại lý tổ chức (thay garage / showroom ô tô)
EXTRA_PARTNERS = [
    ("XM_A", "Đại lý xe máy ủy quyền A", "DAI_LY_XE_MAY", "DAI_LY_TC"),
    ("XM_B", "Đại lý xe máy ủy quyền B", "DAI_LY_XE_MAY", "DAI_LY_TC"),
    ("XM_C", "Đại lý xe máy ủy quyền C", "DAI_LY_XE_MAY", "DAI_LY_TC"),
    ("BC_A", "Mạng lưới bưu cục A", "BUU_CHINH", "DAI_LY_TC"),
]
# Quy ước NULL theo nghiệp vụ nguồn (lớp bronze giữ đúng như hệ thống lõi):
#  - partner_code NULL = không qua đối tác (trực tiếp, đại lý cá nhân, đấu thầu, web/app công ty) — hợp lệ
#  - channel_code NULL = nguồn không khai báo kênh (~0,5%, dữ liệu bẩn có chủ đích) — lỗi dữ liệu
#  Thành viên "không qua đối tác" / "chưa xác định" chỉ tạo ở lớp phân tích (view rpt.v_revenue_line).
# Kênh điện tử: tỷ lệ bán qua nền tảng đối tác (phần còn lại là website/app của công ty)
DIGITAL_PARTNER_SHARE = .55

# Khách hàng: phân khúc theo sản phẩm
SEGMENT_MIX = {
    "XE_TNDS_MOTO": {"CA_NHAN": .97, "DN_TRONG_NUOC": .03},
    "XE_TNDS_OTO":  {"CA_NHAN": .82, "DN_TRONG_NUOC": .14, "DN_FDI": .02, "CO_QUAN_NN": .02},
    "XE_VCX_OTO":   {"CA_NHAN": .80, "DN_TRONG_NUOC": .15, "DN_FDI": .03, "CO_QUAN_NN": .02},
    "XE_VCX_MOTO":  {"CA_NHAN": 1.0},
    "NG_HSSV_TN":   {"CA_NHAN": 1.0},
    "NG_HSSV_SK":   {"CA_NHAN": 1.0},
    "NG_DL_ND":     {"CA_NHAN": .93, "DN_TRONG_NUOC": .05, "DN_FDI": .02},
    "NG_DL_QT":     {"CA_NHAN": .90, "DN_TRONG_NUOC": .06, "DN_FDI": .04},
    "NG_SM_CN":     {"CA_NHAN": 1.0},
    "NG_NVV":       {"CA_NHAN": 1.0},
    "NG_TN24":      {"CA_NHAN": 1.0},
    "NG_SK_CN":     {"CA_NHAN": 1.0},
    "NG_SK_NHOM":   {"DN_TRONG_NUOC": .60, "DN_FDI": .30, "CO_QUAN_NN": .10},
    "NG_SK_BHN":    {"CA_NHAN": 1.0},
    "TS_NHA":       {"HO_GIA_DINH": .70, "CA_NHAN": .30},
    "TS_MRR":       {"DN_TRONG_NUOC": .70, "DN_FDI": .20, "CO_QUAN_NN": .10},
    "TS_MRRCN":     {"DN_TRONG_NUOC": .55, "DN_FDI": .45},
    "CHN_BB":       {"DN_TRONG_NUOC": .68, "DN_FDI": .17, "CO_QUAN_NN": .08, "CO_SO_GD": .03, "HO_GIA_DINH": .04},
    "CHN_TN":       {"DN_TRONG_NUOC": .70, "DN_FDI": .20, "CO_QUAN_NN": .05, "HO_GIA_DINH": .05},
}
# Quy mô "kho" khách hàng tiềm năng theo phân khúc (khách thực tế = khách có hợp đồng)
POOL = {"CA_NHAN": 2_600_000, "HO_GIA_DINH": 120_000, "DN_TRONG_NUOC": 40_000, "DN_FDI": 6_000,
        "CO_QUAN_NN": 3_000, "CO_SO_GD": 8_000}
SEG_PREFIX = {"CA_NHAN": 1, "HO_GIA_DINH": 2, "DN_TRONG_NUOC": 3, "DN_FDI": 4, "CO_QUAN_NN": 5, "CO_SO_GD": 6}

# Tỷ lệ tái tục trong số hợp đồng (sản phẩm năm) [ƯỚC TÍNH]
RENEW_RATE = {"XE_TNDS_MOTO": .08, "XE_TNDS_OTO": .20, "XE_VCX_OTO": .45, "XE_VCX_MOTO": .20, "NG_HSSV_TN": .30,
              "NG_HSSV_SK": .30, "NG_DL_ND": 0, "NG_DL_QT": 0, "NG_SM_CN": .35, "NG_NVV": 0, "NG_TN24": .15,
              "NG_SK_CN": .40, "NG_SK_NHOM": .60, "NG_SK_BHN": .45, "TS_NHA": .40, "TS_MRR": .55, "TS_MRRCN": .60,
              "CHN_BB": .55, "CHN_TN": .55}

# Sửa đổi bổ sung trong kỳ: xác suất / hợp đồng và cơ cấu loại [ƯỚC TÍNH]
END_PROB = {"XE_TNDS_MOTO": .004, "XE_TNDS_OTO": .02, "XE_VCX_OTO": .07, "XE_VCX_MOTO": .02, "NG_HSSV_TN": .01,
            "NG_HSSV_SK": .01, "NG_DL_ND": .05, "NG_DL_QT": .06, "NG_SM_CN": .03, "NG_NVV": .04, "NG_TN24": .01,
            "NG_SK_CN": .04, "NG_SK_NHOM": .35, "NG_SK_BHN": .03, "TS_NHA": .03, "TS_MRR": .15, "TS_MRRCN": .18,
            "CHN_BB": .12, "CHN_TN": .12}
END_MIX = {
    "vehicle": {"END_NOCHG": .35, "END_INC": .20, "END_DEC": .10, "CANCEL": .25, "REFUND": .10},
    "group":   {"END_INC": .55, "END_DEC": .30, "END_NOCHG": .15},
    "property": {"END_INC": .40, "END_DEC": .20, "END_NOCHG": .25, "CANCEL": .10, "REFUND": .05},
    "loan":    {"REFUND": .70, "END_NOCHG": .30},
    "travel":  {"CANCEL": 1.0},
    "person":  {"END_NOCHG": .40, "END_INC": .20, "END_DEC": .10, "CANCEL": .20, "REFUND": .10},
}
END_KIND = {"XE_TNDS_MOTO": "vehicle", "XE_TNDS_OTO": "vehicle", "XE_VCX_OTO": "vehicle", "XE_VCX_MOTO": "vehicle",
            "NG_SK_NHOM": "group", "TS_MRR": "property", "TS_MRRCN": "property", "CHN_BB": "property",
            "CHN_TN": "property", "TS_NHA": "property", "NG_NVV": "loan", "NG_DL_ND": "travel", "NG_DL_QT": "travel"}

# Địa bàn: trọng số tỉnh (dân số + kinh tế) và công ty thành viên quản lý địa bàn
PROVINCE_W = {"HNI": .20, "HCM": .25, "HPG": .05, "QNH": .02, "BNH": .03, "HYN": .02, "NBH": .015, "PTO": .02,
              "TNN": .015, "TQG": .008, "LCI": .008, "LSN": .006, "CBG": .004, "DBN": .004, "LCU": .003, "SLA": .006,
              "THA": .03, "NAN": .03, "HTH": .01, "QTR": .01, "HUE": .01, "DNG": .035, "QNG": .012, "GLI": .012,
              "KHA": .015, "DLK": .015, "LDG": .015, "DNI": .04, "TNH": .02, "CTO": .025, "VLG": .012, "DTP": .012,
              "CMU": .008, "AGG": .015}
PROVINCE_HOME = {"HNI": {"HN1": .45, "HN2": .30, "HN3": .25}, "HCM": {"HC1": .45, "HC2": .35, "HC3": .20},
                 "HPG": "HPG", "QNH": "QNH", "BNH": "BNH", "HYN": "HN2", "NBH": "HN3", "PTO": "HN3", "TNN": "BNH",
                 "TQG": "BNH", "LCI": "HN3", "LSN": "BNH", "CBG": "BNH", "DBN": "HN3", "LCU": "HN3", "SLA": "HN3",
                 "THA": "THA", "NAN": "NAN", "HTH": "NAN", "QTR": "HUE", "HUE": "HUE", "DNG": "DNG", "QNG": "DNG",
                 "GLI": "DLK", "KHA": "KHA", "DLK": "DLK", "LDG": "KHA", "DNI": "DNI", "TNH": "HC3", "CTO": "CTO",
                 "VLG": "CTO", "DTP": "AGG", "CMU": "CTO", "AGG": "AGG"}
MEMBERS = ["HN1", "HN2", "HN3", "HPG", "QNH", "BNH", "THA", "NAN", "HUE", "DNG", "KHA", "DLK", "HC1", "HC2", "HC3",
           "DNI", "CTO", "AGG"]
COMPANY_PROVINCE = {"DEMO": "HNI", "HO": "HNI", "DGT": None, "HN1": "HNI", "HN2": "HNI", "HN3": "HNI", "HPG": "HPG",
                    "QNH": "QNH", "BNH": "BNH", "THA": "THA", "NAN": "NAN", "HUE": "HUE", "DNG": "DNG", "KHA": "KHA",
                    "DLK": "DLK", "HC1": "HCM", "HC2": "HCM", "HC3": "HCM", "DNI": "DNI", "CTO": "CTO", "AGG": "AGG"}
COMPANY_NAME = {"HO": "Khối Trụ sở chính", "DGT": "Trung tâm Kinh doanh số"}

# Giờ tạo chứng từ: văn phòng vs kênh số (trọng số theo giờ 0–23)
HOUR_OFFICE = [0, 0, 0, 0, 0, 0, 0, 1, 4, 9, 10, 9, 5, 6, 9, 10, 8, 5, 2, 1, 1, .5, 0, 0]
HOUR_DIGITAL = [1, .6, .4, .3, .3, .6, 1.5, 3, 4.5, 5.5, 6, 6, 5.5, 5, 5, 5.5, 6, 6.5, 7.5, 8.5, 9, 8, 5.5, 3]

LAST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô",
              "Dương", "Lý", "Đinh", "Trương", "Mai", "Cao", "Lưu", "Tạ", "Hà", "Đoàn"]
LAST_W = [38, 11, 9.5, 7, 5, 4, 4.5, 3.9, 3, 2.1, 2, 1.4, 1.3, 1.3, 1, .5, .6, .6, .5, .5, .4, .3, .5, .5]
MID_M = ["Văn", "Đức", "Minh", "Quốc", "Hữu", "Thanh", "Công", "Xuân", "Ngọc", "Hoàng", "Gia", "Tuấn", "Đình", "Quang"]
MID_F = ["Thị", "Ngọc", "Thu", "Thanh", "Minh", "Phương", "Hồng", "Kim", "Mai", "Bảo", "Khánh", "Thùy", "Hải", "Diệu"]
GIVEN_M = ["Anh", "Hùng", "Dũng", "Tuấn", "Minh", "Hải", "Long", "Nam", "Phong", "Quân", "Sơn", "Thắng", "Trung", "Việt",
           "Khoa", "Huy", "Đạt", "Hiếu", "Kiên", "Lâm", "Phúc", "Tài", "Thành", "Vinh", "Bình", "Cường", "Duy", "Hoàng",
           "Khánh", "Lộc", "Nghĩa", "Quang", "Tâm", "Toàn", "Trí", "Tùng"]
GIVEN_F = ["Anh", "Hương", "Lan", "Linh", "Mai", "Ngọc", "Nhung", "Phương", "Thảo", "Trang", "Vy", "Yến", "Hà", "Hạnh",
           "Hoa", "Huyền", "Giang", "Dung", "Chi", "Châu", "Hằng", "Hiền", "Loan", "Ly", "My", "Nga", "Ngân", "Oanh",
           "Quyên", "Tâm", "Thủy", "Trinh", "Tuyết", "Uyên", "Vân", "Xuân"]
ORG_W1 = ["Thép", "Xây dựng", "Dệt may", "Thực phẩm", "Điện tử", "Logistics", "Dược phẩm", "Nhựa", "Cơ khí", "Bao bì",
          "Thủy sản", "Gỗ", "Hóa chất", "Năng lượng", "Vận tải", "Thương mại", "Đầu tư", "Bất động sản", "Công nghệ",
          "Nông sản", "Giấy", "Xi măng", "Ô tô", "Da giày", "Điện máy"]
ORG_W2 = ["Phương Nam", "Hòa Phát", "Thành Công", "Đại Việt", "Hưng Thịnh", "Tân Phú", "An Phát", "Minh Long",
          "Phú Thái", "Sao Mai", "Bình Minh", "Hoàng Gia", "Trường Sơn", "Thái Bình Dương", "Kim Long", "Việt Á",
          "Đông Á", "Nam Việt", "Toàn Cầu", "Thiên Long", "Hà Thành", "Sài Gòn", "Hồng Hà", "Cửu Long", "Tây Đô",
          "Đồng Tâm", "Vạn Xuân", "Phú Gia", "Á Châu", "Hải Đăng"]
ORG_FORM = ["Công ty Cổ phần", "Công ty TNHH", "Công ty TNHH MTV", "Tổng công ty"]
FDI_W1 = ["Samsung", "Hanwha", "Lotte", "Toyota", "Honda", "Canon", "Foxconn", "Pou Chen", "Bosch", "Nestlé",
          "Heineken", "Intel", "LG", "Panasonic", "Yamaha", "Kyocera", "Shinsung", "Hyosung", "Daewoo", "Formosa"]
FDI_W2 = ["Electronics", "Vina", "Việt Nam", "Manufacturing", "Industrial", "Components", "Precision", "Global"]
GOV_W1 = ["Sở Y tế", "Sở Giáo dục và Đào tạo", "Sở Giao thông Vận tải", "Bệnh viện Đa khoa", "Trung tâm Y tế",
          "Ban Quản lý dự án", "Kho bạc Nhà nước", "Cục Thuế", "Bảo tàng", "Trung tâm Văn hóa"]
SCHOOL_W1 = ["Trường Tiểu học", "Trường THCS", "Trường THPT", "Trường Mầm non", "Trường Cao đẳng", "Trường Đại học"]
SCHOOL_W2 = ["Lê Quý Đôn", "Nguyễn Du", "Trần Phú", "Chu Văn An", "Lê Lợi", "Quang Trung", "Nguyễn Trãi",
             "Lý Thường Kiệt", "Hai Bà Trưng", "Kim Đồng", "Võ Thị Sáu", "Nguyễn Huệ", "Phan Chu Trinh",
             "Trần Hưng Đạo", "Hùng Vương", "Ngô Quyền", "Đoàn Thị Điểm", "Marie Curie", "Lương Thế Vinh", "Bế Văn Đàn"]


# ===========================================================================
# Tiện ích
# ===========================================================================
def wchoice(rng, items, weights, size):
    w = np.asarray(weights, dtype=float)
    return np.asarray(items, dtype=object)[rng.choice(len(items), size=size, p=w / w.sum())]


def lognorm(rng, median, sigma, size, lo, hi):
    return np.clip(np.exp(np.log(median) + sigma * rng.standard_normal(size)), lo, hi)


def zipf_weights(n, s=1.1):
    w = 1.0 / np.arange(1, n + 1) ** s
    return w / w.sum()


def draw_status(rng, dates):
    """VOID 0,4%; PENDING 0,3% + dồn vào 5 ngày cuối kỳ (chứng từ chưa kịp duyệt)."""
    days_left = (np.datetime64(END) - dates).astype("timedelta64[D]").astype(int)
    p_pend = .003 + np.select([days_left == 0, days_left == 1, days_left == 2, days_left == 3, days_left == 4],
                              [.14, .08, .05, .03, .02], 0)
    u = rng.random(len(dates))
    return np.where(u < .004, "VOID", np.where(u < .004 + p_pend, "PENDING", "APPROVED"))


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ===========================================================================
# 1. LỊCH: số giao dịch cấp mới/tái tục theo ngày × sản phẩm
# ===========================================================================
def day_profile_mult(profile, d: dt.date):
    """Hệ số theo ngày của từng nhóm sản phẩm.
    [QUY ƯỚC] lịch làm việc: kênh văn phòng nghỉ cuối tuần / lễ (BLLĐ 2019 Đ112: Quốc khánh nghỉ 2 ngày);
              kênh số hoạt động mọi ngày. Mức giảm cuối tuần là quy ước, không có số liệu công bố.
    [ƯỚC TÍNH] học sinh tập trung quanh khai giảng 5/9 (khung kế hoạch năm học của Bộ GD&ĐT); độ lớn ước tính.
    Không còn: hệ số cuối tháng, mùa du lịch, đà tăng trưởng (không có nguồn)."""
    wd = d.weekday()   # 0 = thứ Hai
    hol = d in HOLIDAYS
    if profile == "corp":
        return .05 if hol else [1, 1, 1, 1, 1, .25, .05][wd]
    if profile in ("agency", "bank"):
        return .30 if hol else [1, 1, 1, 1, 1, .60, .30][wd]
    if profile == "school":
        x = (d - SCHOOL_START).days
        return (.55 + 2.6 * np.exp(-((x + 6) / 11.0) ** 2)) * (.30 if hol else [1, 1, 1, 1, 1, .60, .30][wd])
    return 1.0                                   # digital, travel: mọi ngày như nhau


_MEAN = {}


def mean_premium(code):
    """Phí bình quân (VND) một hợp đồng của sản phẩm, ước lượng bằng mô phỏng gen_product (seed cố định)."""
    if code not in _MEAN:
        r = np.random.default_rng([SEED, PIDX[code]])
        n = 40_000
        o = gen_product(r, code, n, [dt.date(2026, 8, 15)] * n)
        p = o["prem_usd"] * FX_YM[(2026, 8)] if "prem_usd" in o else o["prem"]
        _MEAN[code] = float(np.mean(p))
    return _MEAN[code]


def month_days(m):
    first = dt.date(2026, m, 1)
    nxt = dt.date(2026 + (m == 12), m % 12 + 1, 1)
    return [first + dt.timedelta(i) for i in range((nxt - first).days)]


def build_calendar(rng, start, end):
    """Số hợp đồng cấp mới/tái tục theo ngày × sản phẩm, SUY RA TỪ NGÂN SÁCH DOANH THU (giống v2):
        hợp đồng của sản phẩm trong tháng = ngân sách nhóm × tỷ trọng doanh thu sản phẩm ÷ phí bình quân;
        rải theo hệ số ngày của sản phẩm (cuối tuần, lễ, khai giảng), có nhiễu Poisson.
    Trả về thêm ngân sách doanh thu của đợt theo nhóm (để hiệu chỉnh)."""
    days = [start + dt.timedelta(i) for i in range((end - start).days + 1)]
    mix = np.zeros((len(days), len(PRODUCTS)), dtype=np.int64)
    budget = {}
    for j, (code, _, prof, _) in enumerate(PRODUCTS):
        g = PGROUP[code]
        for m in sorted({d.month for d in days}):
            w_month = sum(day_profile_mult(prof, d) for d in month_days(m))
            rev = month_budget(g, m) * REV_SHARE[code]
            n_month = rev / mean_premium(code)
            for i, d in enumerate(days):
                if d.month == m:
                    w = day_profile_mult(prof, d) / w_month
                    mix[i, j] = rng.poisson(n_month * w)
                    budget[g] = budget.get(g, 0.0) + rev * w
    return days, mix.sum(axis=1), mix, budget       # mix: [ngày, sản phẩm]


# ===========================================================================
# 2. HỢP ĐỒNG + DÒNG PHÍ CHÍNH theo sản phẩm
# ===========================================================================
def gen_product(rng, code, n, issue):
    """Trả về dict mảng cho n hợp đồng của 1 sản phẩm (dòng phí chính).
    Ngày hiệu lực: [QUY ƯỚC] hiệu lực ngay ngày cấp (không có nguồn công khai về độ trễ) — trừ du lịch
    (phân bố thực nghiệm, xem calibration.json) và học sinh (từ ngày khai giảng)."""
    o = {"cnt": np.ones(n, dtype=np.int64), "group": np.zeros(n, bool), "lot": np.zeros(n, bool),
         "usd": np.zeros(n, bool), "rate": np.full(n, np.nan), "eff_delay": np.zeros(n, np.int64),
         "term": np.full(n, 365, np.int64)}
    u = rng.random(n)
    if code == "XE_TNDS_MOTO":
        tariff = wchoice(rng, [t for t, _ in TNDS_MOTO], [w for _, w in TNDS_MOTO], n).astype(float)
        lot = u < .004
        o["cnt"][lot] = rng.integers(50, 800, lot.sum())
        o["group"], o["lot"] = lot, lot
        o["prem"] = tariff * o["cnt"]
        o["si"] = 150e6 * o["cnt"]
    elif code == "XE_TNDS_OTO":
        tariff = wchoice(rng, [t for t, _ in TNDS_OTO], [w for _, w in TNDS_OTO], n).astype(float)
        fleet = u < .02
        o["cnt"][fleet] = rng.integers(5, 200, fleet.sum())
        o["group"] = fleet
        o["prem"] = tariff * o["cnt"]
        o["si"] = 150e6 * o["cnt"]
    elif code == "XE_VCX_OTO":
        fleet = u < .01
        o["cnt"][fleet] = rng.integers(3, 31, fleet.sum())
        o["group"] = fleet
        value = np.round(lognorm(rng, 750e6, .55, n, 300e6, 5e9), -6)
        o["si"] = value * o["cnt"]
        o["rate"] = np.round(rng.uniform(1.1, 2.0, n), 2)
    elif code == "XE_VCX_MOTO":
        value = np.round(rng.uniform(15e6, 90e6, n), -5)
        o["si"] = value
        o["rate"] = np.round(rng.uniform(1.5, 2.5, n), 2)
    elif code in ("NG_HSSV_TN", "NG_HSSV_SK"):
        grp = u < .01
        o["cnt"] = np.where(grp, rng.integers(100, 1201, n) if code == "NG_HSSV_TN" else rng.integers(50, 601, n),
                            rng.choice([1, 1, 1, 2], n))
        o["group"] = grp
        per = (rng.choice([100_000, 120_000, 150_000], n) if code == "NG_HSSV_TN"
               else rng.choice([200_000, 280_000, 350_000, 420_000, 520_000], n)).astype(float)
        o["prem"] = per * o["cnt"]
        o["si"] = (rng.choice([10e6, 20e6, 30e6, 50e6], n) if code == "NG_HSSV_TN" else rng.choice([20e6, 40e6, 60e6], n)) * o["cnt"]
        # hiệu lực: trước khai giảng → từ ngày khai giảng; sau đó → 0–3 ngày; hết hạn hết năm học
        eff = np.array([max((SCHOOL_START - d).days, 0) for d in issue]) if n else np.zeros(0, np.int64)
        o["eff_delay"] = eff
        o["term"] = np.array([(dt.date(2027, 9, 4) - (d + dt.timedelta(int(e)))).days + 1 for d, e in zip(issue, eff)],
                             dtype=np.int64) if n else np.zeros(0, np.int64)
    elif code == "NG_DL_ND":
        grp = u < .06
        o["cnt"] = np.where(grp, rng.integers(10, 46, n), rng.choice([1, 1, 1, 2, 2, 3, 4], n))
        o["group"] = grp
        per = np.round(rng.choice([17_000, 25_000, 35_000, 50_000, 80_000], n, p=[.25, .3, .2, .15, .1]), -3).astype(float)
        o["prem"] = per * o["cnt"]
        o["si"] = rng.choice([10e6, 20e6, 50e6, 100e6], n) * o["cnt"]
        # [NGUỒN THAY THẾ] Hotel booking demand (Data in Brief 2019), khách nội địa: số ngày đặt trước, độ dài chuyến đi
        o["eff_delay"] = sample_q(rng, CAL["hotel_booking"]["dom"]["lead_time_days_q"], n)
        o["term"] = np.maximum(sample_q(rng, CAL["hotel_booking"]["dom"]["trip_days_q"], n), 1)
    elif code == "NG_DL_QT":
        grp = u < .05
        o["cnt"] = np.where(grp, rng.integers(10, 31, n), rng.choice([1, 1, 2, 2, 3, 4], n))
        o["group"] = grp
        o["usd"] = rng.random(n) < .70
        per_usd = rng.choice([4, 8, 12, 18, 25, 35, 45], n, p=[.10, .18, .22, .20, .14, .10, .06]).astype(float)
        o["prem_usd"] = per_usd * o["cnt"]
        o["si_usd"] = rng.choice([10_000, 30_000, 50_000, 100_000], n) * o["cnt"].astype(float)
        # [NGUỒN THAY THẾ] lead time khách quốc tế (Hotel booking demand); [DATASET] thời hạn chuyến đi (Travel Insurance)
        o["eff_delay"] = sample_q(rng, CAL["hotel_booking"]["intl"]["lead_time_days_q"], n)
        o["term"] = np.maximum(sample_q(rng, CAL["travel_insurance"]["duration_days_q"], n), 1)
    elif code == "NG_SM_CN":
        o["si"] = np.round(lognorm(rng, 100e6, .7, n, 20e6, 500e6), -6)
        o["rate"] = np.round(rng.uniform(.1, .5, n), 3)
    elif code == "NG_NVV":
        lot = u < .01
        o["cnt"][lot] = rng.integers(10, 101, lot.sum())
        o["group"] = lot
        o["si"] = np.round(lognorm(rng, 400e6, .7, n, 50e6, 3e9), -6) * o["cnt"]
        o["rate"] = np.round(rng.uniform(.1, .5, n), 3)
        o["term"] = 365 * rng.integers(1, 6, n)
    elif code == "NG_TN24":
        o["si"] = rng.choice([10e6, 20e6, 30e6, 50e6, 100e6], n, p=[.25, .3, .2, .15, .1])
        o["rate"] = np.round(rng.uniform(.05, .3, n), 3)
    elif code == "NG_SK_CN":
        o["cnt"] = rng.choice([1, 1, 1, 2, 3, 4], n)
        per = np.round(lognorm(rng, 3e6, .6, n, 1.45e6, 15e6), -3)
        o["prem"] = per * o["cnt"]
        o["si"] = rng.choice([100e6, 200e6, 500e6, 1e9], n, p=[.3, .35, .25, .1]) * o["cnt"]
    elif code == "NG_SK_NHOM":
        o["cnt"] = np.round(lognorm(rng, 60, .9, n, 10, 1500)).astype(np.int64)
        o["group"] = np.ones(n, bool)
        per = np.round(rng.uniform(1.5e6, 6e6, n), -4)
        o["prem"] = per * o["cnt"]
        o["si"] = rng.choice([100e6, 200e6, 300e6, 500e6], n) * o["cnt"]
    elif code == "NG_SK_BHN":
        o["prem"] = np.round(lognorm(rng, 1.5e6, .6, n, 5e5, 5e6), -3)
        o["si"] = rng.choice([100e6, 200e6, 300e6, 500e6], n)
    elif code == "TS_NHA":
        o["si"] = np.round(lognorm(rng, 1.2e9, .6, n, 3e8, 5e9), -7)
        o["rate"] = np.round(rng.uniform(.05, .10, n), 3)
    elif code in ("TS_MRR", "TS_MRRCN", "CHN_BB", "CHN_TN"):
        med, sig, lo, hi = {"TS_MRR": (60e9, 1.3, 10e9, 1000e9), "TS_MRRCN": (400e9, 1.2, 50e9, 5000e9),
                            "CHN_BB": (25e9, 1.4, 2e9, 800e9), "CHN_TN": (15e9, 1.5, 1e9, 500e9)}[code]
        o["si"] = np.round(lognorm(rng, med, sig, n, lo, hi), -8)
        if code == "CHN_BB":   # tỷ lệ phí tối thiểu theo nhóm cơ sở (NĐ 67/2023 Phụ lục II)
            o["rate"] = rng.choice([.05, .10, .15, .20, .30, .40, .50], n, p=[.15, .25, .2, .15, .12, .08, .05])
        elif code == "CHN_TN":
            o["rate"] = np.round(rng.uniform(.05, .30, n), 3)
        else:
            o["rate"] = np.round(rng.uniform(.05, .20, n), 3)
        o["usd"] = rng.random(n) < {"TS_MRR": .20, "TS_MRRCN": .40}.get(code, 0)
    if "prem" not in o and "prem_usd" not in o:
        o["prem"] = np.round(o["si"] * o["rate"] / 100, -3)
    return o


# ===========================================================================
# 3. BỘ SINH CHÍNH
# ===========================================================================
class Gen:
    def __init__(self, start, end, state, ref, seed=SEED):
        """Sinh một đợt [start, end]. `state` giữ bộ đếm id / số hợp đồng / khách đã sinh giữa các đợt."""
        self.rng = np.random.default_rng([seed, start.toordinal()])
        self.start, self.end, self.state = start, end, state
        self.ref = ref
        self.max_comm = dict(zip(self.ref["product"]["product_code"], self.ref["product"]["max_commission_pct"].astype(float)))
        self.vat = dict(zip(self.ref["product"]["product_code"], self.ref["product"]["vat_rate"].astype(float)))

    # -------------------------------------------------------------- hợp đồng
    def run(self):
        rng = self.rng
        log("Lập lịch giao dịch theo ngày …")
        days, totals, mix, self.budget = build_calendar(rng, self.start, self.end)
        self.days, self.daily_newrenew = days, totals
        day0 = np.datetime64(self.start)

        parts = []
        for j, code in enumerate(PCODE):
            counts = mix[:, j]
            n = int(counts.sum())
            if not n:
                continue
            issue_idx = np.repeat(np.arange(len(days)), counts)
            issue = [days[i] for i in issue_idx]
            o = gen_product(rng, code, n, issue)
            df = pd.DataFrame({"product_code": code, "issue_date": day0 + issue_idx.astype("timedelta64[D]"),
                               "cnt": o["cnt"], "is_group": o["group"], "lot": o["lot"], "usd": o["usd"],
                               "rate": o["rate"], "eff_delay": o["eff_delay"], "term": o["term"]})
            if "prem_usd" in o:   # du lịch quốc tế: giá USD; đơn VND quy đổi lúc tính phí
                df["prem_usd"], df["si_usd"] = o["prem_usd"], o["si_usd"]
            else:
                df["prem_vnd0"], df["si_vnd0"] = o["prem"], o["si"]
            parts.append(df)
        pol = pd.concat(parts, ignore_index=True)
        pol = pol.sample(frac=1, random_state=SEED).sort_values("issue_date", kind="stable").reset_index(drop=True)
        n = len(pol)
        log(f"{n:,} hợp đồng cấp mới/tái tục")

        pol["effective_date"] = pol["issue_date"] + pol["eff_delay"].astype("timedelta64[D]")
        pol["expiry_date"] = pol["effective_date"] + (pol["term"] - 1).astype("timedelta64[D]")
        pol["accounting_date"] = np.maximum(pol["issue_date"], pol["effective_date"])
        pol["is_renew"] = rng.random(n) < pol["product_code"].map(RENEW_RATE).to_numpy()

        self.assign_channel(pol)
        log("  kênh, đối tác xong")
        self.assign_customer_company(pol)
        log("  khách hàng, đơn vị xong")
        self.pol = pol
        self.build_coverage()
        self.build_endorsements()
        self.build_transactions()
        self.build_coins_alloc()
        self.calibrate()
        self.build_customers()
        return self

    def assign_channel(self, pol):
        rng = self.rng
        ch = np.empty(len(pol), dtype=object)
        partner = np.full(len(pol), None, dtype=object)
        for code, idx in pol.groupby("product_code").indices.items():
            mixd = CHANNEL_MIX[code]
            ch[idx] = wchoice(rng, list(mixd), list(mixd.values()), len(idx))
        # đơn lô TNDS xe máy: đại lý tổ chức (bảng kê qua garage/đại lý xe)
        ch[pol["lot"].to_numpy() & (pol["product_code"] == "XE_TNDS_MOTO").to_numpy()] = "DAI_LY_TC"
        # trường học mua đơn nhóm: trực tiếp hoặc đấu thầu
        school_grp = pol["is_group"].to_numpy() & pol["product_code"].isin(["NG_HSSV_TN", "NG_HSSV_SK"]).to_numpy()
        ch[school_grp] = wchoice(rng, ["TRUC_TIEP", "DAU_THAU", "DAI_LY_CN"], [.6, .15, .25], school_grp.sum())
        prod = pol["product_code"].to_numpy()
        is_travel = np.isin(prod, ["NG_DL_ND", "NG_DL_QT"])
        for (code, c), plist in PARTNERS_BY.items():
            m = (prod == code) & (ch == c)
            if c == "DIEN_TU":
                share = TRAVEL_DIGITAL_PARTNER_SHARE if code in ("NG_DL_ND", "NG_DL_QT") else DIGITAL_PARTNER_SHARE
                m &= rng.random(len(pol)) < share
            if code in ("NG_DL_ND", "NG_DL_QT") and c == "DAI_LY_TC":
                weights = [TRAVEL_AGENT_WEIGHTS[x] for x in plist]          # [DATASET] đại lý online / offline
            else:
                weights = zipf_weights(len(plist), .9)
            partner[m] = wchoice(rng, plist, weights, m.sum())
        m = ch == "MOI_GIOI"
        partner[m] = wchoice(rng, BROKERS, zipf_weights(len(BROKERS), .8), m.sum())
        # dữ liệu bẩn có chủ đích: ~0,5% nguồn không khai báo kênh (NULL)
        dirty = rng.random(len(pol)) < .005
        ch[dirty], partner[dirty] = None, None
        pol["channel_code"], pol["partner_code"] = ch, partner
        # hoa hồng: % trần theo kênh (trực tiếp, đấu thầu, web/app công ty, không rõ kênh = 0)
        frac = np.where(np.isin(ch, ["DAI_LY_CN", "DAI_LY_TC", "BANCA", "MOI_GIOI"]), rng.uniform(.5, 1.0, len(pol)), 0.0)
        frac = np.where((ch == "DIEN_TU") & pd.notna(partner), rng.uniform(.3, .7, len(pol)), frac)
        # du lịch qua trung gian: [DATASET] tỷ lệ hoa hồng/doanh số thực tế (57% không có hoa hồng),
        # cắt ở trần 20% (TT 67/2023 Đ51) → comm_frac = min(tỷ lệ / 20%, 1)
        travel_mid = is_travel & pd.notna(partner)
        ratio = np.interp(rng.random(len(pol)) * 100, np.arange(101), CAL["travel_insurance"]["commission_ratio_q"])
        frac = np.where(travel_mid, np.minimum(ratio / .20, 1.0), frac)
        pol["comm_frac"] = frac

    def assign_customer_company(self, pol):
        rng = self.rng
        n = len(pol)
        prod = pol["product_code"].to_numpy()
        seg = np.empty(n, dtype=object)
        for code, idx in pol.groupby("product_code").indices.items():
            mixd = SEGMENT_MIX[code]
            seg[idx] = wchoice(rng, list(mixd), list(mixd.values()), len(idx))
        school_grp = pol["is_group"].to_numpy() & np.isin(prod, ["NG_HSSV_TN", "NG_HSSV_SK"])
        seg[school_grp] = "CO_SO_GD"
        lot = pol["lot"].to_numpy()

        # chọn khách trong kho: 30% từ nhóm khách thân thiết (lệch Zipf), còn lại ngẫu nhiên
        cust_no = np.zeros(n, dtype=np.int64)
        for s, size in POOL.items():
            m = np.where(seg == s)[0]
            if not len(m):
                continue
            loyal = rng.random(len(m)) < .30
            k = max(size // 50, 10)
            cust_no[m] = rng.integers(1, size + 1, len(m))
            cust_no[m[loyal]] = np.minimum(rng.zipf(1.6, loyal.sum()), k)
        pol["segment_code"] = seg
        pol["cust_key"] = pd.Series(seg).map(SEG_PREFIX).to_numpy() * 10_000_000 + cust_no

        # thuộc tính cố định của từng khách (tỉnh, công ty quản lý): hàm băm theo mã khách → nhất quán giữa các đơn
        provs = list(PROVINCE_W)
        pw = np.array([PROVINCE_W[p] for p in provs])
        cum = np.cumsum(pw / pw.sum())
        h = (pol["cust_key"].to_numpy() * 2654435761 % 2 ** 32) / 2 ** 32
        prov = np.asarray(provs, dtype=object)[np.searchsorted(cum, h, side="right").clip(0, len(provs) - 1)]
        h2 = (pol["cust_key"].to_numpy() * 40503 % 9973) / 9973
        home = np.empty(n, dtype=object)
        for p in provs:
            m = prov == p
            t = PROVINCE_HOME[p]
            if isinstance(t, str):
                home[m] = t
            else:
                c = np.cumsum(list(t.values()))
                home[m] = np.asarray(list(t), dtype=object)[np.searchsorted(c / c[-1], h2[m], side="right").clip(0, len(t) - 1)]
        pol["cust_province"], pol["cust_home"] = prov, home

        # đơn vị cấp đơn
        comp = home.copy()
        ch = pol["channel_code"].to_numpy()
        other = rng.random(n) < .12
        comp[other] = wchoice(rng, MEMBERS, [1] * len(MEMBERS), other.sum())
        dig = (ch == "DIEN_TU") & (rng.random(n) < .70)
        comp[dig] = "DGT"
        si_vnd = pol["si_vnd0"].fillna(0).to_numpy()
        big = (np.isin(prod, ["TS_MRR", "TS_MRRCN", "CHN_BB", "CHN_TN"]) & (si_vnd >= 500e9)) | \
              ((prod == "NG_SK_NHOM") & (pol["cnt"].to_numpy() > 800))
        comp[big & (rng.random(n) < .60)] = "HO"
        corp_broker = (ch == "MOI_GIOI") & np.isin(prod, ["TS_MRR", "TS_MRRCN", "CHN_BB", "CHN_TN", "NG_SK_NHOM"])
        comp[corp_broker & (rng.random(n) < .25)] = "HO"
        pol["issuing_company_code"] = comp
        # đơn lô: bên mua là "Khách lẻ theo bảng kê" của đơn vị cấp đơn
        lot_key = 9 * 10_000_000 + pd.Series(comp[lot]).map({c: i + 1 for i, c in enumerate(["HO", "DGT"] + MEMBERS)}).to_numpy()
        pol.loc[lot, "cust_key"] = lot_key
        pol.loc[lot, "segment_code"] = "CA_NHAN"
        pol.loc[lot, "cust_province"] = [COMPANY_PROVINCE[c] for c in comp[lot]]
        pol.loc[lot, "cust_home"] = comp[lot]

    # ------------------------------------------------------- dòng phí (coverage)
    def fx(self, dates):
        months = pd.DatetimeIndex(dates).month.to_numpy()
        years = pd.DatetimeIndex(dates).year.to_numpy()
        lut = np.zeros((2029 - 2026) * 12 + 13)
        for (y, m), v in FX_YM.items():
            lut[(y - 2026) * 12 + m] = v
        return lut[(years - 2026) * 12 + months]

    def build_coverage(self):
        rng = self.rng
        pol = self.pol
        n = len(pol)
        pol["policy_id"] = self.state["pid"] + np.arange(1, n + 1, dtype=np.int64)
        self.state["pid"] += n
        fx = self.fx(pol["accounting_date"])
        pol["fx_rate"] = np.where(pol["usd"], fx, 1.0)
        pol["currency_code"] = np.where(pol["usd"], "USD", "VND")

        # dòng chính
        # giá gốc: du lịch quốc tế niêm yết USD (prem_usd), còn lại VND (prem_vnd0); quy đổi theo tiền tệ hợp đồng
        usd = pol["usd"].to_numpy()
        p_usd, s_usd = pol["prem_usd"].to_numpy(), pol["si_usd"].to_numpy()
        p_vnd, s_vnd = pol["prem_vnd0"].to_numpy(), pol["si_vnd0"].to_numpy()
        listed_usd = ~np.isnan(p_usd)
        prem_orig = np.where(listed_usd, np.where(usd, p_usd, np.round(p_usd * fx, -3)),
                             np.where(usd, np.round(p_vnd / fx, 2), p_vnd))
        si_orig = np.where(listed_usd, np.where(usd, s_usd, s_usd * fx),
                           np.where(usd, np.round(s_vnd / fx, -3), s_vnd))
        # USD theo % STBH: tính lại phí từ STBH nguyên tệ để khớp tỷ lệ
        rate = pol["rate"].to_numpy()
        on_si = ~np.isnan(rate)
        prem_orig = np.where(on_si & usd, np.round(si_orig * rate / 100, 2), prem_orig)
        main = pd.DataFrame({"policy_id": pol["policy_id"], "product_code": pol["product_code"], "sum_insured": si_orig,
                             "premium_rate_pct": np.where(on_si, rate, np.nan), "insured_count": pol["cnt"],
                             "premium_orig": prem_orig, "line_no": 0})

        # dòng kèm theo (đơn nhiều sản phẩm)
        prod = pol["product_code"].to_numpy()
        extra = []
        m = (prod == "XE_VCX_OTO") & (rng.random(n) < .60)
        t = wchoice(rng, [x for x, _ in TNDS_OTO[:4]], [w for _, w in TNDS_OTO[:4]], m.sum()).astype(float)
        extra.append(pd.DataFrame({"policy_id": pol["policy_id"][m], "product_code": "XE_TNDS_OTO",
                                   "sum_insured": 150e6 * pol["cnt"][m], "premium_rate_pct": np.nan,
                                   "insured_count": pol["cnt"][m], "premium_orig": t * pol["cnt"][m], "line_no": 1}))
        m = (prod == "XE_VCX_MOTO") & (rng.random(n) < .50)
        extra.append(pd.DataFrame({"policy_id": pol["policy_id"][m], "product_code": "XE_TNDS_MOTO",
                                   "sum_insured": 150e6, "premium_rate_pct": np.nan, "insured_count": 1,
                                   "premium_orig": 60_000.0, "line_no": 1}))
        m = (prod == "NG_SK_CN") & (rng.random(n) < .25)
        si = rng.choice([50e6, 100e6, 200e6], m.sum()) * pol["cnt"][m].to_numpy()
        r = np.round(rng.uniform(.1, .2, m.sum()), 3)
        extra.append(pd.DataFrame({"policy_id": pol["policy_id"][m], "product_code": "NG_TN24", "sum_insured": si,
                                   "premium_rate_pct": r, "insured_count": pol["cnt"][m],
                                   "premium_orig": np.round(si * r / 100, -3), "line_no": 1}))
        m = (prod == "CHN_BB") & (rng.random(n) < .20)
        si = np.round(si_orig[m] * rng.uniform(.2, .6, m.sum()), -6)
        r = np.round(rng.uniform(.05, .15, m.sum()), 3)
        extra.append(pd.DataFrame({"policy_id": pol["policy_id"][m], "product_code": "TS_MRR", "sum_insured": si,
                                   "premium_rate_pct": r, "insured_count": 1,
                                   "premium_orig": np.round(si * r / 100, -3), "line_no": 1}))
        cov = pd.concat([main] + extra, ignore_index=True).sort_values(["policy_id", "line_no"], kind="stable")
        cov = cov.merge(pol[["policy_id", "fx_rate", "comm_frac", "usd"]], on="policy_id", how="left")
        cov["premium_orig"] = np.where(cov["usd"], np.round(cov["premium_orig"], 2), np.round(cov["premium_orig"]))
        cov["sum_insured"] = np.round(cov["sum_insured"], 2)
        # tỷ lệ phí lưu theo phí thực thu (phí đã làm tròn) / STBH → premium ≈ STBH × tỷ lệ luôn đúng
        on_si = cov["premium_rate_pct"].notna() & (cov["sum_insured"] > 0)
        cov.loc[on_si, "premium_rate_pct"] = np.round(cov.loc[on_si, "premium_orig"] / cov.loc[on_si, "sum_insured"] * 100, 6)
        self.cov0 = cov.reset_index(drop=True)
        log(f"{len(cov):,} dòng phí cấp mới/tái tục")

    # ------------------------------------------------------- sửa đổi bổ sung
    def build_endorsements(self):
        rng = self.rng
        pol = self.pol
        n = len(pol)
        # trạng thái chứng từ gốc; chỉ hợp đồng đã duyệt mới có SĐBS / hoàn phí / hủy
        pol["base_status"] = draw_status(rng, pol["issue_date"].to_numpy())
        prod = pol["product_code"].to_numpy()
        p_end = pd.Series(prod).map(END_PROB).to_numpy()
        pick = (rng.random(n) < p_end) & (pol["base_status"].to_numpy() == "APPROVED")
        issue = pol["issue_date"].to_numpy()
        eff = pol["effective_date"].to_numpy()
        expiry = pol["expiry_date"].to_numpy()
        kinds = pd.Series(prod).map(lambda c: END_KIND.get(c, "person")).to_numpy()
        is_travel = kinds == "travel"
        lag_eff = (eff - issue).astype("timedelta64[D]").astype(int)
        # du lịch: hủy chuyến trước ngày khởi hành
        delay = np.where(is_travel, (rng.random(n) * np.maximum(lag_eff - 1, 0)).astype(int) + 1,
                         rng.geometric(1 / 15, n))
        pick &= ~is_travel | (lag_eff >= 2)
        tdate = issue + delay.astype("timedelta64[D]")
        pick &= tdate <= np.datetime64(END)
        idx = np.where(pick)[0]
        types = np.empty(len(idx), dtype=object)
        for k, mixd in END_MIX.items():
            m = kinds[idx] == k
            types[m] = wchoice(rng, list(mixd), list(mixd.values()), m.sum())
        td = tdate[idx]
        # phần thời hạn còn lại
        total = (expiry[idx] - eff[idx]).astype("timedelta64[D]").astype(float) + 1
        remain = np.clip((expiry[idx] - np.maximum(td, eff[idx])).astype("timedelta64[D]").astype(float) + 1, 0, None)
        r = np.clip(remain / total, 0, 1)
        raw = np.select([types == "END_INC", types == "END_DEC", types == "REFUND", types == "CANCEL"],
                        [rng.uniform(.05, .30, len(idx)), -rng.uniform(.05, .20, len(idx)),
                         -rng.uniform(.10, .60, len(idx)), -np.ones(len(idx))], 0.0)
        prem_f = np.where(types == "CANCEL", -.90 * r, raw * r)
        e = pd.DataFrame({"policy_id": pol["policy_id"].to_numpy()[idx], "txn_type_code": types,
                          "txn_date": td, "prem_f": prem_f, "raw": raw})
        self.endo = e
        log(f"{len(e):,} giao dịch SĐBS / hoàn phí / hủy")

    # ------------------------------------------------------- giao dịch + dòng phí cuối
    def build_transactions(self):
        rng = self.rng
        pol, e = self.pol, self.endo
        new = pd.DataFrame({"policy_id": pol["policy_id"], "txn_type_code": np.where(pol["is_renew"], "RENEW", "NEW"),
                            "txn_date": pol["issue_date"], "seq": 0})
        e2 = e[["policy_id", "txn_type_code", "txn_date"]].assign(seq=1)
        tx = pd.concat([new, e2], ignore_index=True)
        tx = tx.merge(pol[["policy_id", "effective_date", "channel_code", "partner_code", "issuing_company_code", "usd"]],
                      on="policy_id", how="left")
        # ngày ghi nhận = max(ngày chứng từ, ngày hiệu lực)
        tx["accounting_date"] = np.maximum(tx["txn_date"], tx["effective_date"])
        fx = self.fx(tx["accounting_date"])
        tx["fx_rate"] = np.where(tx["usd"], fx, 1.0)
        # giờ tạo chứng từ
        n = len(tx)
        digital = (tx["channel_code"] == "DIEN_TU").to_numpy() | ((tx["channel_code"] == "DAI_LY_CN").to_numpy() & (rng.random(n) < .3))
        ho = np.array(HOUR_OFFICE) / sum(HOUR_OFFICE)
        hd = np.array(HOUR_DIGITAL) / sum(HOUR_DIGITAL)
        hour = np.where(digital, rng.choice(24, n, p=hd), rng.choice(24, n, p=ho))
        secs = hour * 3600 + rng.integers(0, 3600, n)
        tx["created_at"] = tx["txn_date"] + secs.astype("timedelta64[s]")
        # trạng thái: chứng từ gốc lấy từ build_endorsements; SĐBS rút ngẫu nhiên cùng quy luật
        base = tx[["policy_id"]].merge(pol[["policy_id", "base_status"]], on="policy_id", how="left")["base_status"].to_numpy()
        tx["status"] = np.where(tx["seq"].to_numpy() == 0, base, draw_status(rng, tx["txn_date"].to_numpy()))
        # người tạo
        comp = tx["issuing_company_code"].to_numpy()
        partner = tx["partner_code"].to_numpy()
        is_api = (tx["channel_code"] == "DIEN_TU").to_numpy() & pd.notna(partner)
        web = (tx["channel_code"] == "DIEN_TU").to_numpy() & pd.isna(partner)
        staff = pd.Series(comp).astype(str) + ".NV" + pd.Series(rng.integers(1, 41, n)).astype(str).str.zfill(2)
        tx["created_by"] = np.where(is_api, "API." + pd.Series(partner).astype(str), np.where(web, "WEB.APP", staff))

        # sắp xếp theo thời điểm tạo → txn_id tăng dần theo thời gian
        tx = tx.sort_values(["created_at", "policy_id", "seq"], kind="stable").reset_index(drop=True)
        tx["txn_id"] = self.state["tid"] + np.arange(1, len(tx) + 1, dtype=np.int64)
        self.state["tid"] += len(tx)

        # số hợp đồng: <năm>-<đơn vị>-<SP>-<số thứ tự 7 chữ số>, thứ tự theo ngày cấp
        short = {p[0]: p[1] for p in PRODUCTS}
        key = pol["issuing_company_code"] + "-" + pol["product_code"].map(short)
        seqno = pol.groupby(key).cumcount() + 1 + key.map(self.state["seq"]).fillna(0).astype(np.int64)
        for k, v in pd.Series(seqno.to_numpy(), index=key.to_numpy()).groupby(level=0).max().items():
            self.state["seq"][k] = int(v)
        pol["policy_no"] = "2026-" + key + "-" + seqno.astype(str).str.zfill(7)
        # tái tục: số hợp đồng năm trước (ngoài kỳ dữ liệu → lưu dạng text)
        prev = pd.Series(None, index=pol.index, dtype=object)
        rn = pol["is_renew"].to_numpy()
        prev[rn] = "2025-" + key[rn] + "-" + pd.Series(self.rng.integers(1, 9_999_999, rn.sum())).astype(str).str.zfill(7).to_numpy()
        pol["prev_policy_no"] = prev
        self.pol = pol
        tx = tx.merge(self.pol[["policy_id", "policy_no"]], on="policy_id", how="left")
        tx["txn_no"] = tx["policy_no"] + "/" + tx["seq"].astype(str).str.zfill(2)
        self.tx = tx

        # dòng phí của giao dịch
        c0 = self.cov0.merge(tx[tx["seq"] == 0][["policy_id", "txn_id"]], on="policy_id")
        e = self.endo.merge(tx[tx["seq"] == 1][["policy_id", "txn_id", "txn_type_code"]], on=["policy_id", "txn_type_code"])
        ce = self.cov0.merge(e[["policy_id", "txn_id", "txn_type_code", "prem_f", "raw"]], on="policy_id")
        t = ce["txn_type_code"].to_numpy()
        ce["premium_orig"] = np.where(ce["usd"], np.round(ce["premium_orig"] * ce["prem_f"], 2),
                                      np.round(ce["premium_orig"] * ce["prem_f"]))
        ce["sum_insured"] = np.select([t == "CANCEL", t == "END_NOCHG"], [-ce["sum_insured"], 0],
                                      np.round(ce["sum_insured"] * ce["raw"], 2))
        ce["insured_count"] = np.select([t == "CANCEL", t == "END_NOCHG"], [ce["insured_count"], 0],
                                        np.maximum(np.round(ce["insured_count"] * np.abs(ce["raw"])), 1)).astype(np.int64)
        ce.loc[t == "END_NOCHG", "premium_orig"] = 0.0
        cov = pd.concat([c0, ce.drop(columns=["txn_type_code", "prem_f", "raw"])], ignore_index=True)
        cov = cov.drop(columns=["fx_rate"]).merge(tx[["txn_id", "fx_rate"]], on="txn_id")
        cov = cov.sort_values(["txn_id", "line_no"], kind="stable").reset_index(drop=True)
        cov["coverage_id"] = self.state["cid"] + np.arange(1, len(cov) + 1, dtype=np.int64)
        self.state["cid"] += len(cov)
        cov["premium_vnd"] = np.round(cov["premium_orig"] * cov["fx_rate"]).astype(np.int64)
        cov["vat_vnd"] = np.round(cov["premium_vnd"] * cov["product_code"].map(self.vat) / 100).astype(np.int64)
        cov["commission_rate_pct"] = np.round(cov["comm_frac"] * cov["product_code"].map(self.max_comm), 4)
        self.cov = cov
        log(f"{len(tx):,} giao dịch, {len(cov):,} dòng phí")

    # ------------------------------------------------------- đồng BH + phân bổ
    def build_coins_alloc(self):
        rng = self.rng
        pol = self.pol
        n = len(pol)
        prod = pol["product_code"].to_numpy()
        si_vnd = (self.cov0[self.cov0["line_no"] == 0].set_index("policy_id")["sum_insured"]
                  .reindex(pol["policy_id"]).to_numpy() * pol["fx_rate"].to_numpy())
        coin = ((np.isin(prod, ["TS_MRR", "TS_MRRCN", "CHN_BB", "CHN_TN"]) & (si_vnd >= 300e9) & (rng.random(n) < .55)) |
                ((prod == "NG_SK_NHOM") & (pol["cnt"].to_numpy() > 1000) & (rng.random(n) < .30)))
        others_all = ["CO_A", "CO_B", "CO_C", "CO_D", "CO_E", "CO_F"]
        rows = [pd.DataFrame({"policy_id": pol["policy_id"][~coin], "insurer_code": "OWN", "role": "SOLE", "share_pct": 100.0})]
        recs = []
        for pid in pol["policy_id"].to_numpy()[coin]:
            lead = rng.random() < .4
            own = float(rng.choice([40, 50, 60, 70])) if lead else float(rng.choice([10, 15, 20, 25, 30, 40]))
            k = int(rng.integers(1, 4))
            others = rng.choice(others_all, k, replace=False)
            w = rng.dirichlet(np.ones(k) * 2) * (100 - own)
            w = np.round(w, 2)
            w[-1] = round(100 - own - w[:-1].sum(), 2)
            recs.append((pid, "OWN", "LEADER" if lead else "FOLLOWER", own))
            for i, (o, s) in enumerate(zip(others, w)):
                recs.append((pid, o, "FOLLOWER" if (lead or i > 0) else "LEADER", float(s)))
        rows.append(pd.DataFrame(recs, columns=["policy_id", "insurer_code", "role", "share_pct"]))
        self.coins = pd.concat(rows, ignore_index=True).sort_values(["policy_id", "insurer_code"]).reset_index(drop=True)
        log(f"{int(coin.sum()):,} hợp đồng đồng bảo hiểm")

        comp = pol["issuing_company_code"].to_numpy()
        home = pol["cust_home"].to_numpy()
        u = rng.random(n)
        pid = pol["policy_id"].to_numpy()
        ho_coop = (comp == "HO") & (home != "HO") & (u < .60)
        dgt_tr = (comp == "DGT") & (u < .50)
        mem = np.isin(comp, MEMBERS)
        mem_coop = mem & (u < .10)
        mem_tr = mem & (u >= .10) & (u < .11)
        single = ~(ho_coop | dgt_tr | mem_coop | mem_tr)
        mine_ho = rng.choice([50.0, 60.0, 70.0], n)
        mine_mem = rng.choice([50.0, 60.0, 70.0, 80.0], n)
        partner_mem = wchoice(rng, MEMBERS, [1] * len(MEMBERS), n)
        partner_mem = np.where(partner_mem == comp, np.where(comp == "HN1", "HC1", "HN1"), partner_mem)
        al = [
            pd.DataFrame({"policy_id": pid[single], "company_code": comp[single], "allocation_type_code": "TU_KHAI_THAC", "allocation_pct": 100.0}),
            pd.DataFrame({"policy_id": pid[ho_coop], "company_code": "HO", "allocation_type_code": "HO_TRO_CHEO", "allocation_pct": mine_ho[ho_coop]}),
            pd.DataFrame({"policy_id": pid[ho_coop], "company_code": home[ho_coop], "allocation_type_code": "HO_TRO_CHEO", "allocation_pct": 100 - mine_ho[ho_coop]}),
            pd.DataFrame({"policy_id": pid[dgt_tr], "company_code": home[dgt_tr], "allocation_type_code": "CHUYEN_GIAO", "allocation_pct": 100.0}),
            pd.DataFrame({"policy_id": pid[mem_coop], "company_code": comp[mem_coop], "allocation_type_code": "HO_TRO_CHEO", "allocation_pct": mine_mem[mem_coop]}),
            pd.DataFrame({"policy_id": pid[mem_coop], "company_code": partner_mem[mem_coop], "allocation_type_code": "HO_TRO_CHEO", "allocation_pct": 100 - mine_mem[mem_coop]}),
            pd.DataFrame({"policy_id": pid[mem_tr], "company_code": partner_mem[mem_tr], "allocation_type_code": "CHUYEN_GIAO", "allocation_pct": 100.0}),
        ]
        self.alloc = pd.concat(al, ignore_index=True).sort_values(["policy_id", "company_code"]).reset_index(drop=True)

    # ------------------------------------------------------- hiệu chỉnh về ngân sách (giống v2)
    def calibrate(self):
        """Đơn bán lẻ giữ nguyên giá niêm yết. Co giãn đơn doanh nghiệp / nhóm / lô (STBH, số người, phí) để doanh thu
        phí gốc của từng nhóm sản phẩm khớp ngân sách đợt. Doanh thu đo như v2: giao dịch cấp mới / tái tục, đã duyệt,
        phần của công ty. Hệ số áp cho mọi dòng phí (kể cả SĐBS) của hợp đồng co giãn được, theo nhóm của dòng phí."""
        cov, tx, pol = self.cov, self.tx, self.pol
        own = self.coins[self.coins["insurer_code"] == "OWN"].set_index("policy_id")["share_pct"] / 100
        p = pol.set_index("policy_id")
        pid = cov["policy_id"]
        grp_pol = pid.map(p["is_group"] | p["lot"]).to_numpy()
        scal = pid.map(p["product_code"]).isin(SCALABLE_PRODUCTS).to_numpy() | grp_pol
        g_line = cov["product_code"].map(PGROUP).to_numpy()
        t = tx.set_index("txn_id")
        base = ((cov["txn_id"].map(t["seq"]) == 0) & (cov["txn_id"].map(t["status"]) == "APPROVED")).to_numpy()
        rev = cov["premium_vnd"].to_numpy() * pid.map(own).to_numpy()
        f = np.ones(len(cov))
        self.calib = {}
        for g, target in sorted(self.budget.items()):
            m = g_line == g
            fixed, sc = rev[m & base & ~scal].sum(), rev[m & base & scal].sum()
            k = max(.05, (target - fixed) / sc) if sc > 0 else 1.0
            f[m & scal] = k
            self.calib[g] = (target / 1e9, fixed / 1e9, sc / 1e9, k)
        # Sản phẩm có đơn giá cố định (biểu phí TNDS, phí theo người): co giãn SỐ XE / SỐ NGƯỜI rồi phí = đơn giá × số mới,
        # để phí mỗi xe / mỗi người vẫn đúng biểu phí. Sản phẩm tính % × STBH: nhân STBH và phí cùng hệ số.
        pol_cnt = pid.map(p["cnt"]).to_numpy().astype(float)
        unit = cov["product_code"].isin(UNIT_PRICED).to_numpy()
        new_cnt = np.maximum(np.round(pol_cnt * f), np.where(grp_pol, 2, 1))
        f = np.where(scal & (unit | grp_pol), np.where(scal, new_cnt / pol_cnt, 1.0), f)
        usd = cov["usd"].to_numpy().astype(bool)
        cov["premium_orig"] = np.where(usd, np.round(cov["premium_orig"] * f, 2), np.round(cov["premium_orig"] * f))
        cov["sum_insured"] = np.round(cov["sum_insured"] * f, 2)
        cnt = cov["insured_count"].to_numpy()
        cov["insured_count"] = np.where(scal & grp_pol & (cnt > 0), np.maximum(np.round(cnt * f), 1), cnt).astype(np.int64)
        cov["premium_vnd"] = np.round(cov["premium_orig"] * cov["fx_rate"]).astype(np.int64)
        cov["vat_vnd"] = np.round(cov["premium_vnd"] * cov["product_code"].map(self.vat) / 100).astype(np.int64)
        self.cov = cov
        log("  hiệu chỉnh: " + " · ".join(f"{g} ×{v[3]:.2f}" for g, v in self.calib.items()))
        log(f"  hệ số quy mô k = {volume_scale():.3f} (doanh thu = k × quy mô PVI, cơ cấu giữ nguyên)")

    # ------------------------------------------------------- khách hàng
    def build_customers(self):
        rng = self.rng
        pol = self.pol
        g = pol.groupby("cust_key").agg(segment_code=("segment_code", "first"), province_code=("cust_province", "first"),
                                        home_company_code=("cust_home", "first"), first_date=("issue_date", "min"))
        g = g.reset_index()
        g = g[~g["cust_key"].isin(self.state["seen"])].reset_index(drop=True)
        self.state["seen"].update(g["cust_key"].tolist())
        n = len(g)
        key = g["cust_key"].to_numpy()
        seg = g["segment_code"].to_numpy()
        g["customer_code"] = "KH" + pd.Series(key + self.state["cust_base"]).astype(str).str.zfill(9)
        agg = key >= 9 * 10_000_000
        g["is_aggregated_retail"] = agg
        # tên
        name = np.empty(n, dtype=object)
        gender = np.full(n, None, dtype=object)
        birth = np.full(n, np.nan)
        ind = np.isin(seg, ["CA_NHAN", "HO_GIA_DINH"]) & ~agg
        k = ind.sum()
        male = rng.random(k) < .52
        ln = wchoice(rng, LAST_NAMES, LAST_W, k)
        mid = np.where(male, wchoice(rng, MID_M, [1] * len(MID_M), k), wchoice(rng, MID_F, [1] * len(MID_F), k))
        gv = np.where(male, wchoice(rng, GIVEN_M, [1] * len(GIVEN_M), k), wchoice(rng, GIVEN_F, [1] * len(GIVEN_F), k))
        full = pd.Series(ln) + " " + pd.Series(mid) + " " + pd.Series(gv)
        hh = seg[ind] == "HO_GIA_DINH"
        full[hh] = "Hộ gia đình " + full[hh]
        name[ind] = full.to_numpy()
        gender[ind] = np.where(male, "M", "F")
        birth[ind] = np.clip(np.round(rng.normal(1986, 11, k)), 1945, 2007)
        for s, w1, w2, fmt in [("DN_TRONG_NUOC", ORG_W1, ORG_W2, "dn"), ("DN_FDI", FDI_W1, FDI_W2, "fdi"),
                               ("CO_QUAN_NN", GOV_W1, None, "gov"), ("CO_SO_GD", SCHOOL_W1, SCHOOL_W2, "school")]:
            m = (seg == s) & ~agg
            c = m.sum()
            if not c:
                continue
            a = wchoice(rng, w1, [1] * len(w1), c)
            provn = pd.Series(g["province_code"][m].to_numpy()).map(self.ref["province_name_short"]).fillna("").to_numpy()
            if fmt == "dn":
                form = wchoice(rng, ORG_FORM, [.45, .35, .15, .05], c)
                b = wchoice(rng, w2, [1] * len(w2), c)
                name[m] = (pd.Series(form) + " " + pd.Series(a) + " " + pd.Series(b) + " " + pd.Series(provn)).str.strip().to_numpy()
            elif fmt == "fdi":
                b = wchoice(rng, w2, [1] * len(w2), c)
                name[m] = ("Công ty TNHH " + pd.Series(a) + " " + pd.Series(b) + " " + pd.Series(provn)).str.strip().to_numpy()
            elif fmt == "gov":
                name[m] = (pd.Series(a) + " " + pd.Series(provn)).str.strip().to_numpy()
            else:
                b = wchoice(rng, w2, [1] * len(w2), c)
                name[m] = (pd.Series(a) + " " + pd.Series(b) + " " + pd.Series(provn)).str.strip().to_numpy()
        comp_by_lot = {9 * 10_000_000 + i + 1: c for i, c in enumerate(["HO", "DGT"] + MEMBERS)}
        name[agg] = ["Khách lẻ theo bảng kê – " + self.ref["company_name"][comp_by_lot[x]] for x in key[agg]]
        g["customer_name"] = name
        g["gender"], g["birth_year"] = gender, birth
        org = np.isin(seg, ["DN_TRONG_NUOC", "DN_FDI", "CO_QUAN_NN", "CO_SO_GD"])
        tax = pd.Series(rng.integers(100_000_000, 999_999_999, n)).astype(str).radd("0")
        g["tax_code"] = np.where(org, tax, None)
        # ngày tạo khách: 55% là khách mới trong kỳ (= ngày mua đầu tiên), còn lại khách cũ từ 2015
        old = (rng.random(n) >= .55) | agg
        span = (g["first_date"] - np.datetime64("2015-01-01")).dt.days.to_numpy()
        back = (rng.random(n) * span).astype(int)
        g["created_date"] = np.where(old, np.datetime64("2015-01-01") + back.astype("timedelta64[D]"), g["first_date"])
        g.loc[agg, "created_date"] = np.datetime64("2020-01-01")
        self.customers = g
        self.pol = pol.assign(customer_code="KH" + (pol["cust_key"] + self.state["cust_base"]).astype(str).str.zfill(9))
        log(f"{n:,} khách hàng")

    # ------------------------------------------------------- thống kê
    def stats(self):
        tx, cov, coins, alloc = self.tx, self.cov, self.coins, self.alloc
        daily = tx[tx["txn_date"] <= np.datetime64(self.end)].groupby("txn_date").size()
        log(f"Giao dịch/ngày: min {daily.min():,} · max {daily.max():,} · TB {daily.mean():,.0f} · {len(daily)} ngày")
        own = coins[coins["insurer_code"] == "OWN"].set_index("policy_id")["share_pct"]
        a = cov.merge(tx[["txn_id", "status"]], on="txn_id")
        a = a[a["status"] == "APPROVED"]
        a["rev"] = a["premium_vnd"] * a["policy_id"].map(own) / 100
        grp = self.ref["product"].set_index("product_code")["product_group_code"]
        lob = (self.ref["product_group"].merge(self.ref["line_of_business"], on="lob_code")
               .set_index("product_group_code")["poc_group_code"])
        by = a.groupby(a["product_code"].map(grp))["rev"].sum() / 1e9
        tot = by.sum()
        log(f"Doanh thu (APPROVED, phần công ty): {tot:,.0f} tỷ")
        log("Ngân sách đợt (tỷ): " + " · ".join(f"{g} {v[0]:,.1f}" for g, v in self.calib.items()))
        for k, v in by.sort_values(ascending=False).items():
            print(f"    {k:<10} {v:>10,.1f} tỷ  {v / tot:6.1%}")
        poc = a.groupby(a["product_code"].map(grp).map(lob))["rev"].sum() / 1e9
        print("    Nhóm POC: " + " · ".join(f"{k} {v / tot:.1%}" for k, v in poc.items()))
        bad = coins.groupby("policy_id")["share_pct"].sum().round(4).ne(100).sum()
        bad2 = alloc.groupby("policy_id")["allocation_pct"].sum().round(4).ne(100).sum()
        log(f"Kiểm tra: đồng BH ≠ 100%: {bad} · phân bổ ≠ 100%: {bad2}")


# ===========================================================================
# 4. DANH MỤC TỪ v2
# ===========================================================================
REF_TABLES = ["region", "province", "company", "line_of_business", "regulatory_line", "product_group", "product",
              "channel", "partner", "customer_segment", "currency", "fx_rate", "transaction_type", "insurer", "allocation_type"]


def v2_ref_sql():
    """Trích các khối INSERT danh mục từ v2/02_data.sql (trừ ref.customer)."""
    text = (V2 / "02_data.sql").read_text(encoding="utf-8")
    blocks = {}
    for m in re.finditer(r"^-- ref\.(\w+): [\d,]+ dòng\n(INSERT INTO .*?;)\n", text, flags=re.M | re.S):
        blocks[m.group(1)] = m.group(2)
    return [blocks[t] for t in REF_TABLES]


def load_v2_ref():
    text = (V2 / "02_data.sql").read_text(encoding="utf-8")
    ref = {}

    def rows(table):
        m = re.search(rf"^INSERT INTO ref\.{table} \((.*?)\) VALUES\n(.*?);\n", text, flags=re.M | re.S)
        cols = [c.strip() for c in m.group(1).split(",")]
        out = []
        for line in m.group(2).splitlines():
            vals = re.findall(r"'((?:[^']|'')*)'|(NULL|TRUE|FALSE|-?\d+(?:\.\d+)?)", line)
            out.append([a if a or not b else b for a, b in vals])
        return pd.DataFrame(out, columns=cols)
    ref["product"] = rows("product")
    ref["product_group"] = rows("product_group")
    ref["line_of_business"] = rows("line_of_business")
    prov = rows("province")
    ref["province_name_short"] = dict(zip(prov["province_code"], prov["province_name"].str.replace(r"^(Thành phố|Tỉnh) ", "", regex=True)))
    comp = rows("company")
    ref["company_name"] = dict(zip(comp["company_code"], comp["company_name"]))
    return ref


# ===========================================================================
# 5. NẠP VÀO POSTGRESQL
# ===========================================================================
# Đích: mọi bảng ref.X / core.X của v2 → <SCHEMA>.<PREFIX>X ; view rpt.v_X / rpt.mv_X → <SCHEMA>.v_<PREFIX>X / mv_<PREFIX>X
SCHEMA = os.environ.get("TARGET_SCHEMA", "bronze")
PREFIX = os.environ.get("TABLE_PREFIX", "ins_")


def Q(sql: str) -> str:
    """Viết lại tên đối tượng của v2 sang schema/tiền tố đích."""
    sql = re.sub(r"^CREATE SCHEMA IF NOT EXISTS \w+;[ \t]*$", "", sql, flags=re.M)
    sql = re.sub(r"\b(?:ref|core)\.(\w+)", rf"{SCHEMA}.{PREFIX}\1", sql)
    sql = re.sub(r"\brpt\.(v|mv)_(\w+)", rf"{SCHEMA}.\1_{PREFIX}\2", sql)
    return re.sub(rf"\bix_(?!{PREFIX})", f"ix_{PREFIX}", sql)   # không đổi lại tên đã có tiền tố


class QCursor:
    """Cursor tự đổi tên đối tượng trong mọi câu lệnh."""
    def __init__(self, cur):
        self.cur = cur

    def execute(self, sql, params=None):
        return self.cur.execute(Q(sql), params)

    def copy(self, sql):
        return self.cur.copy(Q(sql))

    def fetchall(self):
        return self.cur.fetchall()

EXTRA_DDL = """
ALTER TABLE ref.customer ADD COLUMN IF NOT EXISTS gender char(1);
ALTER TABLE ref.customer ADD COLUMN IF NOT EXISTS birth_year smallint;
ALTER TABLE core.policy  ADD COLUMN IF NOT EXISTS prev_policy_no varchar(40);
COMMENT ON COLUMN ref.customer.gender IS 'Giới tính (M/F) — chỉ khách cá nhân, hộ gia đình';
COMMENT ON COLUMN ref.customer.birth_year IS 'Năm sinh — chỉ khách cá nhân, hộ gia đình';
COMMENT ON COLUMN core.policy.prev_policy_no IS 'Số hợp đồng năm trước được tái tục (hợp đồng ngoài kỳ dữ liệu nên lưu dạng text)';
"""

RPT_SQL = """
DROP MATERIALIZED VIEW IF EXISTS rpt.mv_revenue_daily, rpt.mv_txn_hourly;
DROP VIEW IF EXISTS rpt.v_revenue_line;

-- Doanh thu chi tiết: 1 dòng / dòng phí × đơn vị được phân bổ (chỉ chứng từ APPROVED)
CREATE VIEW rpt.v_revenue_line AS
SELECT t.accounting_date,
       t.txn_date,
       t.txn_id, t.txn_no, t.txn_type_code, tt.txn_type_name, tt.is_revenue_deduction, tt.gl_account,
       p.policy_id, p.policy_no, p.issuing_company_code, p.is_group_policy, p.currency_code,
       coalesce(p.channel_code, 'CHUA_XD') AS channel_code,
       coalesce(ch.channel_name, 'Chưa xác định') AS channel_name,
       coalesce(ch.report_channel_group, 'Chưa xác định') AS report_channel_group,
       coalesce(p.partner_code, CASE WHEN p.channel_code = 'DIEN_TU' THEN 'WEB_APP'
                                     WHEN p.channel_code IS NULL THEN 'CHUA_XD' ELSE 'KHONG_QUA_DT' END) AS partner_code,
       coalesce(pa.partner_name, CASE WHEN p.channel_code = 'DIEN_TU' THEN 'Website / ứng dụng của Tổng công ty'
                                      WHEN p.channel_code IS NULL THEN 'Chưa xác định' ELSE 'Không qua đối tác' END) AS partner_name,
       coalesce(pa.partner_type, CASE WHEN p.channel_code = 'DIEN_TU' THEN 'KENH_SO_CONG_TY'
                                      WHEN p.channel_code IS NULL THEN 'KHONG_XAC_DINH' ELSE 'KHONG_QUA_DOI_TAC' END) AS partner_type,
       c.product_code, pr.product_name, pr.is_compulsory,
       pg.product_group_code, pg.product_group_name,
       lob.lob_code, lob.lob_name, lob.poc_group_code, lob.poc_group_name,
       ra.company_code, co.company_name, co.company_type, ra.allocation_type_code,
       co_pv.province_code AS company_province_code, co_rg.region_name AS company_region_name,
       cu.customer_code, cu.segment_code, sg.segment_name, sg.is_organization, cu.is_aggregated_retail,
       cu.province_code AS customer_province_code, cu_pv.province_name AS customer_province_name,
       cu_rg.region_name AS customer_region_name,
       c.insured_count,
       c.premium_vnd                                                         AS gross_premium_100_vnd,
       cs.share_pct                                                          AS own_share_pct,
       ra.allocation_pct,
       round(c.premium_vnd * cs.share_pct / 100 * ra.allocation_pct / 100)  AS revenue_vnd,
       round(c.vat_vnd     * cs.share_pct / 100 * ra.allocation_pct / 100)  AS vat_vnd,
       round(c.premium_vnd * cs.share_pct / 100 * ra.allocation_pct / 100 * c.commission_rate_pct / 100) AS commission_vnd
FROM core.transaction_coverage c
JOIN core.policy_transaction t ON t.txn_id = c.txn_id AND t.status = 'APPROVED'
JOIN ref.transaction_type tt   ON tt.txn_type_code = t.txn_type_code
JOIN core.policy p             ON p.policy_id = t.policy_id
JOIN core.coinsurance_share cs ON cs.policy_id = p.policy_id AND cs.insurer_code = 'OWN'
JOIN core.revenue_allocation ra ON ra.policy_id = p.policy_id
JOIN ref.company co            ON co.company_code = ra.company_code
LEFT JOIN ref.province co_pv   ON co_pv.province_code = co.province_code
LEFT JOIN ref.region co_rg     ON co_rg.region_code = co_pv.region_code
JOIN ref.product pr            ON pr.product_code = c.product_code
JOIN ref.product_group pg      ON pg.product_group_code = pr.product_group_code
JOIN ref.line_of_business lob  ON lob.lob_code = pg.lob_code
LEFT JOIN ref.channel ch       ON ch.channel_code = p.channel_code
LEFT JOIN ref.partner pa       ON pa.partner_code = p.partner_code
JOIN ref.customer cu           ON cu.customer_code = p.customer_code
JOIN ref.customer_segment sg   ON sg.segment_code = cu.segment_code
LEFT JOIN ref.province cu_pv   ON cu_pv.province_code = cu.province_code
LEFT JOIN ref.region cu_rg     ON cu_rg.region_code = cu_pv.region_code;
COMMENT ON VIEW rpt.v_revenue_line IS 'Doanh thu chi tiết = phí 100% × tỷ lệ OWN × tỷ lệ phân bổ; chỉ chứng từ APPROVED; ngày ghi nhận = accounting_date. Lớp phân tích: kênh NULL → CHUA_XD, đối tác NULL → KHONG_QUA_DT / WEB_APP / CHUA_XD (bronze giữ NULL như nguồn)';

-- Tổng hợp doanh thu theo ngày ghi nhận × các chiều chính (nguồn cho dashboard)
CREATE MATERIALIZED VIEW rpt.mv_revenue_daily AS
SELECT accounting_date, company_code, channel_code, partner_code, product_code, segment_code,
       customer_region_name, txn_type_code,
       count(DISTINCT txn_id)          AS txn_count,
       sum(insured_count)              AS insured_count,
       sum(gross_premium_100_vnd)      AS gross_premium_100_vnd,
       sum(revenue_vnd)                AS revenue_vnd,
       sum(vat_vnd)                    AS vat_vnd,
       sum(commission_vnd)             AS commission_vnd
FROM rpt.v_revenue_line
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8;
CREATE INDEX ON rpt.mv_revenue_daily (accounting_date);
COMMENT ON MATERIALIZED VIEW rpt.mv_revenue_daily IS 'Doanh thu theo ngày ghi nhận × đơn vị × kênh × đối tác × sản phẩm × phân khúc × vùng khách × loại giao dịch. REFRESH MATERIALIZED VIEW sau khi nạp lại dữ liệu';

-- Vận hành: số giao dịch theo ngày chứng từ × giờ × kênh × trạng thái (mọi trạng thái)
CREATE MATERIALIZED VIEW rpt.mv_txn_hourly AS
SELECT t.txn_date, extract(hour FROM t.created_at)::int AS txn_hour,
       coalesce(p.channel_code, 'CHUA_XD') AS channel_code, p.issuing_company_code,
       t.txn_type_code, t.status, count(*) AS txn_count
FROM core.policy_transaction t
JOIN core.policy p ON p.policy_id = t.policy_id
GROUP BY 1, 2, 3, 4, 5, 6;
CREATE INDEX ON rpt.mv_txn_hourly (txn_date);
COMMENT ON MATERIALIZED VIEW rpt.mv_txn_hourly IS 'Số giao dịch theo ngày chứng từ × giờ × kênh × đơn vị cấp đơn × loại × trạng thái';
"""


def copy_df(cur, table, df, cols):
    out = df[cols].copy()
    for c in cols:
        s = out[c]
        if pd.api.types.is_bool_dtype(s):
            out[c] = np.where(s, "t", "f")
        elif pd.api.types.is_datetime64_any_dtype(s):
            out[c] = s.dt.strftime("%Y-%m-%d %H:%M:%S" if c == "created_at" else "%Y-%m-%d")
    step = 500_000
    with cur.copy(f"COPY {table} ({', '.join(cols)}) FROM STDIN") as cp:
        for i in range(0, len(out), step):
            cp.write(out.iloc[i:i + step].to_csv(sep="\t", header=False, index=False, na_rep="\\N", lineterminator="\n"))
    log(f"  {table}: {len(out):,} dòng")


FACT_TABLES_DELETE_ORDER = ["core.transaction_coverage", "core.policy_transaction", "core.coinsurance_share",
                            "core.revenue_allocation", "core.policy", "ref.customer"]


def drop_fk_idx(cur):
    """Bỏ khóa ngoại + index phụ của bảng fact (COPY / DELETE nhanh). Trả về định nghĩa để tạo lại."""
    cur.execute("""SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) FROM pg_constraint
                   WHERE contype = 'f' AND conrelid::regclass::text IN ('ref.customer', 'core.policy',
                         'core.policy_transaction', 'core.transaction_coverage', 'core.coinsurance_share',
                         'core.revenue_allocation')""")
    fks = cur.fetchall()
    for t, n, _ in fks:
        cur.execute(f'ALTER TABLE {t} DROP CONSTRAINT "{n}"')
    cur.execute("SELECT indexdef, schemaname || '.' || indexname FROM pg_indexes WHERE schemaname = %s AND indexname LIKE %s",
                (SCHEMA, f"ix_{PREFIX}%"))
    idx = cur.fetchall()
    for _, name in idx:
        cur.execute(f"DROP INDEX {name}")   # tên đã đủ schema
    return fks, idx


def existing_keys(cur):
    """Khóa lớn nhất đang có, đọc TRƯỚC khi xóa. Dữ liệu sinh lại không dùng lại policy_id / txn_id / coverage_id /
    số hợp đồng / mã khách đã xóa (CDC và Iceberg vẫn giữ lịch sử các khóa cũ). Làm tròn lên để chừa khoảng trống."""
    def one(sql):
        cur.execute(sql)
        return int(cur.fetchall()[0][0] or 0)
    up = lambda x, step: (x // step + 1) * step if x else 0
    keys = {"pid": up(one("SELECT max(policy_id) FROM core.policy"), 10_000_000),
            "tid": up(one("SELECT max(txn_id) FROM core.policy_transaction"), 10_000_000),
            "cid": up(one("SELECT max(coverage_id) FROM core.transaction_coverage"), 10_000_000),
            "cust_base": up(one("SELECT max(substr(customer_code, 3)::bigint) FROM ref.customer WHERE customer_code ~ '^KH[0-9]+$'"), 100_000_000)}
    cur.execute("SELECT split_part(policy_no, '-', 2) || '-' || split_part(policy_no, '-', 3), "
                "max(split_part(policy_no, '-', 4)::bigint) FROM core.policy GROUP BY 1")
    keys["seq"] = {k: int(up(v, 1_000_000)) for k, v in cur.fetchall()}
    log(f"Khóa bắt đầu sau dữ liệu cũ: policy_id > {keys['pid']:,} · txn_id > {keys['tid']:,} · coverage_id > {keys['cid']:,} "
        f"· mã khách từ KH{keys['cust_base']:09d} · số hợp đồng từ {min(keys['seq'].values(), default=0):,}")
    if keys["cust_base"] >= 900_000_000 or max(keys["seq"].values(), default=0) >= 9_000_000:
        sys.exit("Dải mã khách / số hợp đồng sắp hết chỗ — cần đổi định dạng mã trước khi sinh lại.")
    return keys


def prepare_replace(cur):
    """Giữ nguyên bảng / danh mục / publication CDC; DELETE toàn bộ dữ liệu fact + khách hàng rồi nạp lại.
    Mỗi DELETE là 1 transaction → CDC phát sự kiện xóa cho từng dòng."""
    cur.execute("""SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = %s AND c.relname = %s""", (SCHEMA, PREFIX + "policy"))
    if not cur.fetchall()[0][0]:
        sys.exit(f"Chưa có {SCHEMA}.{PREFIX}policy — dùng --reset cho lần nạp đầu.")
    # danh mục bổ sung còn thiếu (đối tác, tỷ giá) — không đụng dòng đã có
    for r in EXTRA_PARTNERS:
        cur.execute("INSERT INTO ref.partner (partner_code, partner_name, partner_type, channel_code) VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (partner_code) DO NOTHING", r)
    cur.execute("INSERT INTO ref.fx_rate VALUES " + ", ".join(
        f"('USD', '{y}-{m:02d}-01', {v}, '{FX_NOTE_2026}')" for (y, m), v in sorted(FX_YM.items()))
        + " ON CONFLICT (currency_code, rate_month) DO NOTHING")
    fks, idx = drop_fk_idx(cur)
    for t in FACT_TABLES_DELETE_ORDER:
        t0 = time.time()
        cur.execute(f"DELETE FROM {t}")
        log(f"  DELETE {t}: {time.time() - t0:,.0f}s")
    return fks, idx


def prepare(cur, reset: bool):
    """Tạo schema + danh mục; bỏ khóa ngoại / index phụ để COPY nhanh. Trả về định nghĩa để tạo lại."""
    cur.execute("CREATE SCHEMA IF NOT EXISTS " + SCHEMA)
    cur.execute("""SELECT c.relname, c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = %s AND c.relkind IN ('r', 'p', 'v', 'm')
                     AND (c.relname LIKE %s OR c.relname LIKE %s OR c.relname LIKE %s)""",
                (SCHEMA, PREFIX + "%", "v_" + PREFIX + "%", "mv_" + PREFIX + "%"))
    existing = cur.fetchall()
    if existing and not reset:
        sys.exit(f"{SCHEMA} đã có {len(existing)} đối tượng {PREFIX}* của POC. Chạy lại với --reset để xóa và nạp mới.")
    kind = {"m": "MATERIALIZED VIEW", "v": "VIEW", "r": "TABLE", "p": "TABLE"}
    for k in ("m", "v", "r", "p"):       # chỉ xóa đúng các đối tượng có tiền tố của POC, không đụng bảng khác
        for name, rk in existing:
            if rk == k:
                cur.execute(f'DROP {kind[k]} IF EXISTS {SCHEMA}."{name}" CASCADE')
    log(f"Tạo bảng {SCHEMA}.{PREFIX}* + danh mục …")
    cur.execute((V2 / "01_ddl.sql").read_text(encoding="utf-8"))
    cur.execute((V2 / "01b_column_comments.sql").read_text(encoding="utf-8"))
    cur.execute(EXTRA_DDL)
    for sql in v2_ref_sql():
        cur.execute(sql)
    for r in EXTRA_PARTNERS:
        cur.execute("INSERT INTO ref.partner (partner_code, partner_name, partner_type, channel_code) VALUES (%s, %s, %s, %s)", r)
    cur.execute("INSERT INTO ref.fx_rate VALUES " + ", ".join(
        f"('USD', '{y}-{m:02d}-01', {v}, '{FX_NOTE_2026}')" for (y, m), v in sorted(FX_YM.items())))
    return drop_fk_idx(cur)


def load_chunk(cur, g: Gen):
    c = g.customers.copy()
    c["birth_year"] = c["birth_year"].astype("Int64")
    copy_df(cur, "ref.customer", c, ["customer_code", "customer_name", "segment_code", "tax_code", "province_code",
                                     "home_company_code", "is_aggregated_retail", "created_date", "gender", "birth_year"])
    p = g.pol.rename(columns={"is_group": "is_group_policy"}).assign(renewal_of_policy_id=None)
    copy_df(cur, "core.policy", p, ["policy_id", "policy_no", "issuing_company_code", "customer_code", "channel_code",
                                    "partner_code", "currency_code", "issue_date", "effective_date", "expiry_date",
                                    "is_group_policy", "renewal_of_policy_id", "prev_policy_no"])
    copy_df(cur, "core.policy_transaction", g.tx, ["txn_id", "policy_id", "txn_no", "txn_type_code", "txn_date",
                                                   "accounting_date", "status", "fx_rate", "created_by", "created_at"])
    cov = g.cov.assign(premium_rate_pct=g.cov["premium_rate_pct"].round(6))
    copy_df(cur, "core.transaction_coverage", cov, ["coverage_id", "txn_id", "product_code", "sum_insured",
                                                    "premium_rate_pct", "insured_count", "premium_orig",
                                                    "premium_vnd", "vat_vnd", "commission_rate_pct"])
    copy_df(cur, "core.coinsurance_share", g.coins, ["policy_id", "insurer_code", "role", "share_pct"])
    copy_df(cur, "core.revenue_allocation", g.alloc, ["policy_id", "company_code", "allocation_type_code", "allocation_pct"])


def finalize(cur, fks, idx):
    log("Tạo lại khóa ngoại, index …")
    for t, n, d in fks:
        cur.execute(f'ALTER TABLE {t} ADD CONSTRAINT "{n}" {d}')
    for d, _ in idx:
        cur.execute(d)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_policy_customer ON core.policy (customer_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_policy_issue_date ON core.policy (issue_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_policy_transaction_txn_date ON core.policy_transaction (txn_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_revenue_allocation_company ON core.revenue_allocation (company_code)")
    log("ANALYZE …")
    cur.execute("ANALYZE")
    log("Tạo schema rpt (view + materialized view) …")
    cur.execute(RPT_SQL)
    cur.execute("ANALYZE rpt.mv_revenue_daily; ANALYZE rpt.mv_txn_hourly")
    verify(cur)


def verify(cur):
    log("Kiểm tra sau khi nạp:")
    checks = {
        "Giao dịch/ngày (min, max, số ngày)":
            "SELECT min(n), max(n), count(*) FROM (SELECT txn_date, count(*) n FROM core.policy_transaction GROUP BY 1) x",
        "Đồng BH tổng ≠ 100%":
            "SELECT count(*) FROM (SELECT policy_id FROM core.coinsurance_share GROUP BY 1 HAVING sum(share_pct) <> 100) x",
        "Phân bổ tổng ≠ 100%":
            "SELECT count(*) FROM (SELECT policy_id FROM core.revenue_allocation GROUP BY 1 HAVING sum(allocation_pct) <> 100) x",
        "Hoa hồng vượt trần":
            "SELECT count(*) FROM core.transaction_coverage c JOIN ref.product p USING (product_code) WHERE c.commission_rate_pct > p.max_commission_pct",
        "Hợp đồng không có giao dịch":
            "SELECT count(*) FROM core.policy p WHERE NOT EXISTS (SELECT 1 FROM core.policy_transaction t WHERE t.policy_id = p.policy_id)",
        "Doanh thu theo nhóm POC (tỷ)":
            "SELECT poc_group_name, round(sum(revenue_vnd) / 1e9) FROM rpt.mv_revenue_daily m JOIN ref.product USING (product_code) "
            "JOIN ref.product_group USING (product_group_code) JOIN ref.line_of_business USING (lob_code) GROUP BY 1 ORDER BY 2 DESC",
    }
    for k, q in checks.items():
        cur.execute(q)
        print(f"    {k}: {cur.fetchall()}")


# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pg-uri", default=os.environ.get("PG_URI"), help="postgresql://user:pass@host:port/db (hoặc biến PG_URI)")
    ap.add_argument("--local", action="store_true", help="nạp vào PostgreSQL nhúng (pgserver) để chạy thử")
    ap.add_argument("--days", type=int, help="chỉ sinh N ngày đầu (chạy thử)")
    ap.add_argument("--reset", action="store_true", help="xóa schema ref/core/rpt cũ của POC trước khi nạp")
    ap.add_argument("--replace", action="store_true",
                    help="giữ bảng + publication CDC; DELETE dữ liệu fact/khách hàng rồi nạp lại (CDC thấy sự kiện xóa + thêm)")
    ap.add_argument("--dry-run", action="store_true", help="chỉ sinh và in thống kê")
    ap.add_argument("--chunk-days", type=int, default=10, help="số ngày sinh + nạp mỗi đợt (giới hạn RAM)")
    a = ap.parse_args()
    last = START + dt.timedelta(a.days - 1) if a.days else END
    t0 = time.time()
    uri = a.pg_uri
    if a.local:
        import pgserver
        uri = pgserver.get_server(HERE / ".pgdata").get_uri()
    if not a.dry_run and not uri:
        sys.exit("Thiếu --pg-uri / PG_URI (hoặc dùng --local / --dry-run)")

    import psycopg
    conn = None if a.dry_run else psycopg.connect(uri, autocommit=True)
    cur = QCursor(conn.cursor()) if conn else None
    keys = existing_keys(cur) if (a.replace and cur) else {}
    fks, idx = (prepare_replace(cur) if a.replace else prepare(cur, a.reset)) if cur else ([], [])
    ref = load_v2_ref()
    state = {"pid": 0, "tid": 0, "cid": 0, "seq": {}, "seen": set(), "cust_base": 0}
    state.update(keys)
    d = START
    while d <= last:
        e = min(d + dt.timedelta(a.chunk_days - 1), last)
        log(f"=== Đợt {d:%d/%m} – {e:%d/%m} ===")
        g = Gen(d, e, state, ref).run()
        g.stats()
        if cur:
            load_chunk(cur, g)
        del g
        d = e + dt.timedelta(1)
    if cur:
        finalize(cur, fks, idx)
        conn.close()
    log(f"Hoàn tất sau {time.time() - t0:,.0f}s")


if __name__ == "__main__":
    main()
