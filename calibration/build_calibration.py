"""
Tạo calibration.json — tham số có căn cứ cho gen_volume.py, rút từ nguồn công khai.
Chỉ lưu THỐNG KÊ tổng hợp (phân vị, tỷ lệ), không lưu dữ liệu gốc.

    python -I build_calibration.py <travel_insurance.csv> <hotels.csv> <out.json>

Nguồn:
  [DATASET] Travel Insurance (~63k hợp đồng bán qua đại lý/hãng bay): Agency Type, Distribution Channel,
            Duration (ngày), Net Sales, Commision (in value). Bản sao: github.com/sohamthirty/Claim-Prediction (Data/travel_insurance.csv)
  [NGUỒN THAY THẾ] Hotel booking demand datasets — Antonio, Almeida & Nunes, Data in Brief 22 (2019)
            doi:10.1016/j.dib.2018.11.126; bản CSV: TidyTuesday 2020-02-11 (hotels.csv). Dùng lead_time (số ngày đặt trước)
            và số đêm lưu trú; khách nội địa = country 'PRT', quốc tế = còn lại.
  [CHÍNH THỨC] Bản tin thị trường bảo hiểm — Bộ Tài chính: doanh thu phí gốc phi nhân thọ lũy kế 2025
            7T 50.784 · 8T 56.376 · 9T 64.378 tỷ đồng (bản tin tháng 8, 9, 10/2025).
"""
import csv
import json
import sys
from statistics import median

QS = [i / 100 for i in range(101)]


def quantiles(vals):
    v = sorted(vals)
    n = len(v)
    return [v[min(n - 1, int(round(q * (n - 1))))] for q in QS]


def main(travel_csv, hotel_csv, out_json):
    # ---- Travel Insurance
    dur, comm, ag, ch, n = [], [], {}, {}, 0
    with open(travel_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n += 1
            try:
                d = int(r["Duration"])
                ns = float(r["Net Sales"])
                cm = float(r["Commision (in value)"])
            except (ValueError, KeyError):
                continue
            if 1 <= d <= 365:                       # loại giá trị lỗi (âm, >365 ngày)
                dur.append(d)
            if ns > 0:
                comm.append(cm / ns)
            key = (r["Agency Type"], r["Distribution Channel"])
            ag[key] = ag.get(key, 0) + 1
    tot = sum(ag.values())
    travel = {
        "rows": n,
        "duration_days_q": quantiles(dur),
        "duration_kept": len(dur),
        "commission_ratio_q": [round(x, 4) for x in quantiles(comm)],
        "commission_zero_share": round(sum(1 for x in comm if x == 0) / len(comm), 4),
        "agency_channel_share": {f"{a}|{c}": round(k / tot, 4) for (a, c), k in sorted(ag.items())},
    }

    # ---- Hotel booking demand
    lt = {"dom": [], "intl": []}
    nights = {"dom": [], "intl": []}
    canc = {"dom": [0, 0], "intl": [0, 0]}
    with open(hotel_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            g = "dom" if r["country"] == "PRT" else "intl"
            try:
                lt[g].append(int(r["lead_time"]))
                ng = int(r["stays_in_weekend_nights"]) + int(r["stays_in_week_nights"])
            except ValueError:
                continue
            if ng > 0:
                nights[g].append(ng)
            canc[g][0] += int(r["is_canceled"] == "1")
            canc[g][1] += 1
    hotel = {g: {"bookings": len(lt[g]), "lead_time_days_q": quantiles(lt[g]), "lead_time_median": median(lt[g]),
                 "trip_days_q": [x + 1 for x in quantiles(nights[g])],     # số ngày chuyến đi = số đêm + 1
                 "cancel_rate": round(canc[g][0] / canc[g][1], 4)} for g in lt}

    # ---- Bộ Tài chính: phí gốc phi nhân thọ 2025 (tỷ đồng)
    cum = {"2025-07": 50784, "2025-08": 56376, "2025-09": 64378}
    aug, sep = cum["2025-08"] - cum["2025-07"], cum["2025-09"] - cum["2025-08"]
    mof = {"cumulative_2025_bn_vnd": cum, "aug_2025": aug, "sep_2025": sep,
           "sep_vs_aug_per_day": round((sep / 30) / (aug / 31), 4),
           "note": "Số lũy kế là số ước tính tại thời điểm bản tin; chênh lệch tháng có thể gồm điều chỉnh số liệu."}

    out = {"sources": __doc__.split("Nguồn:")[1].strip(), "travel_insurance": travel, "hotel_booking": hotel, "mof_nonlife_2025": mof}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    s = lambda q: f"p10={q[10]} p25={q[25]} p50={q[50]} p75={q[75]} p90={q[90]} p99={q[99]} max={q[100]}"
    print("Travel rows", n, "| duration kept", len(dur), "|", s(travel["duration_days_q"]))
    print("  commission ratio:", s(travel["commission_ratio_q"]), "| zero share", travel["commission_zero_share"])
    print("  agency×channel:", travel["agency_channel_share"])
    for g in hotel:
        print(f"Hotel {g}: bookings {hotel[g]['bookings']} | lead {s(hotel[g]['lead_time_days_q'])} | trip days {s(hotel[g]['trip_days_q'])} | cancel {hotel[g]['cancel_rate']}")
    print("MOF:", mof)


if __name__ == "__main__":
    main(*sys.argv[1:4])
