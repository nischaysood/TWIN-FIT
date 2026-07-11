"""
TwinFit backend end-to-end smoke test.

Usage (backend must be running on :8000):
    python test_e2e.py                  # uses a sample/generated person photo
    python test_e2e.py path/to/me.jpg   # uses YOUR photo (better try-on result)

Tests all 5 endpoints and saves the try-on image to tryon_result.png.
"""
import base64
import sys
import time

import httpx

API = "http://localhost:8000"

# Verified direct garment image (white t-shirt, from the IDM-VTON test set)
GARMENT_URL = "https://raw.githubusercontent.com/yisol/IDM-VTON/main/gradio_demo/example/cloth/04469_00.jpg"

# Candidate sample person photos (IDM-VTON test set)
SAMPLE_PERSON_URLS = [
    "https://raw.githubusercontent.com/yisol/IDM-VTON/main/gradio_demo/example/human/00034_00.jpg",
    "https://raw.githubusercontent.com/yisol/IDM-VTON/main/gradio_demo/example/human/00035_00.jpg",
    "https://raw.githubusercontent.com/yisol/IDM-VTON/main/gradio_demo/example/human/01008_00.jpg",
]

PASS, FAIL = "  ✅", "  ❌"
results = []


def check(name, ok, detail=""):
    print(f"{PASS if ok else FAIL} {name}" + (f" — {detail}" if detail else ""))
    results.append(ok)


def get_person_b64() -> str:
    import os
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "rb") as f:
            print(f"Using your photo: {sys.argv[1]}")
            return base64.b64encode(f.read()).decode()
    elif len(sys.argv) > 1:
        print(f"(ignoring '{sys.argv[1]}' — not a file; using sample photo)")
    for url in SAMPLE_PERSON_URLS:
        try:
            r = httpx.get(url, timeout=15, follow_redirects=True)
            if r.status_code == 200 and len(r.content) > 5000:
                print(f"Using sample person photo: {url.rsplit('/', 1)[-1]}")
                return base64.b64encode(r.content).decode()
        except Exception:
            continue
    # Last resort: generate a plain placeholder so the pipeline still runs
    from PIL import Image
    from io import BytesIO
    img = Image.new("RGB", (512, 768), (200, 180, 160))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    print("Using generated placeholder image (pass your own photo for a real result)")
    return base64.b64encode(buf.getvalue()).decode()


def main():
    print(f"\n━━ TwinFit backend smoke test @ {API} ━━\n")

    # 1. Health
    try:
        r = httpx.get(f"{API}/health", timeout=5)
        check("Health check", r.status_code == 200, r.json().get("status"))
    except Exception as e:
        check("Health check", False, f"Backend not reachable: {e}")
        print("\nStart it first:  uvicorn app.main:app --reload --port 8000")
        sys.exit(1)

    # 2. Size recommendation
    r = httpx.post(f"{API}/api/size/recommend", json={
        "height_cm": 175, "weight_kg": 72, "chest_cm": 96,
        "waist_cm": 82, "hip_cm": 98, "brand": "myntra", "category": "kurta",
    }, timeout=10)
    ok = r.status_code == 200 and "recommended_size" in r.json()
    d = r.json() if ok else r.text
    check("Size recommendation", ok,
          f"{d['recommended_size']} ({d['confidence_pct']}%, risk {d['return_risk']})" if ok else d)

    # 3. Brands list
    r = httpx.get(f"{API}/api/size/brands", timeout=5)
    check("Brands list", r.status_code == 200, ", ".join(r.json().get("brands", [])))

    # 4. Garment analysis (real Fireworks vision call if key is set)
    r = httpx.post(f"{API}/api/garment/analyze",
                   json={"image_url": GARMENT_URL}, timeout=120)
    ok = r.status_code == 200
    d = r.json() if ok else r.text
    if ok:
        mock = " [MOCK — no API key?]" if d.get("_mock") else ""
        check("Garment analysis", True,
              f"{d['color']} {d['fabric_est']} {d['category']}, {d['sleeve_type']} sleeve{mock}")
    else:
        check("Garment analysis", False, d)

    # 5. Try-on (async job)
    person_b64 = get_person_b64()
    r = httpx.post(f"{API}/api/tryon/start", json={
        "user_photo_b64": person_b64,
        "garment_image_url": GARMENT_URL,
        "garment_category": "t-shirt",
    }, timeout=30)
    if r.status_code != 200:
        check("Try-on start", False, r.text)
    else:
        job_id = r.json()["job_id"]
        check("Try-on start", True, f"job {job_id[:8]}…")
        print("     polling (HF queue can take 2-6 min, incl. cold start)...", flush=True)
        status = None
        for i in range(120):  # up to ~10 minutes
            time.sleep(5)
            try:
                s = httpx.get(f"{API}/api/tryon/status/{job_id}", timeout=60).json()
            except Exception:
                print("     (status check slow, retrying...)", flush=True)
                continue
            status = s
            if s["status"] in ("done", "failed"):
                break
            if i % 6 == 5:
                note = f" — {s['error']}" if s.get("error") else ""
                print(f"     still {s['status']}{note}", flush=True)
        if status and status["status"] == "done":
            url = status["result_url"]
            engine = status.get("engine", "?")
            if url.startswith("data:"):
                with open("tryon_result.png", "wb") as f:
                    f.write(base64.b64decode(url.split(",", 1)[1]))
                check("Try-on result", True, f"saved tryon_result.png (engine: {engine})")
            else:
                check("Try-on result", True, f"{url} (engine: {engine})")
        else:
            check("Try-on result", False, (status or {}).get("error", "timed out"))

    print(f"\n━━ {sum(results)}/{len(results)} passed ━━\n")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
