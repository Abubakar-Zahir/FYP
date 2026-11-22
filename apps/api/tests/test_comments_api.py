import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest
from app.core.settings import Settings
from app.models.job import Job, JobStatus
from app.models.reel import Comment, CommentTheme, Reel, ReelSource
from app.services.comment_intelligence import load_classifier, make_sync_handler
from app.workers.runner import JobFailure, run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeQueue, bearer

from ml.comments.labels import CommentLabel

A = bearer("token-a")
QUESTIONS = [f"Ye jagah kahan hai bhai {n}" for n in range(20)]
COMPLAINTS = [f"price bohat mehnga hai yaar {n}" for n in range(20)]


class KeywordClassifier:
    """Stands in for a trained model: 'kahan' means question, everything else complaint."""

    name = "keyword-test"

    def predict(self, texts: Sequence[str]) -> list[CommentLabel]:
        return [CommentLabel.QUESTION if "kahan" in text else CommentLabel.COMPLAINT for text in texts]


async def _seed(factory: async_sessionmaker[AsyncSession], texts: list[str]) -> None:
    async with factory() as session:
        reel = Reel(user_id=USER_A.id, source=ReelSource.OWN, title="r", ig_media_id="m")
        session.add(reel)
        await session.flush()
        now = datetime.now(UTC)
        for index, text in enumerate(texts):
            session.add(
                Comment(
                    user_id=USER_A.id, reel_id=reel.id, ig_comment_id=f"c{index}", text=text, posted_at=now
                )
            )
        session.add(
            Comment(
                user_id=USER_A.id,
                reel_id=reel.id,
                ig_comment_id="old",
                text="purana comment kahan",
                posted_at=now - timedelta(days=200),
            )
        )
        await session.commit()


def _run_sync(factory: async_sessionmaker[AsyncSession]) -> Job:
    async def scenario() -> Job:
        async with factory() as session:
            job = Job(
                user_id=USER_A.id, type=TaskName.COMMENTS_SYNC.value, status=JobStatus.QUEUED, progress=0
            )
            session.add(job)
            await session.commit()
        handler = make_sync_handler(
            lambda: httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(500))),
            loader=lambda _: KeywordClassifier(),
        )
        await run_job(factory, Settings(), job.id, handler, final_attempt=False)
        async with factory() as session:
            found = await session.get(Job, job.id)
            assert found is not None
            return found

    return asyncio.run(scenario())


def test_sync_labels_new_comments_and_builds_themes(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    asyncio.run(_seed(factory, QUESTIONS + COMPLAINTS))

    job = _run_sync(factory)

    assert job.status == JobStatus.DONE, job.error
    assert job.result is not None and job.result["labelled"] == 41
    assert job.result["themes"] >= 1
    summary = client.get("/api/v1/comments/summary", headers=A).json()
    assert summary["total"] == 40  # the 200-day-old comment is outside the 30-day window
    assert {item["label"]: item["count"] for item in summary["by_label"]} == {"question": 20, "complaint": 20}
    themes = client.get("/api/v1/comments/themes", headers=A).json()["items"]
    assert themes and themes[0]["examples"] and themes[0]["idea"]


def test_syncing_again_replaces_themes_and_skips_labelled_comments(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    asyncio.run(_seed(factory, QUESTIONS + COMPLAINTS))

    _run_sync(factory)
    second = _run_sync(factory)

    async def count() -> int:
        async with factory() as session:
            return int((await session.execute(select(func.count()).select_from(CommentTheme))).scalar_one())

    assert second.result is not None and second.result["labelled"] == 0
    assert asyncio.run(count()) == second.result["themes"]


def test_sync_endpoint_queues_a_job(client: TestClient, queue: FakeQueue) -> None:
    response = client.post("/api/v1/comments/sync", headers=A)

    assert response.status_code == 202
    assert queue.sent == [(TaskName.COMMENTS_SYNC, UUID(response.json()["job_id"]))]


def test_no_comments_gives_empty_summary_and_themes(client: TestClient) -> None:
    assert client.get("/api/v1/comments/summary", headers=A).json() == {
        "total": 0,
        "period_days": 30,
        "by_label": [],
    }
    assert client.get("/api/v1/comments/themes", headers=A).json() == {"items": [], "next_cursor": None}


def test_themes_are_private(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    asyncio.run(_seed(factory, QUESTIONS + COMPLAINTS))
    _run_sync(factory)

    assert client.get("/api/v1/comments/themes", headers=bearer("token-b")).json()["items"] == []


def test_disconnect_and_delete_remove_themes(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    asyncio.run(_seed(factory, QUESTIONS + COMPLAINTS))
    _run_sync(factory)

    client.delete("/api/v1/instagram/account", headers=A)

    assert client.get("/api/v1/comments/themes", headers=A).json()["items"] == []


@pytest.mark.parametrize(
    ("settings", "code"),
    [
        (Settings(), "comment_model_not_configured"),
        (Settings(comment_model_path="/no/such/model"), "comment_model_missing"),
    ],
    ids=["unset", "missing"],
)
def test_classifier_settings_fail_with_a_code(settings: Settings, code: str) -> None:
    with pytest.raises(JobFailure) as raised:
        load_classifier(settings)

    assert raised.value.code == code
