"""
Qimen Dunjia (奇门遁甲) calculation engine — pure domain logic.

Depends only on ``lunar_python`` and Python standard library.
Zero imports from Flask, SQLite, Stripe, Claude, or any web framework.
"""

import sys
from datetime import datetime

from lunar_python import Solar, Lunar, EightChar


# ── Nine Palaces (九宫) — Luo Shu magic square ──────────────────────

# Palace number → (name, direction, wuxing)
PALACE_INFO = {
    1: {"name": "坎", "direction": "北", "wuxing": "水", "english": "Kan"},
    2: {"name": "坤", "direction": "西南", "wuxing": "土", "english": "Kun"},
    3: {"name": "震", "direction": "东", "wuxing": "木", "english": "Zhen"},
    4: {"name": "巽", "direction": "东南", "wuxing": "木", "english": "Xun"},
    5: {"name": "中", "direction": "中央", "wuxing": "土", "english": "Center"},
    6: {"name": "乾", "direction": "西北", "wuxing": "金", "english": "Qian"},
    7: {"name": "兑", "direction": "西", "wuxing": "金", "english": "Dui"},
    8: {"name": "艮", "direction": "东北", "wuxing": "土", "english": "Gen"},
    9: {"name": "离", "direction": "南", "wuxing": "火", "english": "Li"},
}

# Luo Shu grid (row-major: 4 9 2 / 3 5 7 / 8 1 6)
LUO_SHU = [4, 9, 2, 3, 5, 7, 8, 1, 6]

# ── Heavenly Stems (天干) ────────────────────────────────────────────

TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
TIAN_GAN_EN = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]

# Six Rituals (六仪) + Three Wonders (三奇) — the 9 stems used in Qimen earth level
SIX_YI_THREE_QI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
# 六仪: 戊己庚辛壬癸, 三奇: 乙丙丁

# Earthly Branches (地支)
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# ── 60 Jiazi cycle ──────────────────────────────────────────────────

GAN_ZHI_60 = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

# 旬首 mapping: (旬首_ganzhi, leader_stem)
XUN_SHOU_MAP = {
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
}

# ── Eight Doors (八门) — 休生伤杜景死惊开 ─────────────────────────

DOORS = [
    {"name": "休", "english": "Rest",    "palace": 1, "wuxing": "水", "good": True,
     "meaning": "Good for rest, healing, negotiation, and romance."},
    {"name": "生", "english": "Life",    "palace": 8, "wuxing": "土", "good": True,
     "meaning": "Good for business, new ventures, wealth, and growth."},
    {"name": "伤", "english": "Harm",    "palace": 3, "wuxing": "木", "good": False,
     "meaning": "Brings injury, conflict, loss, and competition."},
    {"name": "杜", "english": "Block",   "palace": 4, "wuxing": "木", "good": False,
     "meaning": "Obstruction, blocked progress, secrecy."},
    {"name": "景", "english": "Scene",   "palace": 9, "wuxing": "火", "good": True,
     "meaning": "Good for recognition, exams, visibility, and fame."},
    {"name": "死", "english": "Death",   "palace": 2, "wuxing": "土", "good": False,
     "meaning": "Loss, endings, danger, and stagnation."},
    {"name": "惊", "english": "Surprise","palace": 7, "wuxing": "金", "good": False,
     "meaning": "Shock, fear, unexpected events, and arguments."},
    {"name": "开", "english": "Open",    "palace": 6, "wuxing": "金", "good": True,
     "meaning": "Good for travel, starting new things, openness, and justice."},
]

DOOR_BY_PALACE = {d["palace"]: d for d in DOORS}

# ── Nine Stars (九星) ───────────────────────────────────────────────

STARS = [
    {"name": "天蓬", "english": "Heavenly Rapana", "palace": 1, "wuxing": "水", "good": False,
     "meaning": "Cautious — hidden danger, but can be auspicious for water-related activities."},
    {"name": "天芮", "english": "Heavenly Ru",     "palace": 2, "wuxing": "土", "good": False,
     "meaning": "Illness — education and discipleship, but also sickness and weakness."},
    {"name": "天冲", "english": "Heavenly Rush",   "palace": 3, "wuxing": "木", "good": False,
     "meaning": "Impulsive — quick action, military, and breakthroughs."},
    {"name": "天辅", "english": "Heavenly Assist",  "palace": 4, "wuxing": "木", "good": True,
     "meaning": "Support — education, culture, mentorship, and harmony."},
    {"name": "天禽", "english": "Heavenly Bird",    "palace": 5, "wuxing": "土", "good": True,
     "meaning": "Center — noble, balanced, and universally auspicious."},
    {"name": "天心", "english": "Heavenly Heart",   "palace": 6, "wuxing": "金", "good": True,
     "meaning": "Healing — strategy, medicine, wisdom, and leadership."},
    {"name": "天柱", "english": "Heavenly Pillar",  "palace": 7, "wuxing": "金", "good": False,
     "meaning": "Collapse — destruction, arguments, and breakdowns."},
    {"name": "天任", "english": "Heavenly Duty",    "palace": 8, "wuxing": "土", "good": True,
     "meaning": "Stability — responsibility, agriculture, and steady progress."},
    {"name": "天英", "english": "Heavenly Hero",    "palace": 9, "wuxing": "火", "good": False,
     "meaning": "Splendor — vanity, fire danger, and dramatic displays."},
]

STAR_BY_PALACE = {s["palace"]: s for s in STARS}

# ── Eight Gods (八神) ───────────────────────────────────────────────

GODS = [
    {"name": "值符", "english": "Direct Fu",     "good": True,
     "meaning": "Noble — protective, leadership, and divine guidance."},
    {"name": "腾蛇", "english": "Soaring Snake",  "good": False,
     "meaning": "Deception — suspicion, nightmares, and intrigue."},
    {"name": "太阴", "english": "Great Yin",      "good": True,
     "meaning": "Secrecy — strategy, hidden help, and private matters."},
    {"name": "六合", "english": "Six Harmonies",  "good": True,
     "meaning": "Harmony — marriage, partnership, and cooperation."},
    {"name": "白虎", "english": "White Tiger",    "good": False,
     "meaning": "Violence — authority, obstacles, and sudden misfortune."},
    {"name": "玄武", "english": "Dark Warrior",   "good": False,
     "meaning": "Theft — deception, hidden intentions, and loss."},
    {"name": "九地", "english": "Nine Earth",     "good": True,
     "meaning": "Stability — accumulation, patience, and solid foundation."},
    {"name": "九天", "english": "Nine Heaven",    "good": True,
     "meaning": "Expansion — high achievement, success, and breakthroughs."},
]

# ── 24 Solar Terms → Ju number lookup ───────────────────────────────

SOLAR_TERM_JU = {
    # 阳遁 (Winter Solstice → Summer Solstice)
    "冬至": {"type": "yang", "ju_list": [1, 7, 4]},
    "小寒": {"type": "yang", "ju_list": [2, 8, 5]},
    "大寒": {"type": "yang", "ju_list": [3, 9, 6]},
    "立春": {"type": "yang", "ju_list": [8, 5, 2]},
    "雨水": {"type": "yang", "ju_list": [9, 6, 3]},
    "惊蛰": {"type": "yang", "ju_list": [1, 7, 4]},
    "春分": {"type": "yang", "ju_list": [3, 9, 6]},
    "清明": {"type": "yang", "ju_list": [4, 1, 7]},
    "谷雨": {"type": "yang", "ju_list": [5, 2, 8]},
    "立夏": {"type": "yang", "ju_list": [4, 1, 7]},
    "小满": {"type": "yang", "ju_list": [5, 2, 8]},
    "芒种": {"type": "yang", "ju_list": [6, 3, 9]},
    # 阴遁 (Summer Solstice → Winter Solstice)
    "夏至": {"type": "yin", "ju_list": [9, 3, 6]},
    "小暑": {"type": "yin", "ju_list": [8, 2, 5]},
    "大暑": {"type": "yin", "ju_list": [7, 1, 4]},
    "立秋": {"type": "yin", "ju_list": [2, 5, 8]},
    "处暑": {"type": "yin", "ju_list": [1, 4, 7]},
    "白露": {"type": "yin", "ju_list": [9, 3, 6]},
    "秋分": {"type": "yin", "ju_list": [7, 1, 4]},
    "寒露": {"type": "yin", "ju_list": [6, 9, 3]},
    "霜降": {"type": "yin", "ju_list": [5, 8, 2]},
    "立冬": {"type": "yin", "ju_list": [6, 9, 3]},
    "小雪": {"type": "yin", "ju_list": [5, 8, 2]},
    "大雪": {"type": "yin", "ju_list": [4, 7, 1]},
}

# Jie (节) solar terms — the 12 that can be 符头 (energy leaders)
JIE_TERMS = {"立春", "惊蛰", "清明", "立夏", "芒种",
             "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"}


# ═══════════════════════════════════════════════════════════════════
#  Core calculation
# ═══════════════════════════════════════════════════════════════════

def _resolve_solar_info(year: int, month: int, day: int, hour: int, minute: int):
    """Get solar/lunar data via lunar_python and return relevant fields."""
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    e8 = EightChar.fromLunar(lunar)

    # Solar term info
    prev_jie = lunar.getPrevJie()
    prev_qi = lunar.getPrevQi()
    current_jie_term = prev_jie.getName() if prev_jie else ""
    current_qi_term = prev_qi.getName() if prev_qi else ""

    # Which solar term should we use for Qimen? Use the Jie (节)
    # If the current day is past a Jie, that Jie governs
    # The current JieQi period is from the last Jie to the next Jie
    # But we need the Jie that's currently active
    # In Qimen, between 冬至 and 夏至 it's 阳遁, between 夏至 and 冬至 it's 阴遁

    # Use prev_jie for the 节气 period
    jie_name = current_jie_term

    # Day ganzhi info
    day_gz_str = lunar.getDayInGanZhi()  # e.g. "甲子"
    day_gz_index = GAN_ZHI_60.index(day_gz_str) if day_gz_str in GAN_ZHI_60 else -1

    # Hour ganzhi via EightChar
    hours_since_23 = (hour + 1) % 24  # 23=子时 start
    hour_zhi_index = hours_since_23 // 2
    hour_gan = ""
    hour_zhi = DI_ZHI[hour_zhi_index] if 0 <= hour_zhi_index < 12 else ""
    # Use EightChar to get time ganzhi
    try:
        hour_gan = e8.getTimeGan()
        hour_zhi = e8.getTimeZhi()
    except Exception:
        pass

    hour_gz = hour_gan + hour_zhi if hour_gan and hour_zhi else ""

    return {
        "solar": solar,
        "lunar": lunar,
        "prev_jie": current_jie_term,
        "prev_qi": current_qi_term,
        "day_gz": day_gz_str,
        "day_gz_index": day_gz_index,
        "hour_gan": hour_gan,
        "hour_zhi": hour_zhi,
        "hour_gz": hour_gz,
    }


def _get_yuan(day_gz_index: int) -> int:
    """
    Determine 上元 (0), 中元 (1), or 下元 (2) from day's 60-cycle position.

    Using the 甲己日 rule:
    - 甲/己日 with 子/午/卯/酉 branch → 上元
    - 甲/己日 with 寅/申/巳/亥 branch → 中元
    - 甲/己日 with 辰/戌/丑/未 branch → 下元

    For non-甲/己 days, look backward to the previous 甲日 or 己日.
    """
    if day_gz_index < 0:
        return 0

    # Find the nearest previous 甲日 (index % 10 == 0) or 己日 (index % 10 == 5)
    offset = day_gz_index % 10
    if offset < 5:  # we've passed a 甲日
        ref_index = day_gz_index - offset
    else:  # we've passed a 己日
        ref_index = day_gz_index - (offset - 5)

    ref_branch = ref_index % 12  # earthly branch index of the reference 甲/己日

    # 子(0) 午(6) 卯(3) 酉(9) → 上元
    if ref_branch in (0, 6, 3, 9):
        return 0
    # 寅(2) 申(8) 巳(5) 亥(11) → 中元
    if ref_branch in (2, 8, 5, 11):
        return 1
    # 辰(4) 戌(10) 丑(1) 未(7) → 下元
    return 2


def _get_ju_number(solar_term_name: str, yuan: int) -> tuple:
    """
    Return (yin_yang_type, ju_number) for a given solar term and 元.

    Args:
        solar_term_name: Chinese name of the solar term (Jie).
        yuan: 0=上元, 1=中元, 2=下元.

    Returns:
        (type_str, ju_number) e.g. ("yang", 1) or ("yin", 9)
    """
    info = SOLAR_TERM_JU.get(solar_term_name, {"type": "yang", "ju_list": [1, 7, 4]})
    yin_yang_type = info["type"]
    ju_number = info["ju_list"][yuan]
    return yin_yang_type, ju_number


def _build_earth_level(yin_yang_type: str, ju_number: int) -> dict:
    """
    Place the 9 stems (六仪三奇) in the nine palaces for the Earth Level (地盘).

    阳遁: stems advance through increasing palace numbers (wrapping at 9).
    阴遁: stems advance through decreasing palace numbers.

    Stem order: 戊, 己, 庚, 辛, 壬, 癸, 丁, 丙, 乙

    Returns:
        dict mapping palace_number → stem_character
    """
    stems = SIX_YI_THREE_QI  # 戊己庚辛壬癸丁丙乙
    earth = {}

    for i, stem in enumerate(stems):
        if yin_yang_type == "yang":
            # Start at ju_number, increase by i, wrap at 9
            palace = (ju_number - 1 + i) % 9 + 1
        else:
            # Start at ju_number, decrease by i, wrap at 9
            palace = (ju_number - 1 - i) % 9 + 1

        earth[palace] = stem

    return earth


def _find_xun_shou(hour_gz: str) -> tuple:
    """
    Find the 旬首 (Xun Shou) for a given hour's 干支.

    Returns:
        (xun_shou_ganzhi, leader_stem) e.g. ("甲子", "戊")
    """
    if hour_gz not in GAN_ZHI_60:
        return ("甲子", "戊")

    index = GAN_ZHI_60.index(hour_gz)
    xun_start = (index // 10) * 10
    xun_shou = GAN_ZHI_60[xun_start]

    leader_stem = XUN_SHOU_MAP.get(xun_shou, "戊")
    return xun_shou, leader_stem


def _get_hour_gz_index(gan: str, zhi: str) -> int:
    """Find 60-cycle index for a stem+branch pair."""
    pair = gan + zhi
    if pair in GAN_ZHI_60:
        return GAN_ZHI_60.index(pair)
    return -1


def _build_heaven_level(earth: dict, yin_yang_type: str,
                        hour_gan: str, hour_zhi: str) -> dict:
    """
    Build the Heaven Level (天盘) — rotated Nine Stars.

    The 值符 (Zhi Fu) is the star whose palace's earth stem matches the
    旬首's leader stem. The entire Heaven Level then rotates so that
    the 值符's corresponding 天干 moves to the hour's palace.
    """
    # Get hour ganzhi index
    hour_gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    hour_zhi_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    hour_gz_str = hour_gan + hour_zhi
    xun_shou, leader_stem = _find_xun_shou(hour_gz_str)

    # Find which palace has the leader_stem on the Earth Level
    zhi_fu_palace = None
    for palace, stem in earth.items():
        if stem == leader_stem:
            zhi_fu_palace = palace
            break

    # The 值符 star is the star that normally sits in zhi_fu_palace
    # But we need to determine where it rotates TO

    # First, determine the hour's "palace" (where the hour is in the 九宫)
    # The hour's branch determines direction/palace:
    # 子→1(坎), 丑寅→8(艮), 卯→3(震), 辰巳→4(巽),
    # 午→9(离), 未申→2(坤), 酉→7(兑), 戌亥→6(乾)
    branch_to_palace = {
        "子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
        "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6,
    }
    hour_palace = branch_to_palace.get(hour_zhi, 1)

    # Heaven Level rotation:
    # The 值符 (represented by leader_stem on Earth) moves to hour_palace.
    # All other stems follow the same rotation.
    heaven = {}
    if zhi_fu_palace:
        # Calculate rotation offset
        # zhi_fu_palace moves to hour_palace
        # So offset = hour_palace - zhi_fu_palace (mod 9, skipping 5/center)
        offset = (hour_palace - zhi_fu_palace) % 9
        for palace, stem in earth.items():
            # The stem from palace moves to (palace + offset) % 9
            new_palace = ((palace - 1 + offset) % 9) + 1
            heaven[new_palace] = stem
    else:
        heaven = dict(earth)

    return heaven


def _build_human_level(earth: dict, yin_yang_type: str,
                       hour_gan: str, hour_zhi: str) -> dict:
    """
    Build the Human Level (人盘) — Eight Doors (八门).

    The 值使 (Zhi Shi) is the door in the same palace as the 值符's stem.
    The 值使 rotates based on the hour's earthly branch.
    """
    xun_shou, leader_stem = _find_xun_shou(hour_gan + hour_zhi)

    # Find the 值使 palace (same palace where leader_stem is on Earth)
    zhi_shi_palace = None
    for palace, stem in earth.items():
        if stem == leader_stem:
            zhi_shi_palace = palace
            break

    # Determine door rotation based on hour branch
    branch_to_uph = {
        "子": 1, "丑": 2, "寅": 3, "卯": 4, "辰": 5, "巳": 6,
        "午": 7, "未": 8, "申": 9, "酉": 10, "戌": 11, "亥": 12,
    }
    zhi_num = branch_to_uph.get(hour_zhi, 1)

    # Doors in their fixed positions: 休1 生8 伤3 杜4 景9 死2 惊7 开6
    # But this is for 阳遁. For 阴遁, the rotation direction reverses.
    door_order = [1, 8, 3, 4, 9, 2, 7, 6]
    # Actually, the doors have a specific order in the qimen cycle.
    # The standard arrangement is by the 后天八卦 sequence.

    # For a simpler approach, use 阳遁 clockwise, 阴遁 counter-clockwise
    if yin_yang_type == "yang":
        door_cycle = [1, 8, 3, 4, 9, 2, 7, 6]
    else:
        door_cycle = [1, 8, 3, 4, 9, 2, 7, 6]
        # Could reverse for yin dun... but door placement follows the
        # 值使 rule, not a simple reversal

    # The 值使 door rotates by (zhi_num - 1) steps from its starting palace
    if zhi_shi_palace and zhi_shi_palace != 5:
        # Find the door in zhi_shi_palace
        door_names_fixed = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
        door_palaces_fixed = [1, 8, 3, 4, 9, 2, 7, 6]

        # Map door name to its position in the fixed order
        door_name = DOOR_BY_PALACE.get(zhi_shi_palace, {}).get("name", "休")
        if door_name:
            idx = door_names_fixed.index(door_name)
            # Rotate by (zhi_num - 1) steps
            new_idx = (idx + zhi_num - 1) % len(door_names_fixed)
            new_palace = door_palaces_fixed[new_idx]

            # Now place all doors rotated by the same offset
            offset = (new_idx - idx) % len(door_names_fixed)
            human = {}
            for i, dn in enumerate(door_names_fixed):
                rotated_idx = (i - offset) % len(door_names_fixed)  # reverse to find which door lands in which palace
                # Actually: original door at palace P moves to palace P'
                # door i (at fixed palace P_i) → moves to palace P_{i + offset}
                rotated_palace_idx = (i + offset) % len(door_names_fixed)
                palace_num = door_palaces_fixed[rotated_palace_idx]
                human[palace_num] = door_names_fixed[i]
            return human

    # Fallback: fixed door placement
    return {1: "休", 8: "生", 3: "伤", 4: "杜", 9: "景", 2: "死", 7: "惊", 6: "开"}


def _build_spirit_level(earth: dict, yin_yang_type: str,
                        hour_gan: str, hour_zhi: str) -> dict:
    """
    Build the Spirit Level (神盘) — Eight Gods (八神).

    值符 god starts at the 值符 palace and the gods follow in order.
    For 阳遁 the gods go forward, for 阴遁 they go backward.

    God order: 值符, 腾蛇, 太阴, 六合, 白虎, 玄武, 九地, 九天
    """
    god_order = [g["name"] for g in GODS]  # 值符, 腾蛇, 太阴, 六合, 白虎, 玄武, 九地, 九天

    xun_shou, leader_stem = _find_xun_shou(hour_gan + hour_zhi)

    # Find 值符 palace
    zhi_fu_palace = None
    for palace, stem in earth.items():
        if stem == leader_stem:
            zhi_fu_palace = palace
            break

    if zhi_fu_palace is None:
        zhi_fu_palace = 1

    # Place gods in the 9 palaces (skipping palace 5, center)
    # The 8 gods map to the 8 outer palaces
    outer_palaces = [1, 8, 3, 4, 9, 2, 7, 6]  # skip 5

    if yin_yang_type == "yin":
        # 阴遁: gods follow in reverse order through the palaces
        god_order = list(reversed(god_order))

    # Start 值符 at zhi_fu_palace, then place remaining gods in palace order
    if zhi_fu_palace in outer_palaces:
        start_idx = outer_palaces.index(zhi_fu_palace)
    else:
        start_idx = 0

    spirit = {}
    for i, god_name in enumerate(god_order):
        palace_idx = (start_idx + i) % len(outer_palaces)
        palace = outer_palaces[palace_idx]
        spirit[palace] = god_name

    return spirit


def _get_yinyang_by_date(year: int, month: int, day: int) -> tuple:
    """
    Determine yin/yang type and ju number directly from the solar date.
    Uses the 拆补法 (split-and-fill method).

    Returns:
        (yin_yang_type, ju_number, solar_term_name, yuan)
    """
    solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
    lunar = solar.getLunar()

    prev_jie_obj = lunar.getPrevJie()
    if prev_jie_obj is None:
        # Fallback: use prev_qi
        prev_jie_obj = lunar.getPrevQi()

    jie_name = prev_jie_obj.getName() if prev_jie_obj else "冬至"

    day_gz_str = lunar.getDayInGanZhi()
    day_gz_index = GAN_ZHI_60.index(day_gz_str) if day_gz_str in GAN_ZHI_60 else 0

    yuan = _get_yuan(day_gz_index)
    yin_yang_type, ju = _get_ju_number(jie_name, yuan)

    return yin_yang_type, ju, jie_name, yuan


def calc_qimen(year: int, month: int, day: int, hour: int = 12, minute: int = 0):
    """
    Calculate a complete Qimen Dunjia (奇门遁甲) chart for a given time.

    Args:
        year, month, day, hour, minute: Date/time components (24h format).

    Returns:
        dict: Complete Qimen Dunjia chart data.
    """
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    e8 = EightChar.fromLunar(lunar)

    # ── 1. Solar term, yin/yang, ju number ────────────────────────
    yin_yang_type, ju_number, solar_term_name, yuan = _get_yinyang_by_date(year, month, day)

    # Get JieQi details
    prev_jie = lunar.getPrevJie()
    prev_qi = lunar.getPrevQi()
    next_jie = lunar.getNextJie()
    next_qi = lunar.getNextQi()

    # ── 2. Day/Hour ganzhi ─────────────────────────────────────────
    day_gz_str = lunar.getDayInGanZhi()
    day_gz_index = GAN_ZHI_60.index(day_gz_str) if day_gz_str in GAN_ZHI_60 else -1

    hour_gan = e8.getTimeGan()
    hour_zhi = e8.getTimeZhi()
    hour_gz_str = hour_gan + hour_zhi

    # ── 3. Build Four Levels ──────────────────────────────────────
    earth = _build_earth_level(yin_yang_type, ju_number)

    heaven = _build_heaven_level(earth, yin_yang_type, hour_gan, hour_zhi)

    human = _build_human_level(earth, yin_yang_type, hour_gan, hour_zhi)

    spirit = _build_spirit_level(earth, yin_yang_type, hour_gan, hour_zhi)

    # ── 4. Assemble Nine Palaces grid ──────────────────────────────
    nine_palaces = []
    for ls_num in LUO_SHU:
        palace_info = dict(PALACE_INFO[ls_num])
        palace_info["palace_number"] = ls_num
        palace_info["earth_stem"] = earth.get(ls_num, "")
        palace_info["heaven_stem"] = heaven.get(ls_num, "")

        # Door (human level)
        door_name = human.get(ls_num, "")
        door_data = None
        if door_name:
            for d in DOORS:
                if d["name"] == door_name:
                    door_data = dict(d)
                    break
        palace_info["door"] = door_data

        # Star (heaven level - nine stars)
        star = STAR_BY_PALACE.get(ls_num)
        palace_info["star"] = dict(star) if star else None

        # God (spirit level)
        god_name = spirit.get(ls_num, "")
        god_data = None
        if god_name:
            for g in GODS:
                if g["name"] == god_name:
                    god_data = dict(g)
                    break
        palace_info["god"] = god_data

        nine_palaces.append(palace_info)

    # ── 5. Xun Shou and key markers ────────────────────────────────
    xun_shou, leader_stem = _find_xun_shou(hour_gz_str)

    # ── 6. Auspicious patterns analysis ───────────────────────────
    analysis = _analyze_qimen(nine_palaces, yin_yang_type, ju_number, hour_gz_str)

    return {
        "datetime": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        "lunar_date": lunar.toFullString(),
        "solar_term": solar_term_name,
        "prev_qi": prev_qi.getName() if prev_qi else "",
        "next_jie": next_jie.getName() if next_jie else "",
        "yin_yang": "阳遁" if yin_yang_type == "yang" else "阴遁",
        "yin_yang_type": yin_yang_type,
        "ju_number": ju_number,
        "yuan": ["上元", "中元", "下元"][yuan],
        "day_gan_zhi": day_gz_str,
        "hour_gan_zhi": hour_gz_str,
        "xun_shou": xun_shou,
        "leader_stem": leader_stem,
        "nine_palaces": nine_palaces,
        "analysis": analysis,
    }


# ═══════════════════════════════════════════════════════════════════
#  Analysis
# ═══════════════════════════════════════════════════════════════════

def _analyze_qimen(nine_palaces: list, yin_yang_type: str,
                   ju_number: int, hour_gz: str) -> dict:
    """
    Analyze a Qimen chart for auspicious/inauspicious patterns.

    Looks for:
    - Doors opening in auspicious directions
    - Star and door combinations
    - God placements
    - Special patterns
    """
    findings = []
    auspicious_directions = []
    inauspicious_directions = []

    for p in nine_palaces:
        direction = p.get("direction", "")
        door = p.get("door")
        star = p.get("star")
        god = p.get("god")
        palace_num = p.get("palace_number", 0)

        if palace_num == 5:
            continue  # skip center

        # Check door auspiciousness
        if door and door.get("good"):
            findings.append({
                "type": "auspicious",
                "item": f"{door['english']} Door ({door['name']})",
                "location": f"{p['name']}宫 ({direction})",
                "detail": door["meaning"],
            })
            auspicious_directions.append({
                "direction": direction,
                "palace": p["name"],
                "door": door["name"],
                "star": star["english"] if star else "",
                "activity": _door_activity(door["name"]),
            })
        elif door and not door.get("good"):
            findings.append({
                "type": "inauspicious",
                "item": f"{door['english']} Door ({door['name']})",
                "location": f"{p['name']}宫 ({direction})",
                "detail": door["meaning"],
            })
            inauspicious_directions.append({
                "direction": direction,
                "palace": p["name"],
                "door": door["name"],
            })

        # Check for star + good door combination
        if door and star and door.get("good") and star.get("good"):
            findings.append({
                "type": "excellent",
                "item": f"{star['english']} + {door['english']} Door",
                "location": f"{p['name']}宫 ({direction})",
                "detail": f"Both star and door are auspicious in {direction}. Excellent for important activities.",
            })

        # Check god placement
        if god:
            if god.get("good"):
                findings.append({
                    "type": "auspicious",
                    "item": f"{god['english']} God ({god['name']})",
                    "location": f"{p['name']}宫 ({direction})",
                    "detail": god["meaning"],
                })
            else:
                findings.append({
                    "type": "inauspicious",
                    "item": f"{god['english']} God ({god['name']})",
                    "location": f"{p['name']}宫 ({direction})",
                    "detail": god["meaning"],
                })

    # Calculate overall score
    auspicious_count = sum(1 for f in findings if f["type"] in ("auspicious", "excellent"))
    inauspicious_count = sum(1 for f in findings if f["type"] == "inauspicious")
    total = auspicious_count + inauspicious_count
    score = round((auspicious_count / max(total, 1)) * 100)

    # Generate summary
    if score >= 70:
        summary = f"The Qimen chart shows a favorable configuration ({score}% auspicious). This is a good time for action."
    elif score >= 40:
        summary = f"The Qimen chart is mixed ({score}% auspicious). Choose your timing and directions carefully."
    else:
        summary = f"The Qimen chart is challenging ({score}% auspicious). Focus on preparation and avoid major new initiatives."

    return {
        "score": score,
        "summary": summary,
        "findings": findings,
        "auspicious_directions": auspicious_directions,
        "inauspicious_directions": inauspicious_directions,
    }


def _door_activity(door_name: str) -> str:
    """Recommend activities based on the door."""
    recs = {
        "休": "Rest, romance, healing, negotiation.",
        "生": "Business, investment, new ventures, wealth activities.",
        "伤": "Competition, sports, military action — use with caution.",
        "杜": "Secrecy, planning, hiding — not for outward action.",
        "景": "Public speaking, exams, marketing, creative performance.",
        "死": "Avoid major action. Funerals, endings, letting go.",
        "惊": "Avoid important matters. Be alert for surprises.",
        "开": "Travel, launching, court cases, opening ceremonies.",
    }
    return recs.get(door_name, "General activities.")


# ═══════════════════════════════════════════════════════════════════
#  Serialization
# ═══════════════════════════════════════════════════════════════════

import json


def to_json(result: dict, indent: int = 2) -> str:
    """Serialize Qimen chart results to JSON."""
    return json.dumps(result, ensure_ascii=False, indent=indent)


# ═══════════════════════════════════════════════════════════════════
#  CLI entry point
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 4:
        y, m, d, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
        mi = int(args[4]) if len(args) > 4 else 0
        result = calc_qimen(y, m, d, h, mi)
        print(to_json(result))
    else:
        now = datetime.now()
        result = calc_qimen(now.year, now.month, now.day, now.hour, now.minute)
        print(to_json(result))
