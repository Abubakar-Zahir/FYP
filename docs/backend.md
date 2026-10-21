# backend.md

One FastAPI service, one Celery worker pool, Postgres and Redis. All heavy work is a Celery job that calls into the plain Python `ml/` package.

## Architecture

```
Browser (Next.js)
   | HTTPS, Supabase JWT
   v
FastAPI (apps/api)  ---->  Postgres + pgvector
   | enqueue                 ^
   v                         |
Redis  ---->  Celery workers ---> ml/ package (DNA, scorer, bandit, comments)
                 |-----------> R2 (video), FFmpeg
                 |-----------> Instagram API, LLM API, Pexels API
```

Request handlers stay thin: validate, check ownership, write a row, enqueue a job, return. Services hold the business logic. Workers hold the long work.

## Folder structure

```
apps/api/
  app/
    main.py
    core/             settings, security, logging, errors
    db/               session, base, migrations (alembic/)
    models/           SQLAlchemy models
    schemas/          Pydantic request and response models
    api/v1/           routers by resource
    services/         business logic (instagram, llm, storage, scripts...)
    workers/          Celery app and task modules
  tests/
ml/
  dna/                extractor, schema, hook classifier
  scoring/            hook scorer, features
  bandit/             Thompson sampling, simulator
  comments/           normaliser, classifier, themes
  common/             data loading, metrics, seeds
```

`ml/` imports nothing from `apps/`, FastAPI, Celery or SQLAlchemy. Workers pass plain typed inputs and store the outputs.

## Data model (core tables)

| Table | Key fields |
|---|---|
| `users` | id (Supabase uid), role, niche, language_mix, tone, goals |
| `ig_accounts` | user_id, ig_user_id, encrypted_token, scopes, token_expires_at, account_type |
| `reels` | ig_account_id, ig_media_id, caption, posted_at, source (own or reference), r2_key |
| `reel_metrics` | reel_id, views, reach, saves, shares, watch_time, fetched_at |
| `dna_records` | reel_id, schema_version, hook_type, pacing, beats (json), overlays (json), cta, length_s, outlier_score, embedding (vector) |
| `dna_templates` | user_id, dna_record_id, name |
| `scripts` | user_id, template_id, topic, language, hooks (json), angles (json), body, model_version |
| `hook_scores` | script_id, hook_text, score, top_factors (json), model_version |
| `videos` | user_id, r2_key, duration_s, status |
| `edit_jobs` | video_id, options (json), output_r2_key, status |
| `experiments` | video_id, ig_account_id, strategy, created_at |
| `variants` | experiment_id, hook_line, opener, caption, ig_container_id, is_trial, status |
| `variant_insights` | variant_id, window (24h or 72h), views, reach, saves, shares |
| `bandit_state` | ig_account_id, feature, alpha, beta, updated_at |
| `comments` | reel_id, ig_comment_id, text, language |
| `comment_labels` | comment_id, label, source (human, model), model_version |
| `comment_themes` | ig_account_id, theme, size, example_comment_ids |
| `weekly_reports` | user_id, week_start, content (json) |
| `jobs` | id, user_id, type, status, progress, result (json), error, created_at |

Comments and tokens are user data. Deleting a user removes rows and R2 objects.

## API surface (v1)

All under `/api/v1`. Auth: `Authorization: Bearer <Supabase JWT>`.

| Area | Endpoints |
|---|---|
| Me | `GET /me`, `PUT /me/profile`, `DELETE /me` (delete all data) |
| Instagram | `GET /instagram/connect` (start OAuth), `GET /instagram/callback`, `DELETE /instagram/account`, `POST /instagram/import` (job) |
| Reels | `GET /reels`, `GET /reels/{id}`, `POST /reels/reference` (upload reference file), `GET /reels/{id}/metrics` |
| DNA | `POST /dna/analyse` (job), `GET /dna`, `GET /dna/{id}`, `POST /dna/{id}/save-template`, `GET /dna/clusters` |
| Scripts | `POST /scripts/generate` (job), `GET /scripts/{id}`, `POST /hooks/score` |
| Editing | `POST /videos/upload-url`, `POST /videos/{id}/edit` (job), `GET /videos/{id}/edit/{job_id}` |
| Variants | `POST /experiments` (create variants), `POST /experiments/{id}/publish` (job), `GET /experiments/{id}`, `POST /experiments/{id}/share-winner` |
| Comments | `GET /comments/themes`, `GET /comments/summary`, `POST /comments/sync` (job) |
| Reports | `GET /reports/weekly`, `GET /analytics/overview` |
| Jobs | `GET /jobs/{id}` |

Response conventions: `202 {job_id}` for async work, standard error shape, cursor pagination for lists. Full examples go in the OpenAPI schema, which the frontend reads.

## Instagram integration

1. Use Instagram API with Instagram Login. Expected permissions: basic profile, content publish, insights, comments. Confirm exact names and the account type needed for publishing in the week 1 spike.
2. Publishing flow: create container (`media_type=REELS`, `trial_params` for Trial Reels), poll status until finished, then publish. Respect the publishing rate limit and check usage before each publish.
3. If the account is not eligible for Trial Reels, publish a normal reel and mark the variant `is_trial=false` (FR-6.8).
4. Pull insights per variant at 24 h and 72 h with scheduled jobs.
5. Tokens: encrypt before storing (AES-GCM or Fernet, key from env). Refresh before expiry. Never log them.
6. Dev mode first with pilot creators added as testers. Submit for app review early.
7. Business Discovery API only for public metrics. No scraping.

## Jobs

1. Every job writes a `jobs` row: `queued`, `running`, `done`, `failed`, with `progress` and `error`.
2. Tasks are idempotent and retry with backoff. A failed job never blocks the UI.
3. Separate queues: `video` (FFmpeg, Whisper, heavy), `ai` (LLM calls), `default` (imports, insights). Video workers use limited concurrency to protect the CPU.
4. Time limits on every task. Clean temp files in `finally`.
5. Beat schedule: insights at 24 h and 72 h, weekly report, token refresh.

## ML integration

| Component | Called by | Notes |
|---|---|---|
| DNA extractor | `dna.analyse` task | Whisper, PySceneDetect, keyframes, vision LLM or OCR, LLM structuring into the DNA schema |
| Hook scorer | `hooks/score` | Embeddings and LightGBM. Return score and top 3 SHAP factors. Model loaded once per worker |
| Variant learner | `experiments` services | Thompson sampling over variant features. State in `bandit_state`. Shared prior across creators |
| Comment classifier | `comments.sync` task | Normalise Roman Urdu, classify, then cluster themes with BERTopic |
| Script generation | `scripts.generate` task | LLM API. Grounded by DNA record and retrieved examples of the creator's captions |

Trained models are stored on Hugging Face Hub or R2 with a version string. Every prediction row stores `model_version`.

LLM access goes through one `services/llm.py` wrapper so the provider can be swapped (OpenRouter, Gemini, Claude). The wrapper records tokens and cost, and enforces a monthly budget guard.

## Auto-edit pipeline

1. Upload to R2 through a presigned URL. Max 90 s, vertical.
2. Extract audio, run Whisper with word timestamps.
3. Transliterate Urdu script output to Roman Urdu when the creator asked for it.
4. Detect silences and cut them. Filler word removal is a later step.
5. Burn word-level captions with FFmpeg using ASS subtitles in the chosen style.
6. Optional: add B-roll from Pexels matched to transcript, frame, progress bar, hook text overlay.
7. Write the output to R2 and return a signed URL for preview.

Target: a 60 s clip finishes under 5 minutes on CPU.

## Configuration

One `Settings` class (`pydantic-settings`). Main variables:

```
DATABASE_URL, REDIS_URL
SUPABASE_JWT_SECRET (or JWKS URL)
TOKEN_ENCRYPTION_KEY
INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_REDIRECT_URI
R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET
LLM_PROVIDER, LLM_API_KEY, LLM_MONTHLY_BUDGET_USD
PEXELS_API_KEY
SENTRY_DSN
```

`infra/.env.example` lists names only.

## Deployment

1. One VPS (4 vCPU, 8 GB RAM or better) running Docker Compose: api, worker-video, worker-ai, beat, redis. Postgres on Supabase.
2. Caddy or Nginx in front with HTTPS.
3. Sentry for errors. Structured logs to stdout.
4. Backups: Supabase daily backup. R2 lifecycle rule to delete temp edits after 7 days.

## Backend done criteria for any endpoint

Schema defined and in OpenAPI, ownership check, error shape, tests (success, validation error, forbidden), docs updated, mock handler in the frontend removed.
