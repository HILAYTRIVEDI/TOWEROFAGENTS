# Deployment Guide

This guide covers a **split deployment**: the Next.js frontend on **Vercel** and
the FastAPI backend on a **Hostinger VPS**. Supabase stays on your existing
managed cloud project and is not self-hosted.

## Architecture at a glance

| Piece | Where it runs | Notes |
| --- | --- | --- |
| `apps/web` (Next.js 15) | **Vercel** | Self-contained; the only pnpm workspace package |
| `apps/api` (FastAPI + `band-agent`) | **Hostinger VPS** | Long-running uvicorn process plus the standalone Band supervisor |
| Supabase (Postgres / pgvector / Storage) | **Managed Supabase cloud** | Do not self-host; reuse your existing project |

> **Hostinger plan requirement:** use a **Hostinger VPS** (or KVM/Cloud plan with
> SSH + Docker). Shared/Business hosting cannot run this backend — FastAPI/uvicorn
> is a persistent async process, and the `band-agent` supervisor holds an open
> WebSocket. Neither is supported on shared PHP hosting.

---

## 1. Backend on a Hostinger VPS

The `apps/api/Dockerfile` already runs
`uvicorn main:app --host 0.0.0.0 --port 8000`, and `docker-compose.yml` defines
both the `api` and `band-agent` services from the same image. Docker is the
cleanest path.

### 1.1 Install Docker

SSH into the VPS (Ubuntu) and install Docker + the Compose plugin:

```bash
curl -fsSL https://get.docker.com | sh
```

### 1.2 Clone and configure

```bash
git clone https://github.com/HILAYTRIVEDI/<repo>.git
cd <repo>
cp .env.example .env
nano .env   # fill in real Supabase / AIML / Band credentials
```

**CORS is what makes the split work.** `core/config.py` reads `api_cors_origins`
(env var `API_CORS_ORIGINS`, comma-separated). It defaults to
`http://localhost:3000`, which will block your Vercel domain. Set it to your
real frontend origins:

```text
API_CORS_ORIGINS=https://your-app.vercel.app,https://yourdomain.com
```

Keep secrets (especially `SUPABASE_SERVICE_ROLE_KEY`) only in this VPS `.env`.
Never commit them and never expose them to browser code.

### 1.3 Start the backend services

Bring up only the backend — the frontend lives on Vercel, so do **not** start the
`web` service here:

```bash
docker compose up -d --build api band-agent
```

- `api` — the FastAPI request path.
- `band-agent` — the standalone Band supervisor. Live Band integration is not
  served by the API request path (`BandSDKClient` raises `NotImplementedError`);
  it runs as this separate process and only activates with `BAND_MODE=sdk` plus
  real credentials. Leave it in mock mode otherwise.

### 1.4 Put HTTPS in front of it

The Vercel site is served over HTTPS, so browsers refuse to call a plain `http://`
backend (mixed content). Point a subdomain (e.g. `api.yourdomain.com`) at the VPS
IP and terminate TLS. Caddy gives automatic Let's Encrypt certificates:

```caddy
# /etc/caddy/Caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8000
}
```

Verify the backend is live:

- `https://api.yourdomain.com/health` returns OK
- `https://api.yourdomain.com/docs` loads the OpenAPI UI

---

## 2. Frontend on Vercel

`apps/web` is self-contained with its own `package-lock.json`.

1. **New Project → import the GitHub repo.**
2. **Root Directory: `apps/web`** (critical — this is the monorepo subdir).
3. Framework preset: **Next.js** (auto-detected). Build command `next build`.
4. Add **Environment Variables** (Production):

   ```text
   NEXT_PUBLIC_API_BASE_URL = https://api.yourdomain.com
   API_BASE_URL             = https://api.yourdomain.com
   NEXT_PUBLIC_DEFAULT_ORG_ID = <your org uuid>
   ```

   Both URL variables are required. Per `apps/web/lib/api.ts`, server components
   (such as the report page) read `API_BASE_URL`, while browser code reads
   `NEXT_PUBLIC_API_BASE_URL`. Point both at the same Hostinger HTTPS URL.

5. Deploy. Once the final Vercel domain is known, ensure it is included in the
   backend `API_CORS_ORIGINS`, then re-run `docker compose up -d` on the VPS.

---

## 3. Gotchas specific to this repo

- **`band-agent` is a separate process**, not part of the API request path. It
  must run on the VPS alongside `api`, and only does live Band work with
  `BAND_MODE=sdk` + credentials.
- **Do not start the `web` service on the VPS.** Specify `api band-agent`
  explicitly so you are not double-hosting the frontend.
- **Secrets** live only in the VPS `.env` and the Vercel dashboard.
  `SUPABASE_SERVICE_ROLE_KEY` must never be a `NEXT_PUBLIC_*` variable.
- **Supabase migrations** must be applied to your managed project before first
  run (see `supabase/`).

---

## 4. Post-deploy checklist

- [ ] `https://api.yourdomain.com/health` returns OK over HTTPS
- [ ] Vercel domain is listed in `API_CORS_ORIGINS` on the VPS
- [ ] Frontend loads and can reach the backend (no CORS / mixed-content errors)
- [ ] Supabase credentials valid; migrations applied
- [ ] `band-agent` running (mock or sdk as intended)
- [ ] No secrets committed or exposed to the browser
