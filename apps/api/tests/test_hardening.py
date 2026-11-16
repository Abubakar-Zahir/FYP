import asyncio
from collections.abc import Iterator

import pytest
from app.core.rate_limit import INSTAGRAM_LIMIT, WRITE_LIMIT, MemoryCounter
from app.core.security import get_token_verifier
from app.core.settings import Settings
from app.main import create_app
from app.workers.queue import get_job_queue
from fastapi.testclient import TestClient
from tests.support import FakeQueue, FakeVerifier, bearer


@pytest.fixture
def limited() -> Iterator[TestClient]:
    app = create_app(
        # database_url and redis_url set to None, so a local .env never reaches the test.
        Settings(
            supabase_url="https://p.supabase.co",
            cors_origins=["http://localhost:3000"],
            database_url=None,
            redis_url=None,
        ),
        MemoryCounter(),
    )
    app.dependency_overrides[get_token_verifier] = FakeVerifier
    queue = FakeQueue()
    app.dependency_overrides[get_job_queue] = lambda: queue
    with TestClient(app) as client:
        yield client


def test_writes_are_limited_per_caller_and_say_when_to_retry(limited: TestClient) -> None:
    statuses = [
        limited.post("/api/v1/comments/sync", headers=bearer("token-a")).status_code
        for _ in range(WRITE_LIMIT + 1)
    ]

    blocked = limited.post("/api/v1/comments/sync", headers=bearer("token-a"))
    other_user = limited.post("/api/v1/comments/sync", headers=bearer("token-b"))

    assert statuses[-1] == 429 and statuses[-2] != 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert blocked.headers["Retry-After"] == "60"
    assert other_user.status_code != 429


def test_instagram_has_a_tighter_limit(limited: TestClient) -> None:
    codes = [
        limited.post("/api/v1/instagram/import", headers=bearer("token-a")).status_code
        for _ in range(INSTAGRAM_LIMIT + 1)
    ]

    assert codes[-1] == 429 and 429 not in codes[:-1]


def test_reads_are_not_limited(limited: TestClient) -> None:
    codes = {limited.get("/api/v1/health").status_code for _ in range(WRITE_LIMIT + 5)}

    assert codes == {200}


def test_a_blocked_response_still_has_cors_headers(limited: TestClient) -> None:
    headers = {**bearer("token-a"), "Origin": "http://localhost:3000"}
    for _ in range(WRITE_LIMIT):
        limited.post("/api/v1/comments/sync", headers=headers)

    blocked = limited.post("/api/v1/comments/sync", headers=headers)

    assert blocked.status_code == 429
    assert blocked.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_every_response_has_a_request_id(limited: TestClient) -> None:
    assert len(limited.get("/api/v1/health").headers["X-Request-ID"]) == 32
    assert limited.get("/api/v1/health", headers={"X-Request-ID": "abc"}).headers["X-Request-ID"] == "abc"


def test_the_window_resets() -> None:
    now = [0.0]
    counter = MemoryCounter(clock=lambda: now[0])

    first = [asyncio.run(counter.hit("k", 60)) for _ in range(3)]
    now[0] = 61.0

    assert first == [1, 2, 3]
    assert asyncio.run(counter.hit("k", 60)) == 1


def test_sentry_stays_off_without_a_dsn() -> None:
    from app.core.observability import init_sentry

    assert init_sentry(Settings()) is False
