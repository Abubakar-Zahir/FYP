import asyncio
from pathlib import Path
from uuid import UUID

import pytest
from app.core.settings import Settings
from app.models.job import Job, JobStatus
from app.services.hook_scoring import load_scorer, make_score_handler, scored_hooks
from app.workers.runner import JobFailure, run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeQueue, bearer

from ml.dna.schema import HookType
from ml.scoring.model import HookExample, HookScorer

A = bearer("token-a")


@pytest.fixture
def scorer_path(tmp_path: Path) -> Path:
    examples = [
        HookExample(
            text=("Kahan milti hai?" if n % 2 else "Aaj ka vlog") + f" {n}",
            hook_type=HookType.QUESTION if n % 2 else HookType.STORY,
            creator=f"c{n % 3}",
            outlier_score=3.0 if n % 2 else 1.0,
        )
        for n in range(30)
    ]
    HookScorer.train(examples).save(tmp_path / "scorer")
    return tmp_path / "scorer"


def test_without_a_model_hooks_stay_unscored() -> None:
    assert scored_hooks(None, ["Kya scene hai?"], None) == [
        {"text": "Kya scene hai?", "score": None, "top_factors": []}
    ]
    assert load_scorer(Settings()) is None


def test_with_a_model_hooks_get_scores_and_reasons(scorer_path: Path) -> None:
    scorer = load_scorer(Settings(hook_scorer_path=str(scorer_path)))

    [hook] = scored_hooks(scorer, ["Kahan milti hai sab se achhi chaat?"], HookType.QUESTION)

    assert 0 <= hook["score"] <= 100
    assert hook["top_factors"] and {"label", "impact"} <= set(hook["top_factors"][0])


def test_a_missing_model_folder_fails_with_a_code(tmp_path: Path) -> None:
    with pytest.raises(JobFailure) as raised:
        load_scorer(Settings(hook_scorer_path=str(tmp_path / "nope")))

    assert raised.value.code == "hook_scorer_missing"


def test_score_endpoint_queues_a_job_with_its_payload(
    client: TestClient, queue: FakeQueue, factory: async_sessionmaker[AsyncSession], scorer_path: Path
) -> None:
    response = client.post(
        "/api/v1/hooks/score", json={"hooks": ["Kya ye sach hai?"], "hook_type": "question"}, headers=A
    )

    assert response.status_code == 202
    job_id = UUID(response.json()["job_id"])
    assert queue.sent == [(TaskName.HOOKS_SCORE, job_id)]

    async def run() -> Job:
        await run_job(
            factory,
            Settings(hook_scorer_path=str(scorer_path)),
            job_id,
            make_score_handler(),
            final_attempt=True,
        )
        async with factory() as session:
            job = await session.get(Job, job_id)
            assert job is not None
            return job

    job = asyncio.run(run())
    assert job.status == JobStatus.DONE
    assert job.result is not None and job.result["hooks"][0]["text"] == "Kya ye sach hai?"
    assert job.user_id == USER_A.id


@pytest.mark.parametrize(
    "body", [{"hooks": []}, {"hooks": ["x"] * 11}, {"hooks": ["x"], "hook_type": "nope"}]
)
def test_bad_score_requests_are_refused(client: TestClient, body: dict[str, object]) -> None:
    assert client.post("/api/v1/hooks/score", json=body, headers=A).status_code == 422
