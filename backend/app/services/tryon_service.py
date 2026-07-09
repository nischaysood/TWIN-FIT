import asyncio
import uuid
from datetime import datetime
import httpx
from app.core.config import settings
from typing import Optional

_jobs = {}

def create_job() -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status":     "queued",
        "result_url": None,
        "error":      None,
        "created_at": datetime.utcnow().isoformat(),
    }
    return job_id

def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)

def update_job(job_id: str, **kwargs):
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)

async def run_tryon_async(job_id, user_photo_b64, garment_image_url, garment_category="top"):
    update_job(job_id, status="processing")
    try:
        result_url = await _flux_tryon(user_photo_b64, garment_image_url, garment_category)
        update_job(job_id, status="done", result_url=result_url)
    except Exception as e:
        update_job(job_id, status="failed", error=str(e))

async def _flux_tryon(user_photo_b64, garment_image_url, garment_category):
    if not settings.FIREWORKS_API_KEY:
        await asyncio.sleep(2)
        return "https://placehold.co/512x768/1E3A5F/white?text=TwinFit+Demo"

    headers = {
        "Authorization": f"Bearer {settings.FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = (
        f"Change the person's clothing to a {garment_category} "
        f"matching the style of this product: {garment_image_url}. "
        "Keep the person's face, skin tone, hair, and body pose exactly the same. "
        "Only change the clothing. Photorealistic, fashion photography style."
    )

    # FLUX.1 Kontext uses Fireworks' async workflow API:
    # POST /workflows/.../{model}  -> request_id
    # POST /workflows/.../{model}/get_result {"id": ...} -> poll until Ready
    model = settings.FLUX_MODEL.split("/")[-1]  # accepts short name or full path
    base = f"{settings.FIREWORKS_BASE_URL}/workflows/accounts/fireworks/models/{model}"

    payload = {
        "prompt": prompt,
        "input_image": user_photo_b64,   # base64 or URL
        "output_format": "png",
        "safety_tolerance": 2,           # max allowed for image-to-image
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(base, headers=headers, json=payload)
        response.raise_for_status()
        request_id = response.json()["request_id"]

        for _ in range(60):  # up to ~2 minutes
            await asyncio.sleep(2)
            res = await client.post(
                f"{base}/get_result", headers=headers, json={"id": request_id}
            )
            res.raise_for_status()
            data = res.json()
            status = data.get("status")
            if status == "Ready":
                return _extract_image(data.get("result"))
            if status in ("Error", "Task not found", "Request Moderated", "Content Moderated"):
                raise RuntimeError(f"Fireworks try-on failed: {status}")

    raise TimeoutError("Try-on generation timed out after 2 minutes")


def _extract_image(result) -> str:
    """Result may be a URL, raw base64, or a dict with a 'sample' field."""
    if isinstance(result, dict):
        result = result.get("sample") or result.get("image") or result.get("url")
    if not result:
        raise RuntimeError("Fireworks returned no image in result")
    if isinstance(result, str) and result.startswith("http"):
        return result
    if isinstance(result, str) and result.startswith("data:"):
        return result
    return f"data:image/png;base64,{result}"