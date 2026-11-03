# AI Content Intelligence Platform

BS AI final year project, ITU Lahore. Start with `CLAUDE.md`, then `progress.md`.

| Path | What |
|---|---|
| `apps/web` | Next.js app |
| `apps/api` | FastAPI app and Celery workers |
| `ml` | Plain Python ML package |
| `notebooks` | Experiments and training |
| `spikes` | Throwaway experiments that answer one question |
| `infra` | Docker Compose and env examples |
| `docs` | SRS, PRD, backend and frontend specs |

## Setup

You need Node 24, pnpm and [uv](https://docs.astral.sh/uv/).

```
pnpm install && pnpm dev                     # web, http://localhost:3000
uv sync && uv run fastapi dev apps/api/app/main.py   # api, http://localhost:8000
```

For Postgres and Redis, see `infra/README.md`.

## Checks (the same ones CI runs)

```
pnpm lint && pnpm typecheck && pnpm test && pnpm build
pnpm test:e2e
uv run ruff check . && uv run ruff format --check . && uv run mypy apps/api ml && uv run pytest
```
