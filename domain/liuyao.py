"""
Liu Yao (六爻) — I Ching hexagram divination domain logic.

Pure domain logic, zero framework dependencies.
Contains the 64 hexagrams with Chinese and English interpretations.
"""

import random
from typing import Optional

# ── Bagua (八卦) — 8 trigrams ────────────────────────────────────────

TRIGRAMS = {
    "乾": {"english": "Qian", "symbol": "☰", "nature": "Heaven", "element": "Metal",
           "family": "Father", "direction": "NW"},
    "兑": {"english": "Dui",  "symbol": "☱", "nature": "Lake",   "element": "Metal",
           "family": "Youngest Daughter", "direction": "W"},
    "离": {"english": "Li",   "symbol": "☲", "nature": "Fire",   "element": "Fire",
           "family": "Middle Daughter", "direction": "S"},
    "震": {"english": "Zhen", "symbol": "☳", "nature": "Thunder","element": "Wood",
           "family": "Eldest Son", "direction": "E"},
    "巽": {"english": "Xun",  "symbol": "☴", "nature": "Wind",   "element": "Wood",
           "family": "Eldest Daughter", "direction": "SE"},
    "坎": {"english": "Kan",  "symbol": "☵", "nature": "Water",  "element": "Water",
           "family": "Middle Son", "direction": "N"},
    "艮": {"english": "Gen",  "symbol": "☶", "nature": "Mountain","element": "Earth",
           "family": "Youngest Son", "direction": "NE"},
    "坤": {"english": "Kun",  "symbol": "☷", "nature": "Earth",  "element": "Earth",
           "family": "Mother", "direction": "SW"},
}

# Upper trigram index (0-7) → Lower trigram index (0-7) → Hexagram
# Trigram index order: 乾兑离震巽坎艮坤
_HEXAGRAM_MATRIX = {
    # 乾 (Heaven)
    0: {
        0: {"num": 1,  "name": "乾", "english": "The Creative",         "judgement": "元亨利贞. Supreme success, perseverance brings good fortune."},
        1: {"num": 43, "name": "夬", "english": "Breakthrough",         "judgement": "扬于王庭. A resolute breakthrough. Spread the word."},
        2: {"num": 14, "name": "大有", "english": "Great Possession",   "judgement": "元亨. Supreme success. Abundance and prosperity."},
        3: {"num": 34, "name": "大壮", "english": "Great Power",       "judgement": "利贞. Perseverance brings good fortune. Do not advance."},
        4: {"num": 9,  "name": "小畜", "english": "Small Accumulation", "judgement": "亨. Success. Dense clouds but no rain."},
        5: {"num": 5,  "name": "需",  "english": "Waiting",            "judgement": "有孚，光亨，贞吉. Sincere waiting brings light and success."},
        6: {"num": 26, "name": "大畜", "english": "Great Accumulation", "judgement": "利贞. Perseverance favorable. Accumulate inner strength."},
        7: {"num": 11, "name": "泰",  "english": "Peace",              "judgement": "小往大来，吉亨. Small departs, great arrives. Auspicious."},
    },
    # 兑 (Lake)
    1: {
        0: {"num": 10, "name": "履",  "english": "Treading",           "judgement": "履虎尾，不咥人，亨. Treading on tiger's tail — not bitten. Success."},
        1: {"num": 58, "name": "兑",  "english": "The Joyous",         "judgement": "亨，利贞. Success. Perseverance brings joy."},
        2: {"num": 38, "name": "睽",  "english": "Opposition",         "judgement": "小事吉. Small matters succeed amid opposition."},
        3: {"num": 54, "name": "归妹", "english": "The Marrying Maiden","judgement": "征凶，无攸利. Action brings misfortune. Nothing favorable."},
        4: {"num": 61, "name": "中孚", "english": "Inner Truth",       "judgement": "豚鱼吉. Sincerity moves even pigs and fish. Auspicious."},
        5: {"num": 60, "name": "节",  "english": "Limitation",         "judgement": "亨，苦节不可贞. Success but harsh limits cannot persist."},
        6: {"num": 41, "name": "损",  "english": "Decrease",           "judgement": "有孚，元吉. Sincere decrease brings great good fortune."},
        7: {"num": 19, "name": "临",  "english": "Approach",           "judgement": "元亨利贞. Supreme success. The approach of the noble."},
    },
    # 离 (Fire)
    2: {
        0: {"num": 13, "name": "同人", "english": "Fellowship",        "judgement": "同人于野，亨. Fellowship in the open. Success."},
        1: {"num": 49, "name": "革",  "english": "Revolution",         "judgement": "已日乃孚. Change brings trust after a time."},
        2: {"num": 30, "name": "离",  "english": "The Clinging",       "judgement": "利贞，亨. Perseverance and success through clinging to what is right."},
        3: {"num": 55, "name": "丰",  "english": "Abundance",          "judgement": "亨，王假之. Success. The king reaches abundance."},
        4: {"num": 37, "name": "家人", "english": "The Family",        "judgement": "利女贞. Favourable for the woman's perseverance."},
        5: {"num": 63, "name": "既济", "english": "After Completion",  "judgement": "亨小，利贞. Success in small matters. Initial good fortune."},
        6: {"num": 22, "name": "贲",  "english": "Grace",              "judgement": "亨，小利有攸往. Success. Small advantages in action."},
        7: {"num": 36, "name": "明夷", "english": "Darkening of Light", "judgement": "利艰贞. Perseverance in adversity brings benefit."},
    },
    # 震 (Thunder)
    3: {
        0: {"num": 25, "name": "无妄", "english": "Innocence",         "judgement": "元亨利贞. Supreme success. Innocent action brings reward."},
        1: {"num": 17, "name": "随",  "english": "Following",         "judgement": "元亨利贞. Supreme success. Follow the season."},
        2: {"num": 21, "name": "噬嗑", "english": "Biting Through",   "judgement": "亨，利用狱. Success. Favourable for legal matters."},
        3: {"num": 51, "name": "震",  "english": "The Arousing",      "judgement": "亨，震来虩虩. Success comes through shock and awakening."},
        4: {"num": 42, "name": "益",  "english": "Increase",          "judgement": "利有攸往，利涉大川. Favorable to advance and cross great rivers."},
        5: {"num": 3,  "name": "屯",  "english": "Initial Difficulty", "judgement": "元亨利贞. Success through perseverance amid chaos."},
        6: {"num": 27, "name": "颐",  "english": "Nourishment",       "judgement": "贞吉. Perseverance brings good fortune."},
        7: {"num": 24, "name": "复",  "english": "Return",            "judgement": "亨，出入无疾. Success. Return after a setback."},
    },
    # 巽 (Wind)
    4: {
        0: {"num": 44, "name": "姤",  "english": "Meeting",           "judgement": "女壮，勿用取女. A powerful encounter. Proceed with caution."},
        1: {"num": 28, "name": "大过", "english": "Great Excess",     "judgement": "栋桡. The ridgepole sags. Time for radical change."},
        2: {"num": 50, "name": "鼎",  "english": "The Cauldron",      "judgement": "元吉，亨. Great good fortune. Nurturing new possibilities."},
        3: {"num": 32, "name": "恒",  "english": "Duration",          "judgement": "亨，无咎，利贞. Success without blame. Perseverance brings reward."},
        4: {"num": 57, "name": "巽",  "english": "The Gentle",        "judgement": "小亨，利有攸往. Small success through gentle persistence."},
        5: {"num": 48, "name": "井",  "english": "The Well",          "judgement": "改邑不改井. The town may change but the well remains."},
        6: {"num": 18, "name": "蛊",  "english": "Corruption",        "judgement": "元亨，利涉大川. Success through correcting decay."},
        7: {"num": 46, "name": "升",  "english": "Pushing Upward",    "judgement": "元亨. Supreme success through steady ascent."},
    },
    # 坎 (Water)
    5: {
        0: {"num": 6,  "name": "讼",  "english": "Conflict",          "judgement": "有孚窒惕，中吉. Sincere caution brings mid-level fortune."},
        1: {"num": 47, "name": "困",  "english": "Oppression",        "judgement": "亨，贞，大人吉. Success through perseverance. The noble one endures."},
        2: {"num": 64, "name": "未济", "english": "Before Completion","judgement": "亨，小狐汔济. Before completion. Proceed with care like a fox."},
        3: {"num": 40, "name": "解",  "english": "Deliverance",       "judgement": "利西南. Favorable to move southwest. Release from tension."},
        4: {"num": 59, "name": "涣",  "english": "Dispersion",        "judgement": "亨，王假有庙. Success through scattering and reforming."},
        5: {"num": 29, "name": "坎",  "english": "The Abyss",         "judgement": "有孚维心. Sincerity in the heart sustains through danger."},
        6: {"num": 4,  "name": "蒙",  "english": "Youthful Folly",    "judgement": "亨，匪我求童蒙. Success through learning from experience."},
        7: {"num": 7,  "name": "师",  "english": "The Army",          "judgement": "贞，丈人吉. Perseverance. Leadership brings good fortune."},
    },
    # 艮 (Mountain)
    6: {
        0: {"num": 33, "name": "遁",  "english": "Retreat",           "judgement": "亨小，利贞. Small success. Timely retreat is wise."},
        1: {"num": 31, "name": "咸",  "english": "Influence",         "judgement": "亨，利贞，取女吉. Success in relationships and influence."},
        2: {"num": 56, "name": "旅",  "english": "The Wanderer",      "judgement": "小亨，旅贞吉. Small success for the traveler."},
        3: {"num": 62, "name": "小过", "english": "Small Excess",     "judgement": "亨，利贞. Success through modest action."},
        4: {"num": 53, "name": "渐",  "english": "Development",       "judgement": "女归吉. Gradual progress like a maiden's marriage."},
        5: {"num": 39, "name": "蹇",  "english": "Obstruction",       "judgement": "利西南，不利东北. Adversity. Turn back and find another way."},
        6: {"num": 52, "name": "艮",  "english": "Stillness",         "judgement": "艮其背. Knowing when to stop. Stillness of the back."},
        7: {"num": 15, "name": "谦",  "english": "Modesty",           "judgement": "亨，君子有终. Success through humility. The noble one prevails."},
    },
    # 坤 (Earth)
    7: {
        0: {"num": 12, "name": "否",  "english": "Standstill",        "judgement": "否之匪人. Stagnation. The noble one withdraws inward."},
        1: {"num": 45, "name": "萃",  "english": "Gathering",         "judgement": "亨，王假有庙. Success through gathering and community."},
        2: {"num": 35, "name": "晋",  "english": "Progress",          "judgement": "康侯用锡马蕃庶. Progress rewarded. Advancement and success."},
        3: {"num": 16, "name": "豫",  "english": "Enthusiasm",        "judgement": "利建侯行师. Favorable to establish leaders and take action."},
        4: {"num": 20, "name": "观",  "english": "Contemplation",     "judgement": "盥而不荐. Observe without acting. Understanding comes first."},
        5: {"num": 8,  "name": "比",  "english": "Union",             "judgement": "吉，原筮. Union brings good fortune. Seek connection."},
        6: {"num": 23, "name": "剥",  "english": "Splitting Apart",   "judgement": "不利有攸往. Not favorable to advance. The foundation weakens."},
        7: {"num": 2,  "name": "坤",  "english": "The Receptive",     "judgement": "元亨，利牝马之贞. Supreme success through receptivity and devotion."},
    },
}

# Upper/lower trigram name order matching index
_TRIGRAM_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]


def _get_trigram_index(name: str) -> int:
    try:
        return _TRIGRAM_ORDER.index(name)
    except ValueError:
        return 0


def toss_coins(num_coins: int = 3) -> int:
    """
    Simulate tossing 3 Chinese coins for I Ching divination.

    Returns: 6 (yin changing), 7 (yang), 8 (yin), or 9 (yang changing)
    Traditional: heads=3, tails=2
    3 heads = 9 (old yang, changing)
    2 heads + 1 tail = 8 (young yin)
    1 head + 2 tails = 7 (young yang)
    3 tails = 6 (old yin, changing)
    """
    total = sum(random.randint(2, 3) for _ in range(3))
    # Simplification: 6=old yin, 7=young yang, 8=young yin, 9=old yang
    return total


def generate_hexagram() -> dict:
    """
    Generate a complete I Ching reading by tossing 6 lines.

    Returns dict with:
    - lines: list of 6 line values (bottom to top)
    - original_hexagram: upper/lower trigram and hexagram info
    - changing_hexagram: if any changing lines, the transformed hexagram
    - changing_lines: which lines are changing (0-indexed from bottom)
    - judgement: oracular text
    """
    lines = [toss_coins() for _ in range(6)]  # bottom to top
    # Convert to yin/yang
    line_yinyang = [("—" if l % 2 == 0 else "-") for l in lines]  # even=yin(---), odd=yang(——)
    # Actually: 6/8 = yin (broken), 7/9 = yang (solid)
    line_symbols = []
    for l in lines:
        if l in (6, 8):
            line_symbols.append("- -")  # yin
        else:
            line_symbols.append("———")  # yang

    # Determine trigrams
    lower_binary = [1 if l in (7, 9) else 0 for l in lines[:3]]  # bottom 3 lines, 1=yang
    upper_binary = [1 if l in (7, 9) else 0 for l in lines[3:]]   # top 3 lines
    lower_trigram = _binary_to_trigram(lower_binary)
    upper_trigram = _binary_to_trigram(upper_binary)

    # Look up hexagram
    hex_data = _lookup_hexagram(upper_trigram, lower_trigram)

    # Find changing lines (6 or 9)
    changing_indices = [i for i, l in enumerate(lines) if l in (6, 9)]

    # Generate changing hexagram if applicable
    changed_data = None
    if changing_indices:
        changed_lines = list(lines)
        for i in changing_indices:
            # Flip: 6→7, 9→8
            if changed_lines[i] == 6:
                changed_lines[i] = 7
            elif changed_lines[i] == 9:
                changed_lines[i] = 8

        # Recalculate trigrams for changed hexagram
        clower_bin = [1 if l in (7, 9) else 0 for l in changed_lines[:3]]
        cupper_bin = [1 if l in (7, 9) else 0 for l in changed_lines[3:]]
        clower_tri = _binary_to_trigram(clower_bin)
        cupper_tri = _binary_to_trigram(cupper_bin)
        changed_data = _lookup_hexagram(cupper_tri, clower_tri)

    # Line interpretations
    line_texts = _get_line_interpretations(hex_data["num"], lines)

    return {
        "lines": lines,
        "line_symbols": line_symbols,
        "lower_trigram": {"name": lower_trigram, "info": TRIGRAMS.get(lower_trigram, {})},
        "upper_trigram": {"name": upper_trigram, "info": TRIGRAMS.get(upper_trigram, {})},
        "hexagram": hex_data,
        "changing_lines": changing_indices,
        "changed_hexagram": changed_data,
        "line_texts": line_texts,
    }


def _binary_to_trigram(bits: list) -> str:
    """Convert 3 binary bits (1=yang, 0=yin) to trigram name.
    Using the bagua binary mapping:
    yin=0, yang=1, bits are bottom to top.
    0b111=乾, 0b110=兑, 0b101=离, 0b100=震
    0b011=巽, 0b010=坎, 0b001=艮, 0b000=坤
    """
    mapping = {
        0b111: "乾", 0b110: "兑", 0b101: "离", 0b100: "震",
        0b011: "巽", 0b010: "坎", 0b001: "艮", 0b000: "坤",
    }
    code = (bits[0] << 2) | (bits[1] << 1) | bits[2]
    return mapping.get(code, "乾")


def _lookup_hexagram(upper_name: str, lower_name: str) -> dict:
    """Look up hexagram by upper and lower trigram names."""
    upper_idx = _get_trigram_index(upper_name)
    lower_idx = _get_trigram_index(lower_name)

    row = _HEXAGRAM_MATRIX.get(upper_idx, {})
    hex_data = row.get(lower_idx, {"num": 1, "name": "乾", "english": "The Creative",
                                    "judgement": "元亨利贞. Supreme success."})
    hex_data["upper_trigram"] = upper_name
    hex_data["lower_trigram"] = lower_name
    return hex_data


def _get_line_interpretations(hexagram_num: int, lines: list) -> list:
    """Provide basic interpretation for each line."""
    interpretations = []
    positions = ["bottom (beginning)", "second (inside)", "third (transition)",
                  "fourth (outside)", "fifth (ruler)", "top (climax)"]

    for i, (val, pos) in enumerate(zip(lines, positions)):
        nature = "changing" if val in (6, 9) else "stable"
        yinyang = "Yin" if val in (6, 8) else "Yang"
        symbol = "- -" if val in (6, 8) else "———"

        if val == 6:
            advice = "An ending that leads to transformation. Release the old."
        elif val == 7:
            advice = "A strong but gentle yang line. Steady progress."
        elif val == 8:
            advice = "A receptive yin line. Yield to find your way."
        else:  # 9
            advice = "Strong yang energy peaking. Channel it wisely."

        interpretations.append({
            "position": i + 1,
            "place": pos,
            "value": val,
            "yinyang": yinyang,
            "symbol": symbol,
            "nature": nature,
            "advice": advice,
        })

    return interpretations


def calc_liuyao() -> dict:
    """Full Liu Yao divination reading — convenience wrapper."""
    return generate_hexagram()
