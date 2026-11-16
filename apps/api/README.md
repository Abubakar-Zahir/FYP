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

## Reference reel upload

Reference reels are uploaded files, never links (CLAUDE.md hard constraint 1). The video goes from the browser straight to Cloudflare R2:

1. `POST /api/v1/reels/reference {filename, content_type, size_bytes}` checks the type (`video/mp4` or `video/quicktime`) and size (up to 200 MB), creates the reel row, and returns `upload_url` and `upload_headers`. The URL is signed for that exact type and size and lasts 15 minutes.
2. The browser sends `PUT upload_url` with the file and those headers.
3. The browser calls `POST /api/v1/dna/analyse` (next PR). The worker checks the 90-second limit, because only reading the file can tell it.

`DELETE /api/v1/reels/{id}` deletes the file and the row. `DELETE /me` deletes every stored file first, and refuses with `503 storage_not_configured` rather than leave files behind.

Set `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY` and `R2_BUCKET`. The bucket also needs a CORS rule in the Cloudflare dashboard (R2 > bucket > Settings > CORS policy), or browsers can't upload:

```json
[{ "AllowedOrigins": ["http://localhost:3000", "https://your-app.vercel.app"], "AllowedMethods": ["PUT", "GET"], "AllowedHeaders": ["Content-Type"], "MaxAgeSeconds": 3600 }]
```

## Format DNA

`POST /api/v1/dna/analyse {reel_id}` starts a `dna.analyse` job on the `video` queue. It checks first that the video can be reached: the upload exists for a reference reel, or Instagram is connected for an own reel. The worker then:

1. downloads the video to a temp folder (from R2, or from a fresh Instagram `media_url` for own reels),
2. extracts signals with `ml/dna/extract.py` (Whisper, scene cuts), and rejects reels over 90 s,
3. structures them with `ml/dna/structure.py` through the budget-guarded LLM client,
4. saves one `dna_records` row per reel. Analysing again replaces it.

The job result is `{"dna_id": ...}`. Error codes: `video_too_long`, `video_unreadable`, `upload_missing`, `llm_not_configured`, `llm_budget_exceeded`, `dna_structuring_failed`. `llm_unavailable` and `video_download_failed` are retried.

| Endpoint | What it does |
|---|---|
| `GET /dna?limit&cursor&templates_only` | The DNA library, newest first |
| `GET /dna/{id}` | One record with beats, overlays and transcript |
| `POST /dna/{id}/save-template` | Marks it as a template for script generation |

Keyframes are not kept yet, because nothing reads them until OCR or a vision model is wired. `WHISPER_MODEL` (default `small`) and `DNA_CUT_THRESHOLD` (default 27) tune the extractor.

## Script generation

`POST /api/v1/scripts/generate {template_id, topic, language}` checks that the DNA template is the caller's and that onboarding is done (409 `profile_missing`), creates the script row, and starts `scripts.generate` on the `ai` queue. `language` is `english`, `roman_urdu` or `mixed`.

The worker builds the prompt from the template's structure, the creator's niche, tone and goals, and their latest captions as voice examples (`ml/scripts/generate.py`). It asks for 5 hooks, 3 angles and a full script, retries once on a bad answer, and stores the prompt and model version with the output.

`GET /api/v1/scripts/{id}` returns the script, or `409 script_not_ready` while the job runs. Hooks carry `score: null` until the hook scorer ships in Phase 2.

## Comment intelligence

`POST /api/v1/comments/sync` starts `comments.sync` on the `ai` queue:

1. Labels every comment without a label, using the model at `COMMENT_MODEL_PATH`. That is a `.joblib` file from `ml.comments.train`, or the XLM-R ONNX folder from the notebook, which needs the `nlp` group on the worker. Each label stores the model that made it.
2. Groups the last 90 days of labelled, non-spam comments into up to 8 themes (`ml/comments/themes.py`).
3. Asks the LLM for a short name and a next-video idea per theme. Without an LLM, or if its answer is unreadable, it uses a plain fallback built from the comments themselves.

`GET /api/v1/comments/summary` counts labelled comments by label over 30 days. `GET /api/v1/comments/themes` returns the themes, largest first. Disconnecting Instagram deletes the themes along with the comments.

## Auto-edit

1. `POST /api/v1/videos/upload-url {filename, content_type, size_bytes}` returns a presigned PUT, the same way reference reels upload.
2. `POST /api/v1/videos/{id}/edit {caption_style, cut_silences, progress_bar, hook_overlay, hook_text?, roman_urdu_captions?}` starts `videos.edit` on the `video` queue.
3. The worker downloads the video and gets word timings from Whisper. It cuts pauses longer than 0.6 s, writes word-level captions (`bold_pop`, `karaoke`, `minimal` or `boxed`, in Roman Urdu by default) and burns them in with one FFmpeg run. It can add a progress bar and the hook line, then uploads `edited.mp4` to R2.
4. The job result, and `GET /api/v1/videos/{id}`, give `output_url` (valid for an hour), `duration_s` and `removed_silence_s`.

The `ml/edit/` code holds the cut, caption, transliteration and render logic. The video worker image installs `ffmpeg`. Error codes: `video_too_long`, `video_unreadable`, `upload_missing`, `render_failed`.

## Variants, publishing and the variant learner

1. `POST /api/v1/experiments {video_id, script_id?, variant_count}`: the LLM writes candidates, and the Thompson sampling learner picks which 3 to 5 to test.
2. `POST /api/v1/experiments/{id}/publish`: `experiments.publish` (video queue) checks the publishing quota. Then, for each variant, it burns the hook line onto the edited video, uploads it, and publishes it as a Trial Reel (`TRIAL_GRADUATION_STRATEGY`, default `MANUAL`), with a cover frame chosen by the opener type.
   - If Instagram refuses the first Trial Reel, the account is marked not eligible. Only the learner's top pick goes out, as a normal reel (FR-6.8), because posting every variant publicly would look like duplicate content.
   - A retry never republishes a variant that is already live.
3. Every 30 minutes, the `beat` task `experiments.collect_insights` stores insights at 24 h (preliminary, data can lag) and 72 h. Once every live variant has 72 h numbers, it picks the winner on views, and the learner records whether each variant beat the creator's median views.
4. `POST /api/v1/experiments/{id}/share-winner` records the request and returns `share_instructions`. The API can't share a Trial Reel with followers, so the creator does it in the app.

## Analytics and weekly report

`GET /api/v1/analytics/overview` sums the last 30 days of imported reels against the 30 before. It returns daily views, plus the best formats by hook type (median outlier score).

The weekly report (`ml/reports/weekly.py`) is built from the creator's own data with plain rules, no LLM:
- wins and losses against the creator's usual views;
- comment themes and their ideas;
- the variant learner's findings once a feature has 3 or more tests and wins more than half.

The `beat` service builds it every Monday at 06:00 UTC. `POST /api/v1/reports/weekly` rebuilds it now, and `GET /api/v1/reports/weekly` returns the latest one.
