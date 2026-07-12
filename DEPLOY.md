# Deployment — frontend (Vercel) + backend (Render)

Live setup: the **Vercel** SPA (`frontend/`) calls the **Render** FastAPI service (`backend/`).
They're different sites, so the `sid` cookie ships as `SameSite=None; Secure` and CORS allows
the Vercel origin with credentials. Provider/service-role keys live **only** in Render env.

> ⚠️ **No rate limiting yet (Phase 6).** A public chat URL lets anonymous visitors spend your
> Anthropic/Voyage credits. Fine for low personal traffic; gate it before wide sharing.

Prerequisites: repo pushed to GitHub; Supabase already provisioned + ingested (Slice 1).

---

## 1. Backend → Render (do first — you need its URL for the frontend)

1. **New → Web Service**, connect the GitHub repo.
2. **Root Directory:** `backend`  ·  **Runtime:** `Docker` (uses `backend/Dockerfile`).
3. **Health Check Path:** `/api/health`.
4. **Environment variables:**
   | Key | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | your key |
   | `VOYAGE_API_KEY` | your key |
   | `SUPABASE_URL` | `https://<project>.supabase.co` |
   | `SUPABASE_SERVICE_ROLE_KEY` | service-role (Secret) key |
   | `ALLOWED_ORIGIN_REGEX` | `https://.*\.vercel\.app` |
   | `COOKIE_SAMESITE` | `none` |
   | `COOKIE_SECURE` | `true` |
   | *(optional)* `CHAT_MODEL`, `RETRIEVAL_TOP_K`, … | overrides |
5. Deploy. Verify: `curl https://<svc>.onrender.com/api/health` → `{"status":"ok","version":"…"}`.

Cold starts: the free tier spins down after inactivity, so the first request may be slow. SSE
still streams (the app sends `X-Accel-Buffering: no`).

## 2. Frontend → Vercel

1. **Add New → Project**, import the same repo.
2. **Root Directory:** `frontend`  ·  Framework preset **Vite** (build `npm run build`, output
   `dist` — auto-detected). `vercel.json` adds the SPA fallback.
3. **Environment variable:** `VITE_API_BASE` = the Render URL from step 1
   (e.g. `https://<svc>.onrender.com`). Set it for Production (and Preview if you want previews
   to hit the same backend).
4. Deploy.

## 3. (Optional) Harden CORS + custom domain

- Add the exact Vercel URL (and any custom domain) to Render `ALLOWED_ORIGINS`
  (comma-separated). The regex already covers `*.vercel.app` preview deploys.
- Custom domain: add in Vercel, then include it in `ALLOWED_ORIGINS`.

---

## Verify end-to-end

Open the Vercel URL → send a starter question. Confirm:

- Tokens **stream in** (not a single blob) and end cleanly.
- DevTools → Network → `POST /api/chat`: response has `Set-Cookie: sid=…; SameSite=None; Secure`
  and **no CORS error**.
- Reload and ask again → the same `sid` cookie is reused (persisted).

## Local pre-push checks

```bash
cd backend && uv run pytest        # 5 pass (cookie test unaffected)
cd ../frontend && npm run build     # tsc + vite green
# optional container smoke test:
docker build -t maas backend/
docker run --rm -e PORT=8000 --env-file backend/.env -p 8000:8000 maas
curl http://localhost:8000/api/health
```

## Redeploys

Both hosts auto-deploy on push to the default branch (and build PR previews). Backend changes
under `backend/`, frontend under `frontend/`.
