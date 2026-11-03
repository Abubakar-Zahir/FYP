# ml

Plain Python ML code. It takes explicit inputs and returns typed outputs, so the same code runs in notebooks and workers.

It must not import `fastapi`, `celery`, `sqlalchemy` or anything from `apps/`. `tests/test_boundaries.py` enforces this.

```
uv run pytest ml
```
