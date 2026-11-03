# apps/api

FastAPI service and, later, the Celery workers. Structure and API plan are in `docs/backend.md`.

Input: HTTP requests under `/api/v1`. Output: JSON, plus the OpenAPI schema the frontend generates types from.

```
uv sync
uv run fastapi dev apps/api/app/main.py   # http://localhost:8000/api/v1/health
uv run pytest apps/api
```
