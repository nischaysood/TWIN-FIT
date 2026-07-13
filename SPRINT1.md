# Sprint 1 — Hosted TwinFit, step by step

The code is done (persistence, storage, API keys, telemetry — all env-gated).
Everything still runs locally with zero config. These steps light up each
SaaS feature by pasting one env var at a time. Do them in order.

## 1. Modal — your own IDM-VTON engine (~1h, mostly waiting)
```bash
pip3 install modal
modal setup                              # browser auth
modal deploy gpu-server/modal_app.py     # image build ~30-40 min, one time
```
Copy the printed URL → `backend/.env`:
```
TRYON_HF_SPACE=https://<you>--twinfit-idm-vton-ui.modal.run
TRYON_ENGINE_LABEL=IDM-VTON @ Modal (serverless GPU)
```
Test: run `python backend/test_e2e.py` — try-on should say engine Modal.

## 2. Neon — Postgres (~10 min)
1. neon.tech → New Project → name `twinfit` → copy the connection string
2. `backend/.env`: `DATABASE_URL=postgresql://...`
3. Restart backend — startup log should say **"SaaS (Postgres) mode"**.
   Tables auto-create; a demo merchant (key `twinfit-demo`) is seeded.

## 3. Cloudflare R2 — image storage (~15 min)
1. dash.cloudflare.com → R2 → Create bucket `twinfit-results`
2. Bucket → Settings → enable public access (r2.dev URL) — copy it
3. R2 → Manage API Tokens → Create (Object Read & Write) — copy keys
4. `backend/.env`:
```
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=twinfit-results
R2_PUBLIC_BASE_URL=https://<bucket-hash>.r2.dev
```
Try-on results now come back as short URLs instead of base64.

## 4. Render — hosted backend (~20 min)
1. render.com → New + → **Blueprint** → connect the GitHub repo
   (`render.yaml` is already in the repo root)
2. Paste env vars in the dashboard: FIREWORKS_API_KEY, DATABASE_URL,
   TRYON_HF_SPACE, HF_TOKEN, R2_* — same values as your local .env
3. Deploy → note the URL, e.g. `https://twinfit-api.onrender.com`
4. Test: `curl https://twinfit-api.onrender.com/health`
   (Free tier sleeps when idle; first request after sleep takes ~30s.)

## 5. Vercel — hosted frontend + widget (~15 min)
1. vercel.com → Add New Project → import the repo → root dir `frontend`
2. Env var: `NEXT_PUBLIC_API_URL=https://twinfit-api.onrender.com`
3. Deploy → you get `https://twinfit-<x>.vercel.app`
4. THE MONEY URL: `https://twinfit-<x>.vercel.app/demo-store.html`
   — live retailer demo, hosted, clickable by anyone.
5. If lablab still allows edits: update the Demo Application URL with it.

## 6. Flip on real auth (when first design partner signs up)
- Render env: `REQUIRE_API_KEY=true`
- Add merchant row (Neon SQL editor):
```sql
INSERT INTO merchants (id, name, api_key, brand_chart, monthly_tryon_quota)
VALUES (gen_random_uuid()::text, 'Partner Store', 'tf_live_<random>', 'myntra', 200);
```
- Their embed: `<script src=".../widget.js" data-brand="myntra" data-key="tf_live_...">`

## Sanity checklist when all done
- [ ] `python backend/test_e2e.py` against the Render URL (edit API= line): 6/6
- [ ] Demo store on Vercel completes a full try-on
- [ ] Neon: `SELECT kind, count(*) FROM events GROUP BY 1;` shows telemetry flowing
- [ ] R2 bucket has PNGs in `tryons/`
- [ ] Modal dashboard shows GPU seconds only during try-ons

Then Sprint 2: Shopify Partners → app scaffold. See ROADMAP.md.
