"""Rate limits on writes (rules.md 6.4: rate limit auth and job endpoints).

A fixed window per caller: the sign-in token's hash when there is one, otherwise the client
IP. Reads are not limited. Instagram connect gets a tighter limit, because each call reaches
Meta. Redis keeps the counts when it is configured, so all API processes share them. If Redis
fails, the request goes through and the failure is logged: a broken counter must not lock
every creator out.
"""

import hashlib
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

WINDOW_S = 60
WRITE_LIMIT = 60
INSTAGRAM_LIMIT = 10
LIMITED_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
INSTAGRAM_PREFIX = "/api/v1/instagram/"
KEY_PREFIX = "rate:"


class Counter(Protocol):
    async def hit(self, key: str, window_s: int) -> int: ...


class MemoryCounter:
    """Per process. Fine for tests and a single API process."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._counts: dict[str, tuple[int, float]] = {}

    async def hit(self, key: str, window_s: int) -> int:
        now = self._clock()
        count, started = self._counts.get(key, (0, now))
        if now - started >= window_s:
            count, started = 0, now
        self._counts[key] = (count + 1, started)
        return count + 1


class RedisCounter:
    def __init__(self, url: str) -> None:
        import redis.asyncio

        self._redis = redis.asyncio.from_url(url)

    async def hit(self, key: str, window_s: int) -> int:
        bucket = int(time.time() // window_s)
        name = f"{key}:{bucket}"
        count = int(await self._redis.incr(name))
        if count == 1:
            await self._redis.expire(name, window_s)
        return count


@dataclass(frozen=True)
class Rule:
    name: str
    limit: int


def rule_for(request: Request) -> Rule | None:
    if request.method not in LIMITED_METHODS:
        return None
    if request.url.path.startswith(INSTAGRAM_PREFIX):
        return Rule("instagram", INSTAGRAM_LIMIT)
    return Rule("write", WRITE_LIMIT)


def caller_key(request: Request) -> str:
    """Never the raw token: only a short hash of it reaches Redis."""
    authorization = request.headers.get("authorization", "")
    if authorization:
        return "t:" + hashlib.sha256(authorization.encode()).hexdigest()[:24]
    return "ip:" + (request.client.host if request.client else "unknown")


def _limited(rule: Rule) -> JSONResponse:
    body = {
        "error": {
            "code": "rate_limited",
            "message": "Too many requests. Wait a minute and try again.",
            "details": {"limit": rule.limit, "window_s": WINDOW_S},
        }
    }
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body, headers={"Retry-After": str(WINDOW_S)}
    )


def make_middleware(
    counter: Counter,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        rule = rule_for(request)
        if rule is not None:
            try:
                count = await counter.hit(f"{KEY_PREFIX}{rule.name}:{caller_key(request)}", WINDOW_S)
            except Exception:
                logger.exception("Rate limit counter failed. Letting the request through")
                count = 0
            if count > rule.limit:
                return _limited(rule)
        return await call_next(request)

    return middleware
