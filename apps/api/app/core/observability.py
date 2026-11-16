"""Error tracking and request logs (NFR-12: structured logs, error tracking).

Sentry starts only when SENTRY_DSN is set. It never gets personal data or request bodies,
because bodies hold profiles, comments and captions (rules.md 6.6). Each request gets an id,
returned in X-Request-ID and logged with the path, status and time taken, but no user data.
"""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.settings import Settings

logger = logging.getLogger("app.requests")

REQUEST_ID_HEADER = "X-Request-ID"
TRACES_SAMPLE_RATE = 0.0  # errors only; the free tier is small


def init_sentry(settings: Settings) -> bool:
    if settings.sentry_dsn is None:
        return False
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn.get_secret_value(),
        send_default_pii=False,
        max_request_body_size="never",
        traces_sample_rate=TRACES_SAMPLE_RATE,
        environment=settings.environment,
        release=settings.api_version,
    )
    return True


async def request_log(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
    started = time.perf_counter()
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": round((time.perf_counter() - started) * 1000, 1),
        },
    )
    return response
