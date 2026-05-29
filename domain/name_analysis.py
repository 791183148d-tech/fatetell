"""
Name Analysis (姓名学) — Chinese name 五行 and character analysis.

Pure domain logic with zero framework dependencies.
Supports both Chinese names (姓+名) and English name analysis.
"""

import re

# ── Wuxing (五行) associated with each Heavenly Stem digit ───────────

# Simplified: last digit of the year of birth determines 天干 and thus element
# Birth year last digit → element
BIRTH_YEAR_ELEMENT = {
    0: "Metal", 1: "Metal",
    2: "Water", 3: "Water",
    4: "Wood", 5: "Wood",
    6: "Fire", 7: "Fire",
    8: "Earth", 9: "Earth",
}

# Vowel → element mapping for English name analysis
VOWEL_ELEMENT = {
    "a": "Wood", "e": "Fire", "i": "Earth",
    "o": "Metal", "u": "Water",
}

CONSONANT_ELEMENT = {
    "b": "Water", "c": "Fire", "d": "Wood", "f": "Metal",
    "g": "Earth", "h": "Wood", "j": "Fire", "k": "Metal",
    "l": "Earth", "m": "Water", "n": "Water", "p": "Water",
    "q": "Fire", "r": "Wood", "s": "Earth", "t": "Metal",
    "v": "Wood", "w": "Earth", "x": "Metal", "y": "Earth",
    "z": "Fire",
}

# Traditional Chinese name analysis strokes for 1-10
# These are approximate — real 姓名学 uses traditional stroke counts
# Mapping of simplified Chinese characters to 五行 based on radicals
RADICAL_WUXING = {
    # 金 Metal radicals
    "金": "Metal", "钅": "Metal", "刂": "Metal", "刀": "Metal",
    "辛": "Metal", "酉": "Metal", "冫": "Metal",
    # 木 Wood radicals
    "木": "Wood", "扌": "Wood", "艹": "Wood", "禾": "Wood",
    "竹": "Wood", "户": "Wood", "几": "Wood",
    # 水 Water radicals
    "水": "Water", "氵": "Water", "雨": "Water", "鱼": "Water",
    "冖": "Water", "辶": "Water", "北": "Water",
    # 火 Fire radicals
    "火": "Fire", "灬": "Fire", "日": "Fire", "光": "Fire",
    "心": "Fire", "忄": "Fire",
    # 土 Earth radicals
    "土": "Earth", "石": "Earth", "山": "Earth", "王": "Earth",
    "田": "Earth", "瓦": "Earth", "一": "Earth",
}

# Name analysis interpretations
SANCAI_INTERPRETATIONS = {
    ("Wood", "Wood", "Wood"): "Harmonious — strong growth potential, creativity, and expansion.",
    ("Wood", "Wood", "Fire"): "Auspicious — creativity leads to recognition and success.",
    ("Wood", "Wood", "Water"): "Favorable — nurturing support enables steady growth.",
    ("Wood", "Fire", "Earth"): "Flowing — creativity manifests into practical results.",
    ("Wood", "Earth", "Metal"): "Balanced — grounded creativity produces lasting value.",
    ("Fire", "Fire", "Fire"): "Intense — strong passion but risk of burnout.",
    ("Fire", "Fire", "Earth"): "Productive — passion transforms into tangible achievements.",
    ("Fire", "Earth", "Metal"): "Auspicious — vision becomes reality with lasting impact.",
    ("Fire", "Metal", "Water"): "Transformative — challenge leads to deep wisdom.",
    ("Earth", "Earth", "Earth"): "Stable — reliable, grounded, and practical.",
    ("Earth", "Earth", "Metal"): "Favorable — stability enables precision and refinement.",
    ("Earth", "Metal", "Water"): "Prosperous — practical foundations create flowing abundance.",
    ("Earth", "Fire", "Fire"): "Nurturing — inner fire grounded by stable warmth.",
    ("Metal", "Metal", "Metal"): "Strong — determined and resilient, but may lack flexibility.",
    ("Metal", "Metal", "Water"): "Auspicious — strength channels into wisdom and adaptability.",
    ("Metal", "Water", "Wood"): "Flowing — discipline nurtures growth and creativity.",
    ("Metal", "Earth", "Earth"): "Rooted — strength supported by stable foundations.",
    ("Water", "Water", "Water"): "Deep — intuitive, wise, but may be overly emotional.",
    ("Water", "Water", "Wood"): "Auspicious — intuition feeds creative growth.",
    ("Water", "Wood", "Fire"): "Flourishing — wisdom inspires creativity that shines.",
    ("Water", "Fire", "Earth"): "Steaming — dynamic energy channeled into practical results.",
}

# Default interpretations for non-matching combinations
DEFAULT_SANCAI = "Moderately balanced — consider adjusting your name elements for greater harmony."


def _get_first_radical(char: str) -> str:
    """Extract the first character's radical for 五行 analysis."""
    # Check against known radicals
    for radical, wuxing in sorted(RADICAL_WUXING.items(), key=lambda x: -len(x[0])):
        if char.startswith(radical):
            return wuxing
    return "Unknown"


def _analyze_chinese_name(surname: str, given_name: str, birth_year: int = None) -> dict:
    """Analyze a Chinese name (姓 + 名)."""
    # Basic info
    surname_element = _get_first_radical(surname)
    given_element = _get_first_radical(given_name[0]) if given_name else "Earth"

    # Year element if available
    year_element = BIRTH_YEAR_ELEMENT.get(birth_year % 10, "Unknown") if birth_year else None

    # Three Talents (三才): Heaven(姓), Human(名首字), Earth(名末字)
    last_char = given_name[-1] if given_name and len(given_name) > 1 else given_name[0] if given_name else ""
    earth_element = _get_first_radical(last_char) if last_char else given_element

    sancai = (surname_element, given_element, earth_element)
    sancai_text = SANCAI_INTERPRETATIONS.get(sancai, DEFAULT_SANCAI)

    # Calculate Wuxing distribution
    all_chars = surname + given_name
    wuxing_count = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    for ch in all_chars:
        w = _get_first_radical(ch)
        if w in wuxing_count:
            wuxing_count[w] += 1

    # Determine dominant and missing elements
    sorted_wx = sorted(wuxing_count.items(), key=lambda x: -x[1])
    dominant = sorted_wx[0][0] if sorted_wx[0][1] > 0 else "Earth"
    missing = [k for k, v in sorted_wx if v == 0]

    return {
        "name_type": "chinese",
        "surname": surname,
        "given_name": given_name,
        "full_name": surname + given_name,
        "surname_element": surname_element,
        "given_name_element": given_element,
        "earth_element": earth_element,
        "sancai": {"heaven": surname_element, "human": given_element, "earth": earth_element},
        "sancai_interpretation": sancai_text,
        "year_of_birth": birth_year,
        "year_element": year_element,
        "wuxing_balance": wuxing_count,
        "dominant_element": dominant,
        "missing_elements": missing,
    }


def _analyze_english_name(name: str, birth_year: int = None) -> dict:
    """Analyze an English/Western name."""
    name_lower = name.lower().replace(" ", "")
    vowels = "aeiou"

    v_elements = []
    c_elements = []
    for ch in name_lower:
        if ch in vowels:
            v_elements.append(VOWEL_ELEMENT.get(ch, "Earth"))
        elif ch.isalpha():
            c_elements.append(CONSONANT_ELEMENT.get(ch, "Earth"))

    # Aggregate
    wuxing_count = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    for e in v_elements + c_elements:
        if e in wuxing_count:
            wuxing_count[e] += 1

    sorted_wx = sorted(wuxing_count.items(), key=lambda x: -x[1])
    dominant = sorted_wx[0][0] if sorted_wx[0][1] > 0 else "Earth"
    missing = [k for k, v in sorted_wx if v == 0]

    # Name number (modified Pythagorean)
    name_number = sum(ord(c) - 96 for c in name_lower if c.isalpha())

    # Year element
    year_element = BIRTH_YEAR_ELEMENT.get(birth_year % 10, "Unknown") if birth_year else None

    # Guidance based on dominant element
    guidance_map = {
        "Wood": "A name with Wood energy suggests creativity, growth, and expansion. Embrace flexibility.",
        "Fire": "A name with Fire energy indicates passion, visibility, and dynamic expression.",
        "Earth": "A name with Earth energy shows stability, practicality, and nurturing qualities.",
        "Metal": "A name with Metal energy brings discipline, structure, and clarity of purpose.",
        "Water": "A name with Water energy suggests wisdom, adaptability, and deep intuition.",
    }
    guidance = guidance_map.get(dominant, "Balanced name energy — versatile and adaptable.")

    return {
        "name_type": "english",
        "full_name": name,
        "name_number": name_number,
        "year_of_birth": birth_year,
        "year_element": year_element,
        "wuxing_balance": wuxing_count,
        "dominant_element": dominant,
        "missing_elements": missing,
        "guidance": guidance,
    }


def analyze_name(name: str, birth_year: int = None) -> dict:
    """
    Analyze a name using Chinese name science (姓名学).

    Detects whether the name is Chinese (CJK characters) or English/alphabet,
    and applies appropriate analysis.

    Args:
        name: Full name (Chinese or English).
        birth_year: Optional birth year for element reference.

    Returns:
        dict: Name analysis results.
    """
    # Detect Chinese characters
    has_cjk = any("一" <= ch <= "鿿" for ch in name)

    if has_cjk:
        # Parse surname vs given name for Chinese names
        if len(name) >= 2:
            # Usually 1-char surname, 1-2 char given name
            surname = name[0]
            given_name = name[1:]
        else:
            surname = name
            given_name = ""
        return _analyze_chinese_name(surname, given_name, birth_year)
    else:
        return _analyze_english_name(name, birth_year)
