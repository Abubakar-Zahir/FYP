import asyncio
import json
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from app.core.crypto import TokenCipher
from app.core.settings import Settings
from app.models.experiment import BanditBelief, Experiment, ExperimentStatus, Variant, VariantStatus
from app.models.instagram_account import InstagramAccount
from app.models.job import Job, JobStatus
from app.models.reel import Reel, ReelSource
from app.models.video import Video
from app.services import insights
from app.services.publishing import PublishDependencies, make_publish_handler
from app.workers.runner import run_job
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeStorage, bearer

KEY = Fernet.generate_key().decode()
CIPHER = TokenCipher(KEY)
SETTINGS = Settings(token_encryption_key=SecretStr(KEY))
IG = "1784"
A = bearer("token-a")


class FakeInstagram:
    """Answers the publishing and insights calls. `refuse_trials` mimics an ineligible account."""

    def __init__(self, refuse_trials: bool = False, quota_usage: int = 1) -> None:
        self.refuse_trials = refuse_trials
        self.quota_usage = quota_usage
        self.containers: list[dict[str, Any]] = []
        self.published: list[str] = []
        self.views = {"m0": 900, "m1": 4000, "m2": 1500}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path.removeprefix("/v26.0/")
        if path == f"{IG}/content_publishing_limit":
            return httpx.Response(
                200, json={"data": [{"quota_usage": self.quota_usage, "config": {"quota_total": 50}}]}
            )
        if path == f"{IG}/media":
            body = json.loads(request.content)
            if "trial_params" in body and self.refuse_trials:
                return httpx.Response(400, json={"error": {"message": "Trial reels not available"}})
            self.containers.append(body)
            return httpx.Response(200, json={"id": f"c{len(self.containers) - 1}"})
        if path.startswith("c"):
            return httpx.Response(200, json={"status_code": "FINISHED"})
        if path == f"{IG}/media_publish":
            media = f"m{len(self.published)}"
            self.published.append(json.loads(request.content)["creation_id"])
            return httpx.Response(200, json={"id": media})
        if path.endswith("/insights"):
            media = path.split("/")[0]
            return httpx.Response(
                200, json={"data": [{"name": "views", "values": [{"value": self.views[media]}]}]}
            )
        if path.startswith("m"):
            return httpx.Response(200, json={"permalink": f"https://instagram.com/reel/{path}"})
        return httpx.Response(404, json={"error": {"message": f"unexpected {path}"}})


def _render(source: Path, output: Path, hook: str) -> None:
    shutil.copyfile(source, output)


async def _setup(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage, eligible: bool | None = None
) -> UUID:
    storage.put("k/edited.mp4", b"edited video")
    async with factory() as session:
        session.add(
            InstagramAccount(
                user_id=USER_A.id,
                ig_user_id=IG,
                username="ayesha",
                account_type="MEDIA_CREATOR",
                encrypted_token=CIPHER.encrypt("token"),
                token_expires_at=datetime.now(UTC) + timedelta(days=50),
                scopes="",
                trial_reels_eligible=eligible,
            )
        )
        video = Video(
            user_id=USER_A.id, title="Chai", source_r2_key="k/source.mp4", output_r2_key="k/edited.mp4"
        )
        session.add(video)
        await session.flush()
        experiment = Experiment(user_id=USER_A.id, video_id=video.id, status=ExperimentStatus.DRAFT)
        session.add(experiment)
        await session.flush()
        for index, label in enumerate("ABC"):
            session.add(
                Variant(
                    experiment_id=experiment.id,
                    user_id=USER_A.id,
                    label=label,
                    hook_line=f"Hook {label}",
                    hook_style=["question", "story", "list"][index],
                    opener="x",
                    opener_type=["face", "product", "text"][index],
                    caption=f"Caption {label}",
                    caption_length="short",
                )
            )
        for views in (1000, 1200, 2000):
            session.add(
                Reel(
                    user_id=USER_A.id,
                    source=ReelSource.OWN,
                    title="r",
                    ig_media_id=f"own{views}",
                    views=views,
                )
            )
        await session.commit()
        return experiment.id


async def _job(factory: async_sessionmaker[AsyncSession], experiment_id: UUID) -> UUID:
    async with factory() as session:
        job = Job(
            user_id=USER_A.id,
            type="experiments.publish",
            subject_id=experiment_id,
            status="queued",
            progress=0,
        )
        session.add(job)
        await session.commit()
        return job.id


def _publish(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage, ig: FakeInstagram, experiment_id: UUID
) -> Job:
    async def no_wait(_: float) -> None:
        return None

    dependencies = PublishDependencies(
        http_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(ig)),
        storage=storage,
        render_hook=_render,
        sleep=no_wait,
    )

    async def run() -> Job:
        job_id = await _job(factory, experiment_id)
        await run_job(factory, SETTINGS, job_id, make_publish_handler(dependencies), final_attempt=True)
        async with factory() as session:
            job = await session.get(Job, job_id)
            assert job is not None
            return job

    return asyncio.run(run())


async def _variants(factory: async_sessionmaker[AsyncSession]) -> dict[str, Variant]:
    async with factory() as session:
        return {v.label: v for v in (await session.execute(select(Variant))).scalars()}


async def _account(factory: async_sessionmaker[AsyncSession]) -> InstagramAccount:
    async with factory() as session:
        return (await session.execute(select(InstagramAccount))).scalar_one()


def test_variants_go_out_as_trial_reels(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage))
    ig = FakeInstagram()

    job = _publish(factory, storage, ig, experiment_id)

    assert job.status == JobStatus.DONE, job.error
    assert job.result == {"experiment_id": str(experiment_id), "live": 3, "trial": True}
    variants = asyncio.run(_variants(factory))
    assert all(v.status == VariantStatus.LIVE and v.is_trial and v.permalink for v in variants.values())
    assert [c["trial_params"] for c in ig.containers] == [{"graduation_strategy": "MANUAL"}] * 3
    assert [c["thumb_offset"] for c in ig.containers] == [500, 2000, 0]
    assert [c["caption"] for c in ig.containers] == ["Caption A", "Caption B", "Caption C"]
    assert len([key for key in storage.objects if "/experiments/" in key]) == 3
    assert asyncio.run(_account(factory)).trial_reels_eligible is True


def test_without_trial_reels_only_the_top_pick_goes_out_as_a_normal_reel(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage))
    ig = FakeInstagram(refuse_trials=True)

    job = _publish(factory, storage, ig, experiment_id)

    assert job.result is not None and job.result["trial"] is False
    variants = asyncio.run(_variants(factory))
    assert (variants["A"].status, variants["A"].is_trial) == (VariantStatus.LIVE, False)
    assert {variants["B"].error, variants["C"].error} == {"trial_reels_unavailable"}
    assert len(ig.published) == 1
    assert asyncio.run(_account(factory)).trial_reels_eligible is False


def test_a_full_quota_publishes_nothing(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage))
    ig = FakeInstagram(quota_usage=49)

    job = _publish(factory, storage, ig, experiment_id)

    assert (job.status, job.error) == (JobStatus.FAILED, "publish_quota_reached")
    assert ig.published == []


def test_running_again_never_republishes_live_variants(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage))
    ig = FakeInstagram()
    _publish(factory, storage, ig, experiment_id)

    second = _publish(factory, storage, ig, experiment_id)

    assert len(ig.published) == 3
    assert second.status == JobStatus.DONE
    assert second.result is not None and second.result["live"] == 3


def test_insights_pick_the_winner_and_teach_the_learner(
    client: TestClient, factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage))
    ig = FakeInstagram()
    _publish(factory, storage, ig, experiment_id)

    async def collect(now: datetime) -> dict[str, int]:
        async with factory() as session, httpx.AsyncClient(transport=httpx.MockTransport(ig)) as http:
            return await insights.collect(session, http, CIPHER, now)

    after_day = asyncio.run(collect(datetime.now(UTC) + timedelta(hours=25)))
    after_three_days = asyncio.run(collect(datetime.now(UTC) + timedelta(hours=73)))

    assert after_day == {"insights": 3, "winners": 0}
    assert after_three_days == {"insights": 3, "winners": 1}
    body = client.get(f"/api/v1/experiments/{experiment_id}", headers=A).json()
    winner = next(v for v in body["variants"] if v["id"] == body["winner_variant_id"])
    assert (winner["label"], body["status"]) == ("B", "done")  # B had 4,000 views
    assert {item["window"] for item in winner["insights"]} == {"24h", "72h"}
    assert client.post(f"/api/v1/experiments/{experiment_id}/share-winner", headers=A).json()[
        "share_instructions"
    ]

    async def beliefs() -> int:
        async with factory() as session:
            return int((await session.execute(select(func.count()).select_from(BanditBelief))).scalar_one())

    # 3 features x 3 values, for the creator and for the shared prior.
    assert asyncio.run(beliefs()) == 2 * (3 + 3 + 1)


def test_publish_endpoint_refuses_a_published_experiment(
    client: TestClient, factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage))
    _publish(factory, storage, FakeInstagram(), experiment_id)

    response = client.post(f"/api/v1/experiments/{experiment_id}/publish", headers=A)

    assert response.status_code == 409


@pytest.mark.parametrize("eligible", [False])
def test_a_known_ineligible_account_skips_trials(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage, eligible: bool
) -> None:
    experiment_id = asyncio.run(_setup(factory, storage, eligible=eligible))
    ig = FakeInstagram()

    _publish(factory, storage, ig, experiment_id)

    assert "trial_params" not in ig.containers[0]
    assert len(ig.published) == 1
