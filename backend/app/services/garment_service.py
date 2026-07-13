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
    # Prefer a self-hosted OpenAI-compatible endpoint (Gemma 3 on AMD MI300X);
    # otherwise Fireworks serverless; otherwise mock.
    if settings.GEMMA_BASE_URL:
        base_url = settings.GEMMA_BASE_URL.rstrip("/")
        api_key = settings.GEMMA_API_KEY or "none"
    elif settings.FIREWORKS_API_KEY:
        base_url = settings.FIREWORKS_BASE_URL.rstrip("/")
        api_key = settings.FIREWORKS_API_KEY
    else:
        return _mock_analysis()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Fetch the image ourselves and send it inline as a data URI.
    # Works identically across Gemini / Fireworks / self-hosted vLLM, and
    # avoids provider-side URL-fetch limits entirely.
    image_ref = image_url
    try:
        import base64
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            r = await client.get(image_url)
            r.raise_for_status()
            mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
            if mime.startswith("image/"):
                image_ref = f"data:{mime};base64,{base64.b64encode(r.content).decode()}"
    except Exception:
        pass  # fall back to passing the raw URL

    payload = {
        "model": settings.GEMMA_MODEL,
        "max_tokens": 2048,  # reasoning models spend tokens thinking before the JSON
        "temperature": 0.1,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_ref}},
                {"type": "text", "text": ANALYSIS_PROMPT}
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()

    raw_text = data["choices"][0]["message"]["content"].strip()
    try:
        return _extract_json(raw_text)
    except (json.JSONDecodeError, ValueError):
        result = _mock_analysis()
        result["parse_error"] = True
        return result


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a reply that may contain
    reasoning text, markdown fences, or other noise around it."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in model reply")
    return json.loads(text[start:end + 1])

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
