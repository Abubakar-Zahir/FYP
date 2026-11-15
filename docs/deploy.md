# deploy.md

How to host the app. The frontend runs on Vercel. The API (and later the Celery workers) runs in Docker Compose on one VPS, behind Caddy for HTTPS. Postgres and Auth run on Supabase. Video goes to Cloudflare R2. Plan from `docs/backend.md`, Deployment.

```
Browser ──> Vercel (Next.js)
   │
   └──HTTPS──> VPS: Caddy :443 ──> api:8000 ──> Supabase Postgres
                                       └──> redis (inside the VPS only)
```

The production stack was tested locally on 2026-11-11 (HTTPS, HTTP to HTTPS redirect, CORS, migrations from the container). It has not been deployed to a real server yet.

## 1. Accounts to create

Each person creates these with the team's shared email. Never put the passwords in the repo or in chat.

| Service | What for | Cost |
|---|---|---|
| Supabase | Postgres with pgvector, and Auth | Free tier. Free projects pause after about a week with no activity |
| Vercel | Frontend | Hobby tier is free |
| VPS (Hetzner, DigitalOcean or similar) | API, Redis, later workers | About USD 5 to 10 per month for 2 vCPU, 4 GB. `backend.md` asks for 4 vCPU, 8 GB once video workers run |
| Domain | HTTPS for the API, and the Meta app redirect URL | About USD 10 per year |
| Cloudflare R2 | Video files | Free tier is 10 GB. Not needed until uploads exist |

Prices are rough estimates, so check them before you pay. Everything together must stay under USD 30 per month (`CLAUDE.md`).

## 2. Supabase

1. Create a project. Pick the region closest to the VPS.
2. **Database > Extensions:** turn on `vector`.
3. **Project Settings > API > JWT Keys:** switch to asymmetric signing keys. The API checks tokens with the public keys and rejects all of them otherwise (`apps/api/README.md`).
4. **Authentication > Providers:** turn on Email and Google.
5. **Authentication > URL Configuration:** set the Site URL to your Vercel URL.
6. Copy the **Session pooler** connection string from **Connect**. Change `postgresql://` to `postgresql+asyncpg://`. Use the session pooler, not the transaction pooler: the transaction pooler does not work with asyncpg's prepared statements. Check this against Supabase's current docs.

## 3. VPS

Use Ubuntu 24.04 LTS. Log in with an SSH key, not a password.

```bash
# Docker Engine and the compose plugin, from Docker's official docs for Ubuntu
# https://docs.docker.com/engine/install/ubuntu/

# Firewall: SSH, HTTP and HTTPS only
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

Note: Docker publishes ports by writing its own firewall rules, which skip ufw. Only Caddy publishes ports in `docker-compose.prod.yml`, so Redis and the API stay private.

## 4. Domain

Add an `A` record, for example `api.yourdomain.com`, pointing at the VPS IP. Caddy gets the HTTPS certificate on first start, but only once DNS points at the server.

## 5. Deploy the API

On the VPS:

```bash
git clone <repo-url> fyp && cd fyp
cp infra/.env.prod.example infra/.env.prod
nano infra/.env.prod          # API_DOMAIN, DATABASE_URL, SUPABASE_URL, CORS_ORIGINS
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod up -d --build
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod run --rm api \
  alembic -c apps/api/alembic.ini upgrade head
curl https://api.yourdomain.com/api/v1/health      # {"status":"ok",...}
```

`CORS_ORIGINS` is a JSON list, for example `["https://your-app.vercel.app"]`.

To update after merging to `main`:

```bash
git pull
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod up -d --build
# run the alembic command above if the PR added a migration
```

## 6. Deploy the frontend on Vercel

1. **Add New > Project:** import the GitHub repo.
2. **Root Directory:** `apps/web`. Vercel finds Next.js and the pnpm workspace by itself.
3. Environment variables:

| Name | Value now | Value once the frontend uses the real API |
|---|---|---|
| `NEXT_PUBLIC_USE_MOCKS` | `true` | `false` |
| `NEXT_PUBLIC_API_BASE_URL` | empty | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | empty | Supabase Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | empty | Supabase publishable key |

4. Deploy. Each push to `main` deploys again, and each PR gets a preview URL.

The repo pins `pnpm@12.11.2` in `package.json`. If the Vercel install step fails on the pnpm version, set `ENABLE_EXPERIMENTAL_COREPACK=1` in the project's environment variables. This is not tested yet.

Until the frontend is connected to Supabase and the API, the hosted site is the clickable prototype on mock data. That is enough for the landing page and pilot recruitment.

## 7. Check it works

- [ ] `https://api.yourdomain.com/api/v1/health` returns `ok`
- [ ] `http://` redirects to `https://`
- [ ] `https://api.yourdomain.com/api/v1/me` returns 401 without a token (not 503, which means Supabase isn't configured)
- [ ] The Vercel URL loads the landing page, and `/dashboard` shows mock data
- [ ] Port 6379 and 8000 are not reachable from outside: `nc -zv <vps-ip> 6379` fails

## Not set up yet

- Celery workers and beat: add them to `docker-compose.prod.yml` when the first worker lands (P1-03).
- Sentry, R2 lifecycle rules and backups (`backend.md`, Deployment).
- Automatic deploy from CI. Deploys are manual `git pull` for now.
