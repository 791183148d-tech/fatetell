"""
AI 报告生成器 — Claude API 适配器 (Implements ReportGateway port).

Generates English BaZi life-reading reports via the Anthropic Claude API.
Falls back to a sample report when no API key is configured.
"""

import json
import logging

from domain.bazi import TIAN_GAN_EN

logger = logging.getLogger("fatetell.report")

# Use anthropic SDK if available, else raw HTTP
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

SYSTEM_PROMPT = (
    "You are a professional BaZi (Chinese Four Pillars) astrologer with 30 years of experience. "
    "You combine traditional Chinese metaphysics with modern psychological insights to provide practical, "
    "actionable life guidance.\n\n"
    "You write in a warm, insightful, and empowering tone - NOT fear-based or superstitious. "
    "Your audience is English-speaking Western users who are curious about Eastern wisdom.\n\n"
    "Rules:\n"
    "1. Always write in clear, fluent English\n"
    "2. Be encouraging and constructive - never predict doom or disaster\n"
    "3. Ground your analysis in the BaZi chart data provided\n"
    "4. Explain Chinese terms (Wu Xing, Yin-Yang, etc.) in simple English\n"
    "5. Format your response in clean markdown\n"
    "6. Each section should be 2-5 paragraphs with specific, personalized insights\n"
    "7. Use 'you' and 'your' to speak directly to the reader\n"
    "8. Include practical advice for each life area\n"
    "9. Total report length: 10000-15000 words\n\n"
    "Report structure:\n"
    "1. OVERVIEW - Brief introduction to the person's BaZi chart\n"
    "2. YOUR DAY MASTER - Analysis of the day master element and personality\n"
    "3. THE FIVE ELEMENTS - Wu Xing balance analysis\n"
    "4. CAREER & WEALTH - Professional tendencies, earning potential, career timing\n"
    "5. RELATIONSHIPS - Romantic compatibility, social style\n"
    "6. PERSONALITY & CHARACTER - Deep personality analysis from the chart\n"
    "7. LIFE TIMING (DA YUN) - The 10-year life cycles and what they mean\n"
    "8. 2026 FORECAST - What the current year brings\n"
    "9. PRACTICAL ADVICE - Actionable recommendations"
)


def format_bazi_for_prompt(bazi_result):
    """Compress BaZi chart data into a compact prompt."""
    fp = bazi_result["four_pillars"]
    dm = bazi_result["day_master"]
    wx = bazi_result["wuxing"]

    pillar_lines = []
    for pname in ["year", "month", "day", "time"]:
        p = fp[pname]
        pillar_lines.append(
            f"  {pname}: {p['gan']}{p['zhi']} | Element: {p['wuxing']} | NaYin: {p['nayin']} | "
            f"Hidden Gans: {', '.join(p['hidden_gan'])} | Shi Shen Gan: {p['shi_shen_gan']} | "
            f"Shi Shen Zhi: {', '.join(p['shi_shen_zhi'])}"
        )

    dy_lines = []
    for c in bazi_result["da_yun"]["cycles"]:
        dy_lines.append(f"  {c['gan_zhi']}: ages {c['start_age']}-{c['end_age']}")

    return f"""BIRTH: {bazi_result['birth_date']}
GENDER: {bazi_result['gender']}
ZODIAC: {bazi_result['extra']['zodiac']}

FOUR PILLARS:
{chr(10).join(pillar_lines)}

DAY MASTER: {dm['gan']} ({TIAN_GAN_EN[dm['gan_index']]}) — Element: {dm['wuxing']}
Shi Shen (ten gods):
  Year stem: {dm['shi_shen']['year_gan']}
  Month stem: {dm['shi_shen']['month_gan']}
  Time stem: {dm['shi_shen']['time_gan']}
  Year branch: {', '.join(dm['shi_shen']['year_zhi'])}
  Month branch: {', '.join(dm['shi_shen']['month_zhi'])}
  Day branch: {', '.join(dm['shi_shen']['day_zhi'])}
  Time branch: {', '.join(dm['shi_shen']['time_zhi'])}

WU XING (FIVE ELEMENTS) COUNTS: {json.dumps(wx['count'], ensure_ascii=False)}
STRONGEST: {wx['analysis']['strongest']}
WEAKEST: {wx['analysis']['weakest']}
DAY MASTER STRENGTH: {wx['analysis']['day_master_strength']}

DA YUN (10-YEAR CYCLES):
{chr(10).join(dy_lines)}

CURRENT YEAR: {bazi_result['liu_nian']['year']} ({bazi_result['liu_nian']['gan_zhi']})
CURRENT DA YUN: {bazi_result['liu_nian']['current_da_yun']['gan_zhi'] if bazi_result['liu_nian']['current_da_yun'] else 'Pre-da-yun'}"""


def generate_report(bazi_result, api_key=None):
    """Generate full BaZi report using Claude API."""
    bazi_text = format_bazi_for_prompt(bazi_result)
    dm_gan = bazi_result["day_master"]["gan"]
    dm_en = TIAN_GAN_EN[bazi_result["day_master"]["gan_index"]]

    user_prompt = f"""Generate a complete BaZi (Chinese astrology) life reading report for this person.

Here is their BaZi chart data:

{bazi_text}

Please write a full report following the structure specified. Make it warm, insightful, and practical for someone discovering Chinese astrology for the first time. Start with a personalized greeting using their Day Master ({dm_en} - {dm_gan}).

The report must be in English and at least 10000 words total."""

    if api_key:
        is_deepseek = api_key.startswith("sk-") and "ant" not in api_key

        # ── DeepSeek (OpenAI-compatible API) ──────────────────────────
        if is_deepseek:
            import requests
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "content-type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "max_tokens": 32000,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=180,
            )
            if resp.ok:
                return resp.json()["choices"][0]["message"]["content"]
            return f"DeepSeek Error: {resp.status_code} {resp.text}"

        # ── Anthropic / Claude ───────────────────────────────────────
        if HAS_ANTHROPIC:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=32000,
                timeout=120,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        else:
            import requests
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 32000,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=120,
            )
            if resp.ok:
                return resp.json()["content"][0]["text"]
            return f"Claude Error: {resp.status_code} {resp.text}"
    else:
        return _sample_report(bazi_result)


def _sample_report(bazi_result):
    """Sample report when no API key is configured."""
    dm = bazi_result["day_master"]["gan"]
    dm_en = TIAN_GAN_EN[bazi_result["day_master"]["gan_index"]]

    return (
        "# Your BaZi Life Reading\n\n"
        "## Overview\n\n"
        f"Welcome to your personal BaZi (Four Pillars of Destiny) reading. Your chart reveals the cosmic "
        f"blueprint at the moment of your birth - not as a fixed destiny, but as a map of potentials, "
        f"strengths, and growth edges.\n\n"
        f"Your Day Master is **{dm_en} ({dm})**, representing your core self. Combined with the other "
        f"seven characters in your chart, a rich picture emerges of your natural talents, challenges, "
        f"and life rhythms.\n\n"
        f"## Your Day Master: The {dm_en} ({dm}) Archetype\n\n"
        f"In the Five Elements system, {dm} is a Metal energy - specifically, {dm_en} represents refined "
        f"ore waiting to be shaped into something magnificent. Metal people are known for their strength, "
        f"discipline, and clarity of thought.\n\n"
        "*If you had the Claude API key configured, a full 5000+ word report would be generated here.*\n\n"
        "---\n\n"
        "*To generate the full report, set the CLAUDE_API_KEY in your .env file and run again.*"
    )


if __name__ == "__main__":
    from domain.bazi import calc_bazi
    result = calc_bazi(1990, 5, 15, 12, gender="male")
    from infrastructure.config import settings
    report = generate_report(result, api_key=settings.preferred_api_key or None)
    print(report[:2000])
    print(f"\n\n... ({len(report)} total chars)")
