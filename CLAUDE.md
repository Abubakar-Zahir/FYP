# CLAUDE.md

Read this file first in every session. Then read `progress.md` to see what is done and what is next.

## Project

AI Content Intelligence Platform, a BS AI final year project at ITU Lahore. A system that breaks viral Instagram reels into a reusable "format DNA", writes scripts in the creator's voice, auto-edits footage, publishes 3 to 5 variants as Instagram Trial Reels, and learns which variant wins per creator. It also turns Roman Urdu and English comments into themes and next-video ideas.

Primary user: Instagram creators (1,000+ followers). Secondary: small brands (light module, v2 for matching).

The project is judged on measured ML results from a 4 to 6 week pilot, not on feature count.

## Team and ownership

Four people. Owners are listed in `prd.md`. Do not edit another owner's module without telling them in the PR.

## Stack (locked)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router), TypeScript strict, Tailwind, shadcn/ui, TanStack Query |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic |
| Jobs | Celery + Redis |
| Database | Postgres (Supabase) with pgvector |
| Auth | Supabase Auth (Google and email). Backend verifies the JWT |
| Video storage | Cloudflare R2 |
| Video processing | FFmpeg |
| ML | Plain Python package in `ml/`. No FastAPI or Celery imports inside it |
| Labelling | Label Studio (self-hosted) |
| Deploy | Frontend on Vercel. Backend, worker, Redis via Docker Compose on one VPS |

## Repo layout

```
apps/web/        Next.js app
apps/api/        FastAPI app and Celery workers
ml/              Pure Python ML code (DNA, scorer, bandit, comments)
notebooks/       Experiments and training. Output goes to ml/ when stable
infra/           docker-compose, env examples, deploy scripts
docs/            frontend.md, backend.md, srs.md, prd.md
```

Root files: `CLAUDE.md`, `progress.md`, `roadmap.md`, `rules.md`.

## Commands

```
# web
pnpm install
pnpm dev
pnpm lint && pnpm typecheck && pnpm test

# api
uv sync
uv run fastapi dev apps/api/app/main.py
uv run ruff check . && uv run ruff format --check .
uv run mypy apps/api ml
uv run pytest

# stack
docker compose -f infra/docker-compose.yml up
```

## How to work in this repo

1. Read `rules.md` before writing code. It is binding.
2. Work on one task from `progress.md`. Keep the PR small (under 400 changed lines where possible).
3. Contract first: the API shape lives in the Pydantic schemas and the generated OpenAPI. The frontend generates its types from it. Do not hand-write API types twice.
4. Do not invent library APIs, Instagram endpoints or permission names. Check the official docs. If unsure, say so in the PR.
5. Ask before adding a dependency. State why the standard library or an existing dependency is not enough.
6. Never commit secrets, tokens, `.env` files, user videos or comment data.
7. Heavy work (Whisper, FFmpeg, model inference, LLM chains) runs in Celery workers, never inside a request handler.
8. When a task is finished, update `progress.md` in the same PR.

## Hard constraints

1. Use only official Instagram APIs. No scraping of other accounts. Reference reels are uploaded files, not links.
2. OAuth tokens are encrypted at rest. Instagram passwords are never stored.
3. Users can disconnect an account and delete all their data.
4. API spend stays under USD 30 per month during the pilot.
5. Everything must run without a guaranteed GPU. Training happens on Colab or Kaggle.
6. Report ML results honestly. No accuracy claims without a held-out test set.

## Definition of done

A task is done when: code is merged to `main` through a reviewed PR, lint, types and tests pass in CI, the behaviour is covered by a test or a written manual check, docs and `progress.md` are updated, and no TODO is left without an issue number.
