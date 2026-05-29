"""
BaZi (Four Pillars) calculation engine — pure domain logic.

Depends only on ``lunar_python`` and Python standard library.
Zero imports from Flask, SQLite, Stripe, Claude, or any web framework.
"""

import json
import sys
from datetime import datetime

from lunar_python import Solar, EightChar


# ── Heavenly Stems (天干) ────────────────────────────────────────────────

TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
TIAN_GAN_EN = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
TIAN_GAN_WU_XING = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]
TIAN_GAN_WU_XING_EN = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]

# ── Earthly Branches (地支) ──────────────────────────────────────────────

DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
DI_ZHI_EN = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
DI_ZHI_WU_XING = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]
DI_ZHI_WU_XING_EN = ["Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"]

# ── Ten Gods (十神) ──────────────────────────────────────────────────────

SHI_SHEN_MAP = {
    "比肩": "Bi Jian (Peer)", "劫财": "Jie Cai (Rob Wealth)",
    "食神": "Shi Shen (Food God)", "伤官": "Shang Guan (Hurt Official)",
    "偏财": "Pian Cai (Indirect Wealth)", "正财": "Zheng Cai (Direct Wealth)",
    "偏印": "Pian Yin (Indirect Resource)", "正印": "Zheng Yin (Direct Resource)",
    "七杀": "Qi Sha (Seven Kill)", "正官": "Zheng Guan (Direct Officer)",
}

# ── Five Element Colors (for report display) ─────────────────────────────

WU_XING_COLORS = {
    "木": "#4CAF50", "Wood": "#4CAF50",
    "火": "#FF5722", "Fire": "#FF5722",
    "土": "#FFC107", "Earth": "#FFC107",
    "金": "#9E9E9E", "Metal": "#9E9E9E",
    "水": "#2196F3", "Water": "#2196F3",
}


# ── Gender resolution ────────────────────────────────────────────────────

def resolve_gender_code(gender) -> int:
    """Return numeric gender code: 0=male, 1=female."""
    if isinstance(gender, str):
        g = gender.lower()
        if g in ("m", "male", "男", "0"):
            return 0
        return 1
    return 0 if gender == 0 else 1


# ── Main calculation ─────────────────────────────────────────────────────

def calc_bazi(year, month, day, hour, minute=0, gender="male"):
    """
    Calculate a complete BaZi (Four Pillars) chart.

    Args:
        year, month, day, hour, minute: Birth date/time components.
        hour is 24-hour format.
        gender: "male"/"female" or "男"/"女".

    Returns:
        dict: Complete BaZi chart data (dict for backward compatibility).
    """
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    e8 = EightChar.fromLunar(lunar)
    gender_code = resolve_gender_code(gender)

    def _index_in_list(item, lst):
        try:
            return lst.index(item)
        except ValueError:
            return -1

    # ── Four Pillars ────────────────────────────────────────────────────
    pillars = {}
    for pname, p_getters in [
        ("year", (e8.getYearGan, e8.getYearZhi, e8.getYearWuXing, e8.getYearNaYin,
                  e8.getYearHideGan, e8.getYearShiShenGan, e8.getYearShiShenZhi,
                  e8.getYearDiShi, e8.getYearXunKong)),
        ("month", (e8.getMonthGan, e8.getMonthZhi, e8.getMonthWuXing, e8.getMonthNaYin,
                   e8.getMonthHideGan, e8.getMonthShiShenGan, e8.getMonthShiShenZhi,
                   e8.getMonthDiShi, e8.getMonthXunKong)),
        ("day", (e8.getDayGan, e8.getDayZhi, e8.getDayWuXing, e8.getDayNaYin,
                 e8.getDayHideGan, e8.getDayShiShenGan, e8.getDayShiShenZhi,
                 e8.getDayDiShi, e8.getDayXunKong)),
        ("time", (e8.getTimeGan, e8.getTimeZhi, e8.getTimeWuXing, e8.getTimeNaYin,
                  e8.getTimeHideGan, e8.getTimeShiShenGan, e8.getTimeShiShenZhi,
                  e8.getTimeDiShi, e8.getTimeXunKong)),
    ]:
        gan, zhi = p_getters[0](), p_getters[1]()
        pillars[pname] = {
            "gan": gan, "zhi": zhi,
            "gan_index": _index_in_list(gan, TIAN_GAN),
            "zhi_index": _index_in_list(zhi, DI_ZHI),
            "wuxing": p_getters[2](), "nayin": p_getters[3](),
            "hidden_gan": p_getters[4](),
            "shi_shen_gan": p_getters[5](),
            "shi_shen_zhi": p_getters[6](),
            "di_shi": p_getters[7](),
            "xun_kong": p_getters[8](),
        }

    # ── Day Master ──────────────────────────────────────────────────────
    day_master = {
        "gan": e8.getDayGan(),
        "gan_index": e8.getDayGanIndex(),
        "wuxing": e8.getDayWuXing(),
        "shi_shen": {
            "year_gan": pillars["year"]["shi_shen_gan"],
            "month_gan": pillars["month"]["shi_shen_gan"],
            "time_gan": pillars["time"]["shi_shen_gan"],
            "year_zhi": pillars["year"]["shi_shen_zhi"],
            "month_zhi": pillars["month"]["shi_shen_zhi"],
            "day_zhi": pillars["day"]["shi_shen_zhi"],
            "time_zhi": pillars["time"]["shi_shen_zhi"],
        },
    }

    # ── Wu Xing (Five Element) count ────────────────────────────────────
    wuxing_count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for pillar in ("year", "month", "day", "time"):
        wx = pillars[pillar]["wuxing"]
        for ch in wx:
            if ch in wuxing_count:
                wuxing_count[ch] += 1
        for hg in pillars[pillar]["hidden_gan"]:
            idx = TIAN_GAN.index(hg) if hg in TIAN_GAN else -1
            if idx >= 0:
                wx_hg = TIAN_GAN_WU_XING[idx]
                wuxing_count[wx_hg] = wuxing_count.get(wx_hg, 0) + 0.5

    dm_wx = day_master["wuxing"]
    wuxing_analysis = _analyze_wuxing(wuxing_count, dm_wx)

    # ── Da Yun (Decade Cycles) ──────────────────────────────────────────
    yun = e8.getYun(gender_code)
    da_yun_list = []
    if yun:
        da_yun = yun.getDaYun()
        for dy in da_yun:
            gz = dy.getGanZhi()
            if not gz:
                continue
            sa, ea = dy.getStartAge(), dy.getEndAge()
            da_yun_list.append({
                "gan_zhi": gz,
                "start_age": sa,
                "end_age": ea,
                "years": ea - sa,
            })

    # ── Extra info ──────────────────────────────────────────────────────
    extra = {
        "tai_yuan": e8.getTaiYuan(),
        "tai_yuan_nayin": e8.getTaiYuanNaYin(),
        "ming_gong": e8.getMingGong(),
        "ming_gong_nayin": e8.getMingGongNaYin(),
        "shen_gong": e8.getShenGong(),
        "shen_gong_nayin": e8.getShenGongNaYin(),
        "zodiac": lunar.getYearShengXiao() if hasattr(lunar, 'getYearShengXiao') else "",
    }

    # ── Liu Nian (Current year forecast) ────────────────────────────────
    current_year = datetime.now().year
    liu_nian = calc_liu_nian(da_yun_list, current_year, year)

    return {
        "birth_date": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        "lunar_date": lunar.toFullString(),
        "gender": "Male" if gender_code == 0 else "Female",
        "day_master": day_master,
        "four_pillars": pillars,
        "wuxing": {
            "count": wuxing_count,
            "analysis": wuxing_analysis,
        },
        "da_yun": {
            "start_age": yun.getStartYear() if yun else None,
            "forward": yun.isForward() if yun else None,
            "cycles": da_yun_list,
        },
        "liu_nian": liu_nian,
        "extra": extra,
    }


# ── Wu Xing analysis ─────────────────────────────────────────────────────

def _analyze_wuxing(count, dm_wx):
    """Analyze Five Element balance and strength."""
    total = sum(count.values()) or 1
    percentages = {k: round(v / total * 100, 1) for k, v in count.items()}
    sorted_wx = sorted(count.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_wx[0][0] if sorted_wx else ""
    weakest = sorted_wx[-1][0] if sorted_wx else ""

    dm_count = count.get(dm_wx, 0)
    is_strong = sorted_wx.index((dm_wx, dm_count)) < 2 if dm_wx in dict(sorted_wx) else False

    return {
        "percentages": percentages,
        "strongest": strongest,
        "weakest": weakest,
        "day_master_strength": "Strong" if is_strong else "Weak",
        "balance_advice": get_balance_advice(strongest, weakest, dm_wx),
    }


# ── Liu Nian (current year) ──────────────────────────────────────────────

def calc_liu_nian(da_yun_cycles, current_year, birth_year):
    """Calculate the current year's Liu Nian (流年) forecast."""
    gan_zhi_list = [
        "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未","壬申","癸酉",
        "甲戌","乙亥","丙子","丁丑","戊寅","己卯","庚辰","辛巳","壬午","癸未",
        "甲申","乙酉","丙戌","丁亥","戊子","己丑","庚寅","辛卯","壬辰","癸巳",
        "甲午","乙未","丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
        "甲辰","乙巳","丙午","丁未","戊申","己酉","庚戌","辛亥","壬子","癸丑",
        "甲寅","乙卯","丙辰","丁巳","戊午","己未","庚申","辛酉","壬戌","癸亥",
    ]

    offset = (current_year - 4) % 60
    current_gz = gan_zhi_list[offset]

    age = current_year - birth_year
    current_da_yun = None
    for cycle in da_yun_cycles:
        if cycle["start_age"] <= age <= cycle["end_age"]:
            current_da_yun = cycle
            break

    return {
        "year": current_year,
        "gan_zhi": current_gz,
        "current_da_yun": current_da_yun,
    }


# ── Balance advice ──────────────────────────────────────────────────────

def get_balance_advice(strongest, weakest, dm_wx):
    """Generate Five Element balance advice."""
    advice = {
        "木": "Wood energy needs nurturing. Engage in creative activities, spend time in nature.",
        "火": "Fire energy needs balancing. Practice meditation, avoid overstimulation.",
        "土": "Earth energy needs grounding. Focus on stability, routine, and practical matters.",
        "金": "Metal energy needs refinement. Declutter your space, practice letting go.",
        "水": "Water energy needs flow. Embrace flexibility, go with the flow, rest adequately.",
    }
    return {
        "strongest": f"Strong {strongest} influence. {advice.get(strongest, '')}",
        "weakest": f"Weak {weakest} influence. {advice.get(weakest, '')}",
    }


# ── Serialization helper ────────────────────────────────────────────────

def to_json(bazi_result, indent=2):
    """Serialize BaZi chart to JSON."""
    return json.dumps(bazi_result, ensure_ascii=False, indent=indent)


# ── CLI entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 4:
        y, m, d, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
        g = args[4] if len(args) > 4 else "male"
        result = calc_bazi(y, m, d, h, gender=g)
        print(to_json(result))
    else:
        result = calc_bazi(1990, 5, 15, 12, gender="male")
        print(to_json(result))
