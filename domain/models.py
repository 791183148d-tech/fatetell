"""
Domain entities — pure dataclasses with zero framework dependencies.

These types define the core data structures of the FateTell domain.
All layers above (application, infrastructure) depend on these types,
never the reverse.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


# ── BaZi domain entities ──────────────────────────────────────────────

@dataclass
class PillarData:
    """One of the Four Pillars (year, month, day, time)."""
    gan: str                            # 天干 (e.g. "甲")
    zhi: str                            # 地支 (e.g. "子")
    gan_index: int                      # Index into TIAN_GAN list
    zhi_index: int                      # Index into DI_ZHI list
    wuxing: str                         # 五行 of this pillar
    nayin: str                          # 纳音
    hidden_gan: list                     # 藏干
    shi_shen_gan: str                   # 天干十神
    shi_shen_zhi: str                   # 地支十神
    di_shi: str                         # 地十 (12 stages)
    xun_kong: str                       # 旬空


@dataclass
class DaYunCycle:
    """One decade cycle (大运)."""
    gan_zhi: str
    start_age: int
    end_age: int
    years: int


@dataclass
class WuXingAnalysis:
    """Five Element analysis result."""
    percentages: dict
    strongest: str
    weakest: str
    day_master_strength: str            # "Strong" | "Weak"
    balance_advice: dict


@dataclass
class LiunianData:
    """Current year forecast (流年)."""
    year: int
    gan_zhi: str
    current_da_yun: Optional[dict]


@dataclass
class DayMasterData:
    """日主 — the Day Master (self element)."""
    gan: str
    gan_index: int
    wuxing: str
    shi_shen: dict                      # 十神 relationships to other pillars


@dataclass
class ExtraData:
    """Supplementary BaZi readings."""
    tai_yuan: str
    tai_yuan_nayin: str
    ming_gong: str
    ming_gong_nayin: str
    shen_gong: str
    shen_gong_nayin: str
    zodiac: str


@dataclass
class BaZiChart:
    """Complete BaZi (Four Pillars) chart."""
    birth_date: str
    lunar_date: str
    gender: str
    day_master: DayMasterData
    four_pillars: dict                  # {"year": PillarData, "month": ..., ...}
    wuxing: dict                        # {"count": {...}, "analysis": WuXingAnalysis}
    da_yun: dict                        # {"start_age": int, "forward": bool, "cycles": [DaYunCycle]}
    liu_nian: LiunianData
    extra: ExtraData

    def to_dict(self) -> dict:
        """Recursively convert to plain dict (backward compat with existing code)."""
        return _deep_asdict(self)


# ── Order / Payment domain entities ────────────────────────────────────

@dataclass
class OrderData:
    """A customer order / report."""
    id: str
    session_id: str = ""
    name: str = "You"
    birth_data: str = ""
    bazi_json: str = ""
    report_text: str = ""
    status: str = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def is_paid(self) -> bool:
        return self.status == "paid"

    def is_completed(self) -> bool:
        return self.status == "completed"


@dataclass
class PaymentData:
    """A Stripe payment record."""
    id: str
    order_id: str
    amount: int = 0
    currency: str = "usd"
    status: str = "pending"
    stripe_session_id: str = ""
    stripe_payment_intent: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def is_successful(self) -> bool:
        return self.status == "completed"


# ── Qimen Dunjia domain entities ──────────────────────────────────────

@dataclass
class QimenPalace:
    """One palace in the Qimen Dunjia 3×3 nine-palace grid."""
    palace_number: int
    name: str
    direction: str
    wuxing: str
    english_name: str
    earth_stem: str                              # 地盘天干
    heaven_stem: str                             # 天盘天干
    door: Optional[dict] = None                  # 八门
    star: Optional[dict] = None                  # 九星
    god: Optional[dict] = None                   # 八神


@dataclass
class QimenAnalysis:
    """Analysis results for a Qimen Dunjia chart."""
    score: int                                   # 0-100 overall auspiciousness
    summary: str
    findings: list                               # List of auspicious/inauspicious patterns
    auspicious_directions: list                  # Recommended directions
    inauspicious_directions: list               # Avoid directions


@dataclass
class QimenChart:
    """Complete Qimen Dunjia (奇门遁甲) chart."""
    datetime: str
    lunar_date: str
    solar_term: str
    prev_qi: str
    next_jie: str
    yin_yang: str                                # "阳遁" or "阴遁"
    yin_yang_type: str                           # "yang" or "yin"
    ju_number: int                               # 局数 1-9
    yuan: str                                    # 上元/中元/下元
    day_gan_zhi: str
    hour_gan_zhi: str
    xun_shou: str                                # 旬首
    leader_stem: str                             # 值符天干
    nine_palaces: list                           # List of QimenPalace dicts
    analysis: dict                               # QimenAnalysis as dict

    def to_dict(self) -> dict:
        return _deep_asdict(self)


# ── Internal helpers ──────────────────────────────────────────────────

def _deep_asdict(obj):
    """Recursive dataclass → dict, handles nested dataclasses and lists."""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for f in obj.__dataclass_fields__:
            val = getattr(obj, f)
            result[f] = _deep_asdict(val)
        return result
    if isinstance(obj, list):
        return [_deep_asdict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _deep_asdict(v) for k, v in obj.items()}
    return obj
