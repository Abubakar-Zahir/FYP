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

Set `REDIS_URL` (for example `redis://localhost:6379/0`), then start a worker from the repo root, so it can import both `app` and `ml`:

```
PYTHONPATH=apps/api:. uv run celery -A app.workers.celery_app worker --queues default,ai -l info
PYTHONPATH=apps/api:. uv run --group video celery -A app.workers.celery_app worker --queues video --concurrency 1 -l info
PYTHONPATH=apps/api:. uv run celery -A app.workers.celery_app beat -l info
```

On Windows, use `;` instead of `:` and add `--pool=solo` to the workers.

Without `REDIS_URL`, endpoints that start jobs answer `503 jobs_not_configured`.

## LLM calls

Every LLM call goes through `app/services/llm.py`. `LlmClient.complete` checks this month's spend in `llm_calls` against `LLM_MONTHLY_BUDGET_USD` before calling, then records tokens and cost. Prompt and reply text are never stored or logged.

`LLM_PROVIDER=openai_compatible` covers OpenRouter (`LLM_BASE_URL=https://openrouter.ai/api/v1`) and Gemini's OpenAI-compatible endpoint. Copy the per-million-token prices from the provider's price page into `LLM_INPUT_USD_PER_MILLION_TOKENS` and `LLM_OUTPUT_USD_PER_MILLION_TOKENS`. Without them the client refuses to start, because the budget guard can't work.

Errors: `LlmUnavailable` (timeouts, 429, 5xx) is worth retrying. `LlmRequestRejected` and `LlmBadResponse` are not. `LlmBudgetExceeded` stops all calls until the next month.

## Instagram

Uses the Instagram API with Instagram Login (`app/services/instagram.py`, ported from `spikes/instagram/`).

1. `GET /api/v1/instagram/connect` returns `authorize_url`. The web app sends the browser there.
2. Instagram redirects to `INSTAGRAM_REDIRECT_URI`, the web app's `/connect/instagram` page, with `code` and `state`.
3. That page calls `POST /api/v1/instagram/callback`. The API checks that `state` was signed for the same user within 10 minutes, swaps the code for a long-lived token, stores it encrypted, and starts the reel import job (`202`).

| Endpoint | What it does |
|---|---|
| `GET /instagram/connect` | Authorize URL with a signed, expiring state |
| `POST /instagram/callback` | Connects the account and starts the import job |
| `POST /instagram/import` | Starts another import job. 404 `instagram_not_connected` without an account |
| `DELETE /instagram/account` | Disconnects and deletes the stored token. Safe to repeat |

Tokens are encrypted with Fernet before they reach the database (`app/core/crypto.py`, rules.md 6.2). Set `TOKEN_ENCRYPTION_KEY` to a key from:

```
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Changing the key makes stored tokens unreadable, and every creator has to reconnect. `DELETE /me` also removes the Instagram account and the user's jobs.

## Reel import

`instagram.import` (default queue) reads the last 50 reels with their insights and comments, and upserts them, so running it again never duplicates anything. It then sets each reel's outlier score: its views over the account's median, or `null` with fewer than 5 reels (`ml/dna/outlier.py`).

`GET /api/v1/reels?limit=&cursor=&source=` lists reels newest first. Pass `next_cursor` back as `cursor`. Metrics are `null` when Instagram has none yet.

A daily `beat` task refreshes tokens that expire within 10 days. Disconnecting deletes imported reels and comments. Uploaded reference reels stay until the user deletes their account.
