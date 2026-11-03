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
