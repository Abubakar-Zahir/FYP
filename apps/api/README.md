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
