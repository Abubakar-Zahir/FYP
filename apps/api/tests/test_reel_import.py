import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import pytest
from app.core.crypto import TokenCipher
from app.core.settings import Settings
from app.models.instagram_account import InstagramAccount
from app.models.job import Job, JobStatus
from app.models.reel import Comment, Reel
from app.services.reel_import import make_import_handler, parse_timestamp, title_from_caption
from app.services.token_refresh import refresh_expiring_tokens
from app.workers.runner import TransientJobError, run_job
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, USER_B, bearer

KEY = Fernet.generate_key().decode()
CIPHER = TokenCipher(KEY)
SETTINGS = Settings(token_encryption_key=SecretStr(KEY))
GRAPH = "https://graph.instagram.com/v26.0"
REEL_IDS = [f"media-{index}" for index in range(6)]
NO_INSIGHTS = "media-5"


def _media() -> list[dict[str, str]]:
    reels = [
        {
            "id": media_id,
            "media_type": "VIDEO",
            "media_product_type": "REELS",
            "caption": f"Reel {index}\nwith a second line",
            "timestamp": f"2026-11-{10 + index:02d}T10:00:00+0000",
        }
        for index, media_id in enumerate(REEL_IDS)
    ]
    return [*reels, {"id": "photo-1", "media_type": "IMAGE", "media_product_type": "FEED"}]


def instagram(request: httpx.Request) -> httpx.Response:
    path = request.url.path.removeprefix("/v26.0/")
    if path == "me/media":
        return httpx.Response(200, json={"data": _media()})
    media_id, _, kind = path.partition("/")
    if kind == "insights":
        if media_id == NO_INSIGHTS:
            return httpx.Response(400, json={"error": {"message": "Not enough data"}})
        index = REEL_IDS.index(media_id)
        values = {
            "views": 1000 * (index + 1),
            "reach": 800,
            "saved": 12,
            "shares": 7,
            "ig_reels_avg_watch_time": 6400,
        }
        return httpx.Response(
            200, json={"data": [{"name": k, "values": [{"value": v}]} for k, v in values.items()]}
        )
    if kind == "comments":
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": f"{media_id}-c{n}", "text": "Ye kahan hai?", "timestamp": None} for n in range(2)
                ]
            },
        )
    return httpx.Response(404, json={"error": {"message": "unexpected"}})


def _handler(route: Any = instagram) -> Any:
    return make_import_handler(lambda: httpx.AsyncClient(transport=httpx.MockTransport(route)))


async def _setup(factory: async_sessionmaker[AsyncSession], *, connected: bool = True) -> UUID:
    async with factory() as session:
        if connected:
            session.add(
                InstagramAccount(
                    user_id=USER_A.id,
                    ig_user_id="1784",
                    username="ayesha.eats.lahore",
                    account_type="MEDIA_CREATOR",
                    encrypted_token=CIPHER.encrypt("long-token"),
                    token_expires_at=datetime.now(UTC) + timedelta(days=50),
                    scopes="instagram_business_basic",
                )
            )
        job = Job(user_id=USER_A.id, type="instagram.import", status=JobStatus.QUEUED, progress=0.0)
        session.add(job)
        await session.commit()
        return job.id


def _run(
    factory: async_sessionmaker[AsyncSession],
    job_id: UUID,
    route: Any = instagram,
    settings: Settings = SETTINGS,
) -> Job:
    asyncio.run(run_job(factory, settings, job_id, _handler(route), final_attempt=False))
    return asyncio.run(_get_job(factory, job_id))


async def _get_job(factory: async_sessionmaker[AsyncSession], job_id: UUID) -> Job:
    async with factory() as session:
        job = await session.get(Job, job_id)
        assert job is not None
        return job


def _count(factory: async_sessionmaker[AsyncSession], model: Any) -> int:
    async def count() -> int:
        async with factory() as session:
            return int((await session.execute(select(func.count()).select_from(model))).scalar_one())

    return asyncio.run(count())


def _reels(factory: async_sessionmaker[AsyncSession]) -> dict[str, Reel]:
    async def read() -> dict[str, Reel]:
        async with factory() as session:
            return {str(reel.ig_media_id): reel for reel in (await session.execute(select(Reel))).scalars()}

    return asyncio.run(read())


def test_import_saves_reels_metrics_and_comments(factory: async_sessionmaker[AsyncSession]) -> None:
    job = _run(factory, asyncio.run(_setup(factory)))

    assert (job.status, job.result) == (JobStatus.DONE, {"reels": 6, "comments": 12})
    reels = _reels(factory)
    assert sorted(reels) == REEL_IDS  # the photo is skipped
    first = reels["media-0"]
    assert (first.title, first.views, first.saves, first.shares) == ("Reel 0", 1000, 12, 7)
    assert first.avg_watch_time_s == 6.4  # Meta reports milliseconds
    assert first.posted_at is not None
    assert _count(factory, Comment) == 12


def test_a_reel_without_insights_keeps_null_metrics(factory: async_sessionmaker[AsyncSession]) -> None:
    _run(factory, asyncio.run(_setup(factory)))

    missing = _reels(factory)[NO_INSIGHTS]
    assert (missing.views, missing.outlier_score) == (None, None)


def test_outlier_scores_compare_with_the_accounts_median(factory: async_sessionmaker[AsyncSession]) -> None:
    _run(factory, asyncio.run(_setup(factory)))

    reels = _reels(factory)
    # Views 1000..5000, median 3000.
    assert reels["media-4"].outlier_score == pytest.approx(1.67)
    assert reels["media-2"].outlier_score == 1.0


def test_importing_again_updates_instead_of_duplicating(factory: async_sessionmaker[AsyncSession]) -> None:
    _run(factory, asyncio.run(_setup(factory)))
    second_job = asyncio.run(_setup(factory, connected=False))

    _run(factory, second_job)

    assert _count(factory, Reel) == 6
    assert _count(factory, Comment) == 12


def test_import_without_an_account_fails_with_a_code(factory: async_sessionmaker[AsyncSession]) -> None:
    job = _run(factory, asyncio.run(_setup(factory, connected=False)))

    assert (job.status, job.error) == (JobStatus.FAILED, "instagram_not_connected")


def test_instagram_being_down_is_retried(factory: async_sessionmaker[AsyncSession]) -> None:
    job_id = asyncio.run(_setup(factory))

    with pytest.raises(TransientJobError):
        _run(factory, job_id, lambda _: httpx.Response(503, json={}))

    job = asyncio.run(_get_job(factory, job_id))
    assert (job.status, job.error) == (JobStatus.QUEUED, "instagram_unavailable")


def test_a_changed_encryption_key_asks_for_a_reconnect(factory: async_sessionmaker[AsyncSession]) -> None:
    other_key = Settings(token_encryption_key=SecretStr(Fernet.generate_key().decode()))

    job = _run(factory, asyncio.run(_setup(factory)), settings=other_key)

    assert (job.status, job.error) == (JobStatus.FAILED, "instagram_reconnect_needed")


def test_reels_list_pages_newest_first(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    _run(factory, asyncio.run(_setup(factory)))

    first = client.get("/api/v1/reels?limit=4", headers=bearer("token-a")).json()
    second = client.get(
        f"/api/v1/reels?limit=4&cursor={first['next_cursor']}", headers=bearer("token-a")
    ).json()

    assert [item["title"] for item in first["items"]] == ["Reel 5", "Reel 4", "Reel 3", "Reel 2"]
    assert [item["title"] for item in second["items"]] == ["Reel 1", "Reel 0"]
    assert second["next_cursor"] is None
    assert first["items"][1]["views"] == 5000
    assert first["items"][0]["views"] is None


def test_reels_are_private(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    _run(factory, asyncio.run(_setup(factory)))

    assert client.get("/api/v1/reels", headers=bearer("token-b")).json() == {"items": [], "next_cursor": None}


def test_a_bad_cursor_is_a_400(client: TestClient) -> None:
    response = client.get("/api/v1/reels?cursor=not-a-cursor", headers=bearer("token-a"))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_cursor"


def test_disconnect_deletes_imported_reels_and_comments(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    _run(factory, asyncio.run(_setup(factory)))

    client.delete("/api/v1/instagram/account", headers=bearer("token-a"))

    assert (_count(factory, Reel), _count(factory, Comment), _count(factory, InstagramAccount)) == (0, 0, 0)


def test_deleting_the_user_removes_reels_and_comments(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    _run(factory, asyncio.run(_setup(factory)))

    client.delete("/api/v1/me", headers=bearer("token-a"))

    assert (_count(factory, Reel), _count(factory, Comment)) == (0, 0)


def test_tokens_close_to_expiry_are_refreshed(factory: async_sessionmaker[AsyncSession]) -> None:
    now = datetime.now(UTC)

    async def scenario() -> tuple[int, str, datetime]:
        async with factory() as session:
            account = InstagramAccount(
                user_id=USER_A.id,
                ig_user_id="1",
                username="a",
                account_type="MEDIA_CREATOR",
                encrypted_token=CIPHER.encrypt("old-token"),
                token_expires_at=now + timedelta(days=3),
                scopes="",
                updated_at=now - timedelta(days=2),
            )
            fresh = InstagramAccount(
                user_id=USER_B.id,
                ig_user_id="2",
                username="b",
                account_type="MEDIA_CREATOR",
                encrypted_token=CIPHER.encrypt("new-token"),
                token_expires_at=now + timedelta(days=3),
                scopes="",
            )
            session.add_all([account, fresh])
            await session.commit()
            route = httpx.MockTransport(
                lambda _: httpx.Response(
                    200, json={"access_token": "refreshed-token", "expires_in": 5_184_000}
                )
            )
            async with httpx.AsyncClient(transport=route) as http:
                refreshed = await refresh_expiring_tokens(session, http, CIPHER, now)
            await session.refresh(account)
            return refreshed, CIPHER.decrypt(account.encrypted_token), account.token_expires_at

    refreshed, token, expires_at = asyncio.run(scenario())

    # The fresh account was updated less than 24 hours ago, so Instagram won't refresh it yet.
    assert refreshed == 1
    assert token == "refreshed-token"  # noqa: S105
    assert expires_at.replace(tzinfo=UTC) > now + timedelta(days=50)


@pytest.mark.parametrize(
    ("caption", "title"),
    [
        (None, "Untitled reel"),
        ("   ", "Untitled reel"),
        ("Best chaat\nin Lahore", "Best chaat"),
        ("x" * 100, "x" * 79 + "…"),
    ],
)
def test_titles_come_from_the_first_caption_line(caption: str | None, title: str) -> None:
    assert title_from_caption(caption) == title


def test_instagram_timestamps_parse_to_utc() -> None:
    assert parse_timestamp("2026-11-10T15:30:00+0500") == datetime(2026, 11, 10, 10, 30, tzinfo=UTC)
    assert parse_timestamp("garbage") is None
    assert parse_timestamp(None) is None
