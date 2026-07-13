# TwinFit — Company Roadmap (post-hackathon)

Constraint that shapes everything: **₹0 cash budget. Free tiers + $30 Modal credits.**
Every choice below is the best thing that costs nothing.

---

## Sprint 1 (Weeks 1-2) — Backend Hardening → first hosted deployment

Goal: TwinFit runs on the internet, not on a laptop. A real URL a merchant can click.

### 1. Own inference engine on Modal (uses the free credits)
- Deploy `gpu-server/modal_app.py` (already written): `pip install modal && modal setup && modal deploy gpu-server/modal_app.py`
- Set `TRYON_HF_SPACE=<modal-url>`, `TRYON_ENGINE_LABEL=IDM-VTON @ Modal`
- Container auto-sleeps after 5 idle min → credits only burn during actual try-ons
- Budget math: ~$2/hr active GPU → $30 ≈ 15 GPU-hours ≈ 500-900 try-ons. Plenty for demos + design partners.

### 2. Persistence (kill the in-memory job store)
- **Neon Postgres (free tier)**: tables `merchants`, `api_keys`, `tryon_jobs`, `events`
- Jobs survive restarts; judges/merchants never see "job not found"

### 3. Result storage
- **Cloudflare R2 (free 10GB)**: upload try-on PNGs, return short URLs instead of 2MB base64 blobs
- Cuts response sizes ~100x, makes results shareable links

### 4. Multi-tenancy (the actual SaaS part)
- `X-API-Key` header required on all widget-originated calls
- Per-merchant: brand chart config, usage counters (try-ons this month), rate limits
- Usage counters = billing-ready before billing exists

### 5. Hosted deployment
- Backend → **Render free tier** (FastAPI web service; note: sleeps after idle, ~30s cold start — acceptable pre-revenue)
- Frontend + widget.js → **Vercel** (hobby)
- Outcome: `https://twinfit.vercel.app/demo-store.html` — a REAL demo URL (update the lablab submission if edits are still open)

### 6. Telemetry seed (Stage-3 flywheel starts on day 1)
- Log every event to `events` table: size_recommended, garment_analyzed, tryon_started/completed, engine_used, latency, confidence
- Costs nothing now; is the moat later

---

## Sprint 2-4 (Weeks 3-8) — Stage 1: Shopify App

Goal: a clothing store installs TwinFit in 2 clicks without touching code.

- **Shopify Partners account** (free) + dev store
- Scaffold with Shopify CLI (Remix app template)
- **Theme App Extension**: embeds `widget.js` on product pages automatically, reads the product image + title straight from the Shopify product object (no `data-twinfit` needed)
- **Admin settings page**: brand chart selection, on/off toggle, usage dashboard (reads the counters from Sprint 1)
- **Billing API**: $29/mo base + metered per-try-on above a free quota (Shopify handles all payments — no payment infra to build)
- Submit for App Store review (allow 1-4 weeks; use the review time for Stage 2 groundwork)
- Interim distribution while in review: unlisted install links for design partners

**Design partners (parallel, from week 3):** DM 10-20 Indian D2C clothing brands
(Instagram/Shopify stores). Offer free forever-plan for the first 3 in exchange for
feedback + a testimonial. Their product pages become the real demos.

---

## Stage 2 (Months 3-4) — Marketplace sellers & white-label API

- Public REST API + docs (FastAPI auto-docs are 80% there)
- Target Myntra Rising Stars / AJIO sellers who also run their own D2C sites
- White-label mode: retailer's logo/colors on the modal (config per API key)
- Pricing tier for volume (per-1000 try-ons)

## Stage 3 (Months 4+) — The fit-data flywheel

- Post-purchase feedback loop: "Did size M fit?" one-tap email/widget prompt
- Join try-on events + size recs + keep/return outcomes → train India-specific
  size models per brand/category — better than any static size chart
- This data is the defensible asset; everything before it is distribution

---

## Immediate housekeeping (do before Sprint 1)
- [ ] **Rotate the Fireworks API key** (it was pasted in a chat once — 30 seconds at app.fireworks.ai)
- [ ] Repo: add LICENSE, clean commit history if needed, pin a good README screenshot
- [ ] Modal account + deploy (first Sprint-1 task, ~1 hr including image build)
- [ ] Create accounts: Neon, Cloudflare R2, Render, Vercel, Shopify Partners (all free)

## Cost ceiling until first revenue
Modal: $30 credits · Neon/R2/Render/Vercel/Shopify Partners: $0 · **Total cash: $0**
First revenue target: 3 paying Shopify merchants at $29/mo by end of Stage 1.
