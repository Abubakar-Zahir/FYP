import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from app.core.settings import LlmProviderName, Settings
from app.models.dna import DnaRecordRow
from app.models.job import Job, JobStatus
from app.models.llm_call import LlmCall
from app.models.reel import Reel, ReelSource
from app.services.dna_analysis import DnaDependencies, make_analyse_handler
from app.workers.runner import TransientJobError, run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeQueue, FakeStorage, bearer

from ml.dna.errors import VideoTooLong
from ml.dna.schema import ReelSignals, TranscriptSegment

A = bearer("token-a")
SETTINGS = Settings(
    llm_provider=LlmProviderName.OPENAI_COMPATIBLE,
    llm_base_url="https://llm.example/v1",
    llm_model="test-model",
    llm_api_key=SecretStr("sk-test"),
    llm_input_usd_per_million_tokens=2,
    llm_output_usd_per_million_tokens=10,
)
SIGNALS = ReelSignals(
    length_s=12.0,
    cut_times_s=[3.0],
    pacing_cuts_per_10s=0.83,
    detected_language="ur",
    transcript=[
        TranscriptSegment(start_s=0.0, end_s=2.8, text=" Sab se crispy chaat kahan hai?"),
        TranscriptSegment(start_s=3.0, end_s=12.0, text="Main ne 10 jagah try ki."),
    ],
    hook_candidate_text="Sab se crispy chaat kahan hai?",
    keyframe_paths=["keyframes/scene_000.jpg"],
    model_version="faster-whisper-small+int8",
)
ANSWER = {
    "hook_type": "question",
    "hook_text": "Sab se crispy chaat kahan hai?",
    "beats": [
        {"label": "Hook", "start_s": 0, "end_s": 3, "description": "Asks a question."},
        {"label": "Payoff", "start_s": 3, "end_s": 12, "description": "Reviews the places."},
    ],
    "cta": "",
}


def llm_route(answer: object = ANSWER, status: int = 200) -> Any:
    def handle(_: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status, json={"error": "busy"})
        body = {
            "choices": [{"message": {"content": json.dumps(answer)}}],
            "usage": {"prompt_tokens": 900, "completion_tokens": 150},
        }
        return httpx.Response(200, json=body)

    return handle


def _fake_extract(seen: list[Path]) -> Any:
    def extract(video: Path, keyframes: Path) -> ReelSignals:
        seen.append(video)
        assert video.read_bytes() == b"fake video bytes"
        return SIGNALS

    return extract


async def _reference_reel(factory: async_sessionmaker[AsyncSession], storage: FakeStorage) -> Reel:
    async with factory() as session:
        reel = Reel(
            user_id=USER_A.id, source=ReelSource.REFERENCE, title="chaat", r2_key="users/a/reference/r.mp4"
        )
        session.add(reel)
        await session.commit()
    storage.put("users/a/reference/r.mp4", b"fake video bytes")
    return reel


async def _job(factory: async_sessionmaker[AsyncSession], reel_id: UUID) -> UUID:
    async with factory() as session:
        job = Job(
            user_id=USER_A.id,
            type=TaskName.DNA_ANALYSE.value,
            subject_id=reel_id,
            status="queued",
            progress=0,
        )
        session.add(job)
        await session.commit()
        return job.id


def _analyse(
    factory: async_sessionmaker[AsyncSession],
    storage: FakeStorage,
    job_id: UUID,
    *,
    extract: Any = None,
    route: Any = None,
    settings: Settings = SETTINGS,
) -> Job:
    dependencies = DnaDependencies(
        extract=extract or _fake_extract([]),
        storage=storage,
        http_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(route or llm_route())),
    )
    asyncio.run(run_job(factory, settings, job_id, make_analyse_handler(dependencies), final_attempt=False))

    async def read() -> Job:
        async with factory() as session:
            job = await session.get(Job, job_id)
            assert job is not None
            return job

    return asyncio.run(read())


def _rows(factory: async_sessionmaker[AsyncSession], model: Any) -> list[Any]:
    async def read() -> list[Any]:
        async with factory() as session:
            return list((await session.execute(select(model))).scalars())

    return asyncio.run(read())


def test_analysis_saves_a_record_and_records_the_llm_cost(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))
    seen: list[Path] = []

    job = _analyse(factory, storage, asyncio.run(_job(factory, reel.id)), extract=_fake_extract(seen))

    assert job.status == JobStatus.DONE, job.error
    [row] = _rows(factory, DnaRecordRow)
    assert job.result == {"dna_id": str(row.id)}
    assert (row.hook_type, row.reel_id, row.length_s) == ("question", reel.id, 12.0)
    assert row.transcript == "Sab se crispy chaat kahan hai? Main ne 10 jagah try ki."
    assert row.record["signals"]["keyframe_paths"] == []  # the temp folder is gone
    assert row.model_version == "openai_compatible:test-model/dna-structure-v1"
    [call] = _rows(factory, LlmCall)
    assert (call.purpose, call.user_id, call.input_tokens) == ("dna.structure", USER_A.id, 900)
    assert len(seen) == 1 and not seen[0].exists()  # the downloaded video is cleaned up


def test_analysing_again_replaces_the_record(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    _analyse(factory, storage, asyncio.run(_job(factory, reel.id)))
    _analyse(factory, storage, asyncio.run(_job(factory, reel.id)))

    assert len(_rows(factory, DnaRecordRow)) == 1


def test_a_long_video_fails_with_a_code(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    def too_long(_: Path, __: Path) -> ReelSignals:
        raise VideoTooLong("120 s")

    job = _analyse(factory, storage, asyncio.run(_job(factory, reel.id)), extract=too_long)

    assert (job.status, job.error) == (JobStatus.FAILED, "video_too_long")
    assert _rows(factory, DnaRecordRow) == []


def test_a_missing_upload_fails_with_a_code(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))
    storage.objects.clear()

    job = _analyse(factory, storage, asyncio.run(_job(factory, reel.id)))

    assert (job.status, job.error) == (JobStatus.FAILED, "upload_missing")


def test_a_busy_llm_is_retried(factory: async_sessionmaker[AsyncSession], storage: FakeStorage) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    with pytest.raises(TransientJobError):
        _analyse(factory, storage, asyncio.run(_job(factory, reel.id)), route=llm_route(status=503))


def test_two_bad_llm_answers_fail_without_saving(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    job = _analyse(
        factory, storage, asyncio.run(_job(factory, reel.id)), route=llm_route({"hook_type": "nope"})
    )

    assert (job.status, job.error) == (JobStatus.FAILED, "dna_structuring_failed")
    assert _rows(factory, DnaRecordRow) == []
    assert len(_rows(factory, LlmCall)) == 2  # the retry is paid for and counted too


def test_no_llm_settings_fail_with_a_code(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    job = _analyse(factory, storage, asyncio.run(_job(factory, reel.id)), settings=Settings())

    assert (job.status, job.error) == (JobStatus.FAILED, "llm_not_configured")


def test_analyse_endpoint_queues_a_job_for_an_uploaded_reel(
    client: TestClient, queue: FakeQueue, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    response = client.post("/api/v1/dna/analyse", json={"reel_id": str(reel.id)}, headers=A)

    assert response.status_code == 202
    assert queue.sent == [(TaskName.DNA_ANALYSE, UUID(response.json()["job_id"]))]


def test_analyse_endpoint_refuses_before_the_upload_finishes(
    client: TestClient, queue: FakeQueue, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))
    storage.objects.clear()

    response = client.post("/api/v1/dna/analyse", json={"reel_id": str(reel.id)}, headers=A)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "upload_missing"
    assert queue.sent == []


def test_analyse_endpoint_hides_other_users_reels(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))

    response = client.post("/api/v1/dna/analyse", json={"reel_id": str(reel.id)}, headers=bearer("token-b"))

    assert response.status_code == 404


def test_library_detail_and_templates(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))
    _analyse(factory, storage, asyncio.run(_job(factory, reel.id)))

    library = client.get("/api/v1/dna", headers=A).json()
    [item] = library["items"]
    detail = client.get(f"/api/v1/dna/{item['id']}", headers=A).json()
    saved = client.post(f"/api/v1/dna/{item['id']}/save-template", headers=A).json()

    assert (item["title"], item["source"], item["hook_type"]) == ("chaat", "reference", "question")
    assert [beat["label"] for beat in detail["beats"]] == ["Hook", "Payoff"]
    assert detail["outlier_score"] is None
    assert (item["is_template"], saved["is_template"]) == (False, True)
    assert client.get("/api/v1/dna?templates_only=true", headers=A).json()["items"][0]["id"] == item["id"]
    assert client.get(f"/api/v1/dna/{item['id']}", headers=bearer("token-b")).status_code == 404
    assert client.get("/api/v1/reels", headers=A).json()["items"][0]["hook_type"] == "question"


def test_deleting_the_reel_deletes_its_dna(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel = asyncio.run(_reference_reel(factory, storage))
    _analyse(factory, storage, asyncio.run(_job(factory, reel.id)))

    assert client.delete(f"/api/v1/reels/{reel.id}", headers=A).status_code == 204

    async def count() -> int:
        async with factory() as session:
            return int((await session.execute(select(func.count()).select_from(DnaRecordRow))).scalar_one())

    assert asyncio.run(count()) == 0
