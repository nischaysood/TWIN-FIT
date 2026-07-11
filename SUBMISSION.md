# TwinFit — Submission Kit (deadline: July 11, 9:45 IST)

## Project title
TwinFit — AI Virtual Try-On & Size Intelligence for Indian Fashion

## One-liner
A one-line embed that lets any fashion retailer add AI size recommendation and
virtual try-on to their product pages — attacking India's 25-35% return rate.

## Description (paste into lablab submission)

Indian fashion e-commerce loses billions to returns — 25-35% of orders come
back, mostly because of fit. Shoppers can't tell if an M at Zara is an M at
Myntra, and they can't see the garment on their own body.

TwinFit fixes both, as a B2B SaaS retailers integrate with ONE line of code:

1. **Size Intelligence** — brand-calibrated size charts (H&M, Zara, Myntra +
   generic) scored against the shopper's measurements. Returns a size,
   confidence %, fit notes tuned for Indian ethnic wear, and a return-risk
   flag the retailer can act on.

2. **AI Garment Analysis** — a vision LLM reads the product image and extracts
   category, sleeve, fit, fabric, and color automatically. No catalog
   integration work for the retailer.

3. **Virtual Try-On** — IDM-VTON (SDXL-based diffusion try-on) renders the
   shopper's own photo wearing the exact garment, preserving face, pose, and
   body. Runs on AMD MI300X via ROCm — PyTorch's ROCm backend runs the CUDA
   codebase unmodified.

**Retailer integration is two attributes:**
```html
<script src="https://twinfit.app/widget.js" data-brand="myntra" defer></script>
<img src="product.jpg" data-twinfit>
```
A "Try It On" button appears under the product image; TwinFit opens in a modal
with the garment pre-loaded and analysis already running.

**Architecture:** Next.js widget + app → FastAPI backend → engine cascade:
IDM-VTON on AMD GPU → IDM-VTON fallback → FLUX Kontext fallback. Async job
queue, graceful degradation, engine transparency badge on every result.

**Market:** India fashion e-comm $21.6B growing 24% CAGR; 2,000+ D2C brands on
Myntra Rising Stars + Shopify India as initial wedge. A 20% return reduction
pays for TwinFit many times over.

**Roadmap (this is a company, not a weekend project):**
- **Stage 1 — Shopify App (next 60 days):** theme app extension injects the
  try-on button on every product page with zero merchant code; Shopify Billing
  handles subscriptions. One listing = distribution to every clothing store
  on Shopify. The widget shown in this demo is the exact component the
  extension ships.
- **Stage 2 — Myntra/AJIO seller integrations + white-label API** for larger
  D2C brands.
- **Stage 3 — fit-data flywheel:** every try-on and every avoided return
  trains better India-specific size models — the data moat.

## Tech stack tags
FastAPI · Next.js · IDM-VTON · Stable Diffusion XL · AMD MI300X · ROCm ·
Gemma 3 / vision LLM via Fireworks AI · Tailwind · Docker

## AMD usage statement
- IDM-VTON inference on AMD GPU (hackathon Jupyter instance, ROCm PyTorch)
- Deployment scripts for MI300X droplets included (gpu-server/)
- Gemma 3 27B vLLM/ROCm serving script included (gpu-server/serve_gemma.sh)

---

## Demo video script (3-4 min)

**0:00-0:30 — Problem.** "Every third fashion order in India comes back.
Wrong size, wrong look. Returns cost retailers 25-35% of revenue." Show a
Myntra-style product page. "Shoppers guess. TwinFit ends the guessing."

**0:30-1:00 — The integration.** Show demo-store.html source: highlight the
ONE script tag + data-twinfit attribute. "This is the entire integration.
One line. Watch what the shopper gets."

**1:00-2:30 — The flow (screen recording).** Click Try It On → measurements →
size card ("XL, 78% confidence, LOW return risk — calibrated to Myntra's own
chart") → garment auto-analyzed ("our vision model read the product image
itself — no catalog work") → upload photo → result. Hold on the result image.
"Same face. Same pose. Their body, this garment. This is IDM-VTON, a
diffusion try-on model, running on an AMD GPU with ROCm."

**2:30-3:00 — The badge + architecture.** Point at engine badge. Quick
architecture slide: widget → API → AMD GPU engine cascade. "If the GPU is
busy, we degrade gracefully — the shopper never sees a broken screen."

**3:00-3:30 — Business close.** "$21.6B market, 24% CAGR. 2,000+ D2C brands
we can onboard with a script tag. TwinFit: India's fit problem, solved."

## Submission checklist
- [ ] GitHub repo public, .env NOT committed, README current
- [ ] Demo video recorded + uploaded (YouTube unlisted works for lablab)
- [ ] Live demo: frontend on Vercel / backend on Render — or clearly
      documented local run in README (video is what judges watch)
- [ ] Try-on recorded with "IDM-VTON @ AMD GPU" badge if slot obtained
      (otherwise HuggingFace engine + AMD deployment scripts shown in repo)
- [ ] Team members added on lablab page
- [ ] Submitted BEFORE 9:45 IST — lablab closes hard, submit a draft early
      and update it
