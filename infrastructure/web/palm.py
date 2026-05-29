"""
Palm Reading (手相) — AI-powered palmistry analysis via Claude Vision.

Users upload a photo of their palm, and Claude Vision analyzes
the lines, mounts, and features to provide a palm reading.
"""

import os
import uuid
import logging
from pathlib import Path
from flask import Blueprint, render_template, request, current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger("fatetell.palm")

palm_bp = Blueprint("palm", __name__)

UPLOAD_FOLDER = Path(__file__).parent.parent.parent / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

PALM_SYSTEM_PROMPT = (
    "You are a master palm reader (手相大师) with 50 years of experience in traditional Chinese palmistry. "
    "You combine ancient Chinese palm reading techniques with modern understanding of human psychology. "
    "You write in a warm, insightful, and empowering tone.\n\n"
    "When analyzing a palm image, examine these features in order:\n\n"
    "1. **Hand Shape** (手型): Identify the hand shape—Earth (square palm, short fingers), Water (long palm, long fingers), "
    "Fire (square palm, long fingers), Air/Wood (rectangular palm, short fingers), or Metal (square/angular). "
    "Each shape reveals fundamental personality traits.\n\n"
    "2. **Major Lines** (三大主线):\n"
    "   - Life Line (生命线): Vitality, health, major life changes\n"
    "   - Head Line (智慧线): Intellect, mindset, communication style\n"
    "   - Heart Line (感情线): Emotions, relationships, love style\n"
    "   Note their length, depth, curvature, breaks, islands, chains, forks, and direction.\n\n"
    "3. **Minor Lines** (辅助线):\n"
    "   - Fate Line (事业线): Career path, destiny\n"
    "   - Sun Line (太阳线): Fame, success, creativity\n"
    "   - Marriage Lines (婚姻线): Relationship timing\n"
    "   - Health Line (健康线): Health indicators\n\n"
    "4. **Mounts** (丘): The fleshy parts of the palm—Mount of Venus, Jupiter, Saturn, "
    "Apollo/Sun, Mercury, Moon, Mars. Each mount's prominence indicates related traits.\n\n"
    "5. **Fingers** (手指): Finger lengths, shapes, gaps, flexibility, and nail shape.\n\n"
    "Write in clear English. Structure your reading as:\n"
    "- **Overview**: First impression and hand type\n"
    "- **Personality & Character**: What the palm reveals about their nature\n"
    "- **Life Path & Vitality**: From the Life Line\n"
    "- **Mind & Intellect**: From the Head Line\n"
    "- **Heart & Relationships**: From the Heart Line\n"
    "- **Career & Destiny**: Career indications\n"
    "- **Current Timing**: Any notable current-life indicators\n"
    "- **Advice**: Practical guidance based on the palm\n\n"
    "Rules:\n"
    "1. Be encouraging and constructive—never predict death or disaster\n"
    "2. If the image is unclear or not a palm, politely say so\n"
    "3. Speak directly to the reader using 'you' and 'your'\n"
    "4. Total 800-1500 words\n"
    "5. Format in clean markdown with section headers"
)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@palm_bp.route("/palm", methods=["GET", "POST"])
def index():
    """Palm reading page with image upload."""
    result = None
    error = None
    hand = request.args.get("hand", "right")

    if request.method == "POST":
        file = request.files.get("palm_image")
        hand = request.form.get("hand", "right")

        if not file or file.filename == "":
            error = "Please select an image to upload."
        elif not allowed_file(file.filename):
            error = "Unsupported file format. Please upload JPG, PNG, or WebP."
        else:
            try:
                # Read file data
                file_data = file.read()
                if len(file_data) > MAX_FILE_SIZE:
                    error = "File too large. Maximum size is 10MB."
                else:
                    # Detect mime type
                    ext = file.filename.rsplit(".", 1)[1].lower()
                    mime_map = {
                        "jpg": "image/jpeg", "jpeg": "image/jpeg",
                        "png": "image/png", "gif": "image/gif",
                        "webp": "image/webp",
                    }
                    media_type = mime_map.get(ext, "image/jpeg")

                    # Call Claude Vision API
                    result_text = _analyze_palm(file_data, media_type, hand)

                    if result_text:
                        result = result_text
                    else:
                        # Save and return basic info if API fails
                        filename = f"palm_{uuid.uuid4().hex[:8]}.{ext}"
                        filepath = UPLOAD_FOLDER / filename
                        with open(filepath, "wb") as f:
                            f.write(file_data)
                        result = None
                        error = "Analysis unavailable. Please configure the Claude API key."
            except Exception as e:
                logger.exception("Palm analysis error")
                error = f"Analysis error: {e}"

    return render_template("palm.html", result=result, error=error, hand=hand)


def _analyze_palm(image_data: bytes, media_type: str, hand: str) -> str:
    """Send palm image to Claude Vision for analysis."""
    import base64
    from infrastructure.config import settings

    api_key = settings.preferred_api_key
    if not api_key:
        return ""

    img_b64 = base64.standard_b64encode(image_data).decode("utf-8")

    # Prefer anthropic SDK
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=settings.claude_model or "claude-sonnet-4-6",
            max_tokens=settings.claude_max_tokens or 4000,
            timeout=settings.claude_timeout or 120,
            system=PALM_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": f"This is a photo of the {hand} hand. Please analyze this palm using traditional Chinese palmistry. "
                                f"Describe what you see in detail — the hand shape, major lines (life line, head line, heart line), "
                                f"minor lines, mounts, and fingers. Then provide a complete palm reading based on what you observe.",
                    },
                ],
            }],
        )
        return response.content[0].text
    except ImportError:
        # Fallback: raw HTTP
        import requests
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.claude_model or "claude-sonnet-4-6",
                "max_tokens": settings.claude_max_tokens or 4000,
                "system": PALM_SYSTEM_PROMPT,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"This is a photo of the {hand} hand. Please analyze this palm.",
                        },
                    ],
                }],
            },
            timeout=settings.claude_timeout or 120,
        )
        if resp.ok:
            return resp.json()["content"][0]["text"]
        return ""
