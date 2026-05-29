"""
BaZi business rules — pure logic with zero framework dependencies.

Includes compatibility scoring and Five Element analysis rules.
All functions are pure: same inputs → same outputs every time.
"""

from .bazi import TIAN_GAN_EN


def compatibility_score(b1, b2, name1, name2):
    """
    Element-based compatibility scoring between two BaZi charts.

    Uses the generating (Sheng) and controlling (Ke) cycles of Wu Xing.
    Returns a dict with score, verdict, and analysis text.

    Args:
        b1: First BaZi chart dict.
        b2: Second BaZi chart dict.
        name1: Label for first person.
        name2: Label for second person.

    Returns:
        dict with keys: name1, name2, dm1, dm2, element1, element2,
                        score, verdict, analysis.
    """
    dm1 = b1["day_master"]["gan"]
    dm2 = b2["day_master"]["gan"]
    wx1 = b1["day_master"]["wuxing"][:1]
    wx2 = b2["day_master"]["wuxing"][:1]
    dm1_en = TIAN_GAN_EN[b1["day_master"]["gan_index"]]
    dm2_en = TIAN_GAN_EN[b2["day_master"]["gan_index"]]

    generates = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    controls = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}

    score = 5
    if generates.get(wx1) == wx2 or generates.get(wx2) == wx1:
        score += 3
        verdict = "Excellent Match ✨"
        analysis = (
            f"{dm1_en}({dm1}) and {dm2_en}({dm2}) are in a creative (Sheng) cycle. "
            "Your elements nourish each other — this is a highly compatible pairing."
        )
    elif wx1 == wx2:
        score += 1
        verdict = "Good Match 👍"
        analysis = (
            f"Both share the {wx1} element. "
            "You understand each other intuitively but may lack complementary tension."
        )
    elif controls.get(wx1) == wx2 or controls.get(wx2) == wx1:
        score -= 1
        verdict = "Challenging Match ⚡"
        analysis = (
            f"{dm1_en}({dm1}) and {dm2_en}({dm2}) are in a controlling (Ke) cycle. "
            "Your energies clash, but friction can forge growth."
        )
    else:
        verdict = "Neutral Match"
        analysis = "Your elements neither strongly support nor oppose each other. Outcome depends on the rest of your charts."

    score = max(1, min(10, score))
    return {
        "name1": name1, "name2": name2,
        "dm1": dm1, "dm2": dm2,
        "element1": f"{wx1} ({dm1_en})",
        "element2": f"{wx2} ({dm2_en})",
        "score": score,
        "verdict": verdict,
        "analysis": analysis,
    }
