"""
TwinFit IDM-VTON bridge — runs ON the AMD MI300X instance.

Exposes a simple JSON API (:9000) in front of the IDM-VTON gradio demo (:7860).
The TwinFit backend calls POST /tryon here; this bridge feeds the gradio
endpoint (api_name='tryon' in gradio_demo/app.py) and returns the result
as base64.

Run:  uvicorn bridge:app --host 0.0.0.0 --port 9000
"""
import base64
import tempfile
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from gradio_client import Client, handle_file

GRADIO_URL = os.environ.get("GRADIO_URL", "http://127.0.0.1:7860")

app = FastAPI(title="TwinFit IDM-VTON Bridge (AMD MI300X / ROCm)")

_client = None

def gradio_client() -> Client:
    global _client
    if _client is None:
        _client = Client(GRADIO_URL)
    return _client


class TryOnIn(BaseModel):
    person_b64: str                      # raw base64 (no data: prefix)
    garment_url: str | None = None       # product image URL...
    garment_b64: str | None = None       # ...or base64
    garment_desc: str = "garment"        # e.g. "navy cotton kurta"
    denoise_steps: int = 30
    seed: int = 42


@app.get("/health")
def health():
    return {"status": "ok", "engine": "IDM-VTON", "gpu": "AMD MI300X (ROCm)"}


@app.post("/tryon")
def tryon(req: TryOnIn):
    if not req.garment_url and not req.garment_b64:
        raise HTTPException(400, "garment_url or garment_b64 required")

    with tempfile.TemporaryDirectory() as tmp:
        person_path = os.path.join(tmp, "person.png")
        with open(person_path, "wb") as f:
            f.write(base64.b64decode(req.person_b64))

        garment_path = os.path.join(tmp, "garment.png")
        if req.garment_b64:
            with open(garment_path, "wb") as f:
                f.write(base64.b64decode(req.garment_b64))
        else:
            r = httpx.get(req.garment_url, timeout=30, follow_redirects=True)
            r.raise_for_status()
            with open(garment_path, "wb") as f:
                f.write(r.content)

        try:
            result = gradio_client().predict(
                dict={"background": handle_file(person_path), "layers": [], "composite": None},
                garm_img=handle_file(garment_path),
                garment_des=req.garment_desc,
                is_checked=True,        # auto-generate mask
                is_checked_crop=True,   # auto crop & resize
                denoise_steps=req.denoise_steps,
                seed=req.seed,
                api_name="/tryon",
            )
        except Exception as e:
            raise HTTPException(502, f"IDM-VTON inference failed: {e}")

        # result = (output_image, masked_image) — each a filepath or dict with 'path'
        out = result[0]
        out_path = out["path"] if isinstance(out, dict) else out
        with open(out_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

    return {"image_b64": image_b64, "engine": "IDM-VTON @ AMD MI300X"}
