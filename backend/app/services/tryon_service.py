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
    failures = []

    # 1st choice: IDM-VTON on AMD MI300X (hackathon primary engine)
    if settings.IDM_VTON_URL:
        try:
            result_url = await _idm_vton_tryon(user_photo_b64, garment_image_url, garment_category)
            update_job(job_id, status="done", result_url=result_url,
                       engine="IDM-VTON @ AMD MI300X")
            return
        except Exception as e:
            failures.append(f"AMD bridge: {e}")

    # 2nd choice: IDM-VTON via gradio — either your AMD hackathon notebook
    # (TRYON_HF_SPACE=https://xxx.gradio.live) or the public HF Space demo.
    if settings.TRYON_HF_SPACE:
        engine_label = settings.TRYON_ENGINE_LABEL or (
            "IDM-VTON @ AMD GPU (hackathon instance)"
            if settings.TRYON_HF_SPACE.startswith("http")
            else "IDM-VTON @ HuggingFace (demo)")
        try:
            result_url = await _hf_space_tryon(user_photo_b64, garment_image_url, garment_category)
            update_job(job_id, status="done", result_url=result_url,
                       engine=engine_label)
            return
        except Exception as e:
            failures.append(f"IDM-VTON gradio: {e}")

    # Fallback: FLUX Kontext via Fireworks
    try:
        result_url = await _flux_tryon(user_photo_b64, garment_image_url, garment_category)
        update_job(job_id, status="done", result_url=result_url,
                   engine="FLUX Kontext @ Fireworks")
    except Exception as e:
        failures.append(f"FLUX: {e}")
        update_job(job_id, status="failed",
                   error=" | ".join(failures))


async def _hf_space_tryon(user_photo_b64, garment_image_url, garment_category):
    """Real IDM-VTON via the public HuggingFace Space (gradio_client is sync,
    so run it in a worker thread)."""
    return await asyncio.to_thread(
        _hf_space_tryon_sync, user_photo_b64, garment_image_url, garment_category
    )


def _hf_space_tryon_sync(user_photo_b64, garment_image_url, garment_category):
    import base64
    import os
    import tempfile
    from gradio_client import Client, handle_file

    client = Client(settings.TRYON_HF_SPACE,
                    hf_token=settings.HF_TOKEN or None)

    with tempfile.TemporaryDirectory() as tmp:
        person_path = os.path.join(tmp, "person.png")
        with open(person_path, "wb") as f:
            f.write(base64.b64decode(user_photo_b64))

        garment_path = os.path.join(tmp, "garment.png")
        r = httpx.get(garment_image_url, timeout=30, follow_redirects=True)
        r.raise_for_status()
        with open(garment_path, "wb") as f:
            f.write(r.content)

        result = client.predict(
            dict={"background": handle_file(person_path), "layers": [], "composite": None},
            garm_img=handle_file(garment_path),
            garment_des=garment_category,
            is_checked=True,       # auto-mask
            is_checked_crop=True,  # auto crop/resize
            denoise_steps=30,
            seed=42,
            api_name="/tryon",
        )

        out = result[0]
        out_path = out["path"] if isinstance(out, dict) else out
        with open(out_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

    return f"data:image/png;base64,{image_b64}"


async def _idm_vton_tryon(user_photo_b64, garment_image_url, garment_category):
    payload = {
        "person_b64":   user_photo_b64,
        "garment_url":  garment_image_url,
        "garment_desc": garment_category,
    }
    async with httpx.AsyncClient(timeout=300.0) as client:  # SDXL inference takes 30-90s
        response = await client.post(f"{settings.IDM_VTON_URL}/tryon", json=payload)
        response.raise_for_status()
        data = response.json()
    return f"data:image/png;base64,{data['image_b64']}"

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