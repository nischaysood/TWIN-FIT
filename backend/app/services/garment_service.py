import json
import httpx
from app.core.config import settings

ANALYSIS_PROMPT = """You are a fashion AI assistant for an Indian e-commerce platform.
Analyze this garment image and return ONLY a valid JSON object with no extra text, no markdown, no explanation.

Required fields:
{
  "category": "one of: top, kurta, kurti, dress, bottom, jeans, trouser, jacket, other",
  "sleeve_type": "one of: sleeveless, short, three-quarter, full, unknown",
  "fit_type": "one of: slim, regular, loose, oversized, unknown",
  "fabric_est": "best guess: cotton, polyester, silk, denim, linen, blended, unknown",
  "color": "primary color as a single word",
  "gender_target": "one of: women, men, unisex",
  "try_on_ready": true
}"""

async def analyze_garment(image_url: str) -> dict:
    if not settings.FIREWORKS_API_KEY:
        return _mock_analysis()

    headers = {
        "Authorization": f"Bearer {settings.FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GEMMA_MODEL,
        "max_tokens": 256,
        "temperature": 0.1,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": ANALYSIS_PROMPT}
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.FIREWORKS_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        result = _mock_analysis()
        result["parse_error"] = True
        return result

def _mock_analysis() -> dict:
    return {
        "category":      "kurta",
        "sleeve_type":   "three-quarter",
        "fit_type":      "regular",
        "fabric_est":    "cotton",
        "color":         "navy",
        "gender_target": "women",
        "try_on_ready":  True,
        "_mock":         True
    }
