import asyncio
import time
import httpx
from app.core.config import settings

# Job persistence lives in job_store (Postgres when configured, memory otherwise)
from app.services.job_store import create_job, get_job, update_job  # noqa: F401 (re-exported)
from app.services.storage import store_result_image, storage_enabled
from app.services.telemetry import log_event


async def run_tryon_async(job_id, user_photo_b64, garment_image_url,
                          garment_category="top", merchant_id=None):
    started = time.monotonic()

    def _finish(result_url, engine):
        # Push the PNG to R2 if configured — URLs beat 2MB base64 blobs
        if result_url.startswith("data:") and storage_enabled():
            stored = store_result_image(result_url)
            if stored:
                result_url = stored
        latency = round(time.monotonic() - started, 1)
        update_job(job_id, status="done", result_url=result_url,
                   engine=engine, latency_s=latency)
        log_event("tryon_completed", merchant_id,
                  engine=engine, latency_s=latency, category=garment_category)
        from app.core.auth import count_tryon
        count_tryon(merchant_id)

    update_job(job_id, status="processing")
    log_event("tryon_started", merchant_id, category=garment_category)
    failures = []

    # 1st choice: IDM-VTON on our own GPU (AMD box or any bridge deployment)
    if settings.IDM_VTON_URL:
        try:
            result_url = await _idm_vton_tryon(user_photo_b64, garment_image_url, garment_category)
            _finish(result_url, "IDM-VTON @ AMD MI300X")
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
            _finish(result_url, engine_label)
            return
        except Exception as e:
            failures.append(f"IDM-VTON gradio: {e}")

    # 3rd choice: Gemini image editing (no infra, no cold start — the A/B rival)
    if settings.GEMMA_API_KEY and settings.GEMINI_IMAGE_MODEL:
        try:
            result_url = await _gemini_tryon(user_photo_b64, garment_image_url, garment_category)
            _finish(result_url, "Gemini Image @ Google")
            return
        except Exception as e:
            failures.append(f"Gemini image: {e}")

    # No engine succeeded — fail honestly.
    update_job(job_id, status="failed", error=" | ".join(failures) or "no engine configured")
    log_event("tryon_failed", merchant_id, errors=" | ".join(failures)[:500])


async def _gemini_tryon(user_photo_b64, garment_image_url, garment_category):
    """Try-on via Gemini image editing: person + garment images in,
    composed image out. Zero infrastructure."""
    import base64

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as c:
        r = await c.get(garment_image_url)
        r.raise_for_status()
        garment_b64 = base64.b64encode(r.content).decode()
        garment_mime = r.headers.get("content-type", "image/jpeg").split(";")[0]

    instruction = (
        f"Virtual try-on. The first image is a person; the second image is a {garment_category}. "
        "Generate the person wearing this exact garment. Preserve the person's face, hair, "
        "skin tone, body shape, pose, and the background exactly as in the first image. "
        "Replace only their clothing. Reproduce the garment's exact color, pattern, neckline, "
        "sleeves, and details faithfully. Photorealistic e-commerce quality."
    )
    body = {
        "contents": [{"parts": [
            {"inlineData": {"mimeType": "image/jpeg", "data": user_photo_b64}},
            {"inlineData": {"mimeType": garment_mime, "data": garment_b64}},
            {"text": instruction},
        ]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"{settings.GEMINI_IMAGE_MODEL}:generateContent")
    headers = {"x-goog-api-key": settings.GEMMA_API_KEY,
               "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=120.0) as c:
        resp = await c.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    for part in data["candidates"][0]["content"]["parts"]:
        blob = part.get("inlineData") or part.get("inline_data")
        if blob and blob.get("data"):
            mime = blob.get("mimeType") or blob.get("mime_type") or "image/png"
            return f"data:{mime};base64,{blob['data']}"
    raise RuntimeError("Gemini returned no image part")


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
    import time as _time
    from gradio_client import Client, handle_file

    # Serverless engines (Modal) cold-start for minutes on first hit.
    # Knock politely with a long timeout until the server is awake.
    if settings.TRYON_HF_SPACE.startswith("http"):
        deadline = _time.monotonic() + 420  # up to 7 minutes
        while True:
            try:
                r = httpx.get(settings.TRYON_HF_SPACE, timeout=120.0,
                              follow_redirects=True)
                if r.status_code < 500:
                    break  # awake
            except Exception:
                pass
            if _time.monotonic() > deadline:
                raise TimeoutError("try-on engine did not wake up within 7 min")
            _time.sleep(10)

    try:
        client = Client(settings.TRYON_HF_SPACE,
                        hf_token=settings.HF_TOKEN or None,
                        httpx_kwargs={"timeout": httpx.Timeout(600.0, connect=30.0)})
    except TypeError:  # older gradio_client without httpx_kwargs
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