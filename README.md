# TwinFit — AI Virtual Try-On for Indian Fashion

> Built for AMD Developer Hackathon: ACT II · Track 3 (Unicorn Track)

TwinFit solves India's #1 fashion e-commerce problem: **25–35% return rates caused by size and fit issues**.

We give D2C fashion brands a self-serve SDK with two features:
1. **AI Size Recommendation** — accurate size prediction from body measurements, calibrated for Indian body types
2. **Virtual Try-On** — photo-based try-on powered by IDM-VTON running on AMD MI300X GPUs

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Garment AI | Gemma 3 27B via Fireworks AI |
| Try-On Model | IDM-VTON on AMD Developer Cloud (ROCm) |
| Try-On Fallback | FLUX.1 Kontext via Fireworks AI |
| Background Removal | REMBG (local) |
| Frontend | Next.js |
| Queue | Redis |
| Infra | AMD Developer Cloud + Docker |

## AMD GPU Usage

- IDM-VTON inference runs on AMD MI300X via ROCm
- Gemma 3 27B accessed via Fireworks AI (AMD-hardware hosted)
- ROCm PyTorch backend: `pip install torch --index-url https://download.pytorch.org/whl/rocm6.2`

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/YOUR_USERNAME/twinfit
cd twinfit

# 2. Set environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and add your FIREWORKS_API_KEY

# 3. Run with Docker
docker-compose up --build

# Frontend live at: http://localhost:3000
# Backend live at:  http://localhost:8000
# API docs at:      http://localhost:8000/docs
```

## Run Locally (without Docker)

**Backend**
```bash
cd backend
cp .env.example .env          # add your FIREWORKS_API_KEY
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev                   # http://localhost:3000
```

> No `FIREWORKS_API_KEY`? The backend runs in mock mode — canned garment analysis and a placeholder try-on image, so the full UI flow still works for demos.

## API Endpoints

### Size Recommendation
```
POST /api/size/recommend
{
  "height_cm": 165, "weight_kg": 60,
  "chest_cm": 88, "waist_cm": 72, "hip_cm": 96,
  "brand": "myntra", "category": "kurta"
}
```

### Garment Analysis (Gemma AI)
```
POST /api/garment/analyze
{ "image_url": "https://..." }
```

### Virtual Try-On
```
POST /api/tryon/start
{ "user_photo_b64": "...", "garment_image_url": "...", "garment_category": "kurta" }

GET /api/tryon/status/{job_id}
```

## Market Context

- India fashion e-commerce: $21.6B (2025), growing at 24% CAGR
- Fashion return rate in India: 25–35%
- India virtual try-on CAGR: >30% (fastest globally)
- Target: 2,000+ D2C brands on Myntra Rising Stars + Shopify India sellers

## Demo

[Link to deployed demo]

## Team

[Your name] — Builder
# TWIN-FIT
