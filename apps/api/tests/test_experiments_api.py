import asyncio
import json
import random
from typing import Any
from uuid import UUID

import httpx
import pytest
from app.core.settings import LlmProviderName, Settings
from app.models.experiment import Experiment, Variant
from app.models.job import Job, JobStatus
from app.models.video import Video
from app.services.experiments import make_create_handler
from app.workers.runner import run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeQueue, FakeStorage, bearer

A = bearer("token-a")
PROFILE = {
    "role": "creator",
    "niche": "Food",
    "language_mix": ["roman_urdu"],
    "tone": "Honest",
    "goals": "Grow to 20K",
}
SETTINGS = Settings(
    llm_provider=LlmProviderName.OPENAI_COMPATIBLE,
    llm_base_url="https://llm.example/v1",
    llm_model="m",
    llm_api_key=SecretStr("k"),
    llm_input_usd_per_million_tokens=1,
    llm_output_usd_per_million_tokens=1,
)
STYLES = ["question", "bold_claim", "story", "list", "question", "story"]


def llm_route(_: httpx.Request) -> httpx.Response:
    candidates = [
        {
            "hook_line": f"Hook {n}",
            "hook_style": STYLES[n],
            "opener": "First frame",
            "opener_type": "face" if n % 2 else "text",
            "caption": f"Caption {n}",
            "hashtags": ["chai"],
        }
        for n in range(6)
    ]
    body = {
        "choices": [{"message": {"content": json.dumps({"candidates": candidates})}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }
    return httpx.Response(200, json=body)


async def _edited_video(factory: async_sessionmaker[AsyncSession], edited: bool = True) -> UUID:
    async with factory() as session:
        video = Video(
            user_id=USER_A.id,
            title="Chai crawl",
            source_r2_key="k/source.mp4",
            output_r2_key="k/edited.mp4" if edited else None,
        )
        session.add(video)
        await session.commit()
        return video.id


def _create(client: TestClient, factory: async_sessionmaker[AsyncSession], **change: Any) -> UUID:
    video_id = asyncio.run(_edited_video(factory))
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)
    response = client.post("/api/v1/experiments", json={"video_id": str(video_id), **change}, headers=A)
    assert response.status_code == 202, response.json()
    job_id = UUID(response.json()["job_id"])
    handler = make_create_handler(
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(llm_route)), rng=random.Random(3)
    )

    async def run() -> Job:
        await run_job(factory, SETTINGS, job_id, handler, final_attempt=True)
        async with factory() as session:
            job = await session.get(Job, job_id)
            assert job is not None
            return job

    job = asyncio.run(run())
    assert job.status == JobStatus.DONE, job.error
    assert job.result is not None
    return UUID(job.result["experiment_id"])


def test_creation_picks_variants_and_returns_the_experiment(
    client: TestClient, queue: FakeQueue, factory: async_sessionmaker[AsyncSession]
) -> None:
    experiment_id = _create(client, factory, variant_count=4)

    body = client.get(f"/api/v1/experiments/{experiment_id}", headers=A).json()

    assert queue.sent[0][0] == TaskName.EXPERIMENTS_CREATE
    assert body["video_title"] == "Chai crawl"
    assert body["strategy"] == "thompson_sampling"
    assert body["status"] == "draft"
    assert [variant["label"] for variant in body["variants"]] == ["A", "B", "C", "D"]
    assert len({variant["hook_line"] for variant in body["variants"]}) == 4
    assert all(variant["status"] == "draft" and variant["insights"] == [] for variant in body["variants"])
    assert body["variants"][0]["caption"].endswith("#chai")
    assert body["winner_variant_id"] is None and body["share_instructions"] is None


def test_an_unedited_video_is_refused(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    video_id = asyncio.run(_edited_video(factory, edited=False))

    response = client.post("/api/v1/experiments", json={"video_id": str(video_id)}, headers=A)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "video_not_edited"


@pytest.mark.parametrize("count", [2, 6])
def test_variant_count_must_be_3_to_5(
    client: TestClient, factory: async_sessionmaker[AsyncSession], count: int
) -> None:
    video_id = asyncio.run(_edited_video(factory))

    response = client.post(
        "/api/v1/experiments", json={"video_id": str(video_id), "variant_count": count}, headers=A
    )

    assert response.status_code == 422


def test_share_winner_needs_a_winner(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    experiment_id = _create(client, factory)

    response = client.post(f"/api/v1/experiments/{experiment_id}/share-winner", headers=A)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "no_winner_yet"


def test_experiments_are_private_listed_and_deleted_with_the_account(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    experiment_id = _create(client, factory)

    assert client.get(f"/api/v1/experiments/{experiment_id}", headers=bearer("token-b")).status_code == 404
    assert [item["id"] for item in client.get("/api/v1/experiments", headers=A).json()["items"]] == [
        str(experiment_id)
    ]
    assert client.delete("/api/v1/me", headers=A).status_code == 204

    async def counts() -> tuple[int, int]:
        async with factory() as session:
            experiments = (await session.execute(select(func.count()).select_from(Experiment))).scalar_one()
            variants = (await session.execute(select(func.count()).select_from(Variant))).scalar_one()
            return int(experiments), int(variants)

    assert asyncio.run(counts()) == (0, 0)


def test_deleting_the_account_deletes_rendered_variant_files(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    experiment_id = _create(client, factory)

    async def render_variants() -> None:
        async with factory() as session:
            rows = (
                await session.execute(select(Variant).where(Variant.experiment_id == experiment_id))
            ).scalars()
            for variant in rows:
                variant.r2_key = f"variants/{variant.label}.mp4"
                storage.objects[variant.r2_key] = b"rendered"
            await session.commit()

    asyncio.run(render_variants())
    assert storage.objects

    assert client.delete("/api/v1/me", headers=A).status_code == 204
    assert storage.objects == {}
