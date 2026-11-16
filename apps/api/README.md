# apps/api

FastAPI service and, later, the Celery workers. Structure and API plan are in `docs/backend.md`.

Input: HTTP requests under `/api/v1`. Output: JSON, plus the OpenAPI schema the frontend generates types from.

```
uv sync
uv run fastapi dev apps/api/app/main.py   # http://localhost:8000/api/v1/health
uv run pytest apps/api
```

## Sign-in

Every protected endpoint uses `Depends(get_current_user)`, which checks the `Authorization: Bearer <token>` header against your Supabase project's public keys.

Set `SUPABASE_URL` (for example `https://your-project.supabase.co`) in `.env`, and turn on **asymmetric JWT signing keys** in the Supabase dashboard. Without them Supabase publishes no keys and every token is rejected.

| Status | Code | Meaning |
|---|---|---|
| 401 | `not_authenticated` | No token sent |
| 401 | `invalid_token` | Token expired, forged, anonymous, or for another project |
| 503 | `auth_unavailable` | Supabase's keys could not be fetched |
| 503 | `auth_not_configured` | `SUPABASE_URL` is not set |

## Database

Set `DATABASE_URL` in `.env`, for example `postgresql+asyncpg://fyp:<password>@localhost:5432/fyp`. Then:

```
uv run alembic -c apps/api/alembic.ini upgrade head
uv run alembic -c apps/api/alembic.ini revision --autogenerate -m "describe the change"
```

Change tables only through new migrations, and never edit a merged one (`rules.md` 3.8). Tests run the real migration on a temporary SQLite file.

## Me endpoints

| Endpoint | What it does |
|---|---|
| `GET /api/v1/me` | Identity from the token, plus the saved profile, or `null` before onboarding |
| `PUT /api/v1/me/profile` | Creates or updates the onboarding profile |
| `DELETE /api/v1/me` | Deletes this user's rows. Safe to repeat |

The user always comes from the verified token, so no endpoint can reach another user's data. Email and name are read from the token and never stored here.

## Jobs

Long work (imports, DNA, scripts) runs in Celery workers, never in a request handler (`docs/backend.md`, Jobs).

1. The endpoint writes a `jobs` row as `queued`, commits, and sends the task by name. It answers `202 {"job_id": ...}`.
2. A worker runs the task through `app/workers/runner.py`, which sets `running`, then `done` with a result or `failed` with a stable error code.
3. The client polls `GET /api/v1/jobs/{id}`. Someone else's job answers 404, the same as a missing one.

Errors are codes, never exception text, because exception text can hold tokens or user data. `TransientJobError` retries with backoff. `JobFailure` fails at once.

Set `REDIS_URL` (for example `redis://localhost:6379/0`), then start a worker from `apps/api`:

```
uv run celery -A app.workers.celery_app worker --queues default,ai -l info
```

Without `REDIS_URL`, endpoints that start jobs answer `503 jobs_not_configured`.

## LLM calls

Every LLM call goes through `app/services/llm.py`. `LlmClient.complete` checks this month's spend in `llm_calls` against `LLM_MONTHLY_BUDGET_USD` before calling, then records tokens and cost. Prompt and reply text are never stored or logged.

`LLM_PROVIDER=openai_compatible` covers OpenRouter (`LLM_BASE_URL=https://openrouter.ai/api/v1`) and Gemini's OpenAI-compatible endpoint. Copy the per-million-token prices from the provider's price page into `LLM_INPUT_USD_PER_MILLION_TOKENS` and `LLM_OUTPUT_USD_PER_MILLION_TOKENS`. Without them the client refuses to start, because the budget guard can't work.

Errors: `LlmUnavailable` (timeouts, 429, 5xx) is worth retrying. `LlmRequestRejected` and `LlmBadResponse` are not. `LlmBudgetExceeded` stops all calls until the next month.
