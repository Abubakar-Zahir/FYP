import asyncio
import json
from typing import Any
from uuid import UUID

import httpx
import httpx2
import pytest
from app.core.settings import LlmProviderName, Settings
from app.models.dna import DnaRecordRow
from app.models.job import Job, JobStatus
from app.models.reel import Reel, ReelSource
from app.models.script import Script
from app.services.script_generation import make_generate_handler
from app.workers.runner import TransientJobError, run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeQueue, bearer

from ml.dna.schema import Beat, DnaRecord, HookType, ReelSignals

A = bearer("token-a")
PROFILE = {
    "role": "creator",
    "niche": "Lahore street food",
    "language_mix": ["english", "roman_urdu"],
    "tone": "Honest reviewer",
    "goals": "Grow to 20K followers",
}
SETTINGS = Settings(
    llm_provider=LlmProviderName.OPENAI_COMPATIBLE,
    llm_base_url="https://llm.example/v1",
    llm_model="test-model",
    llm_api_key=SecretStr("sk-test"),
    llm_input_usd_per_million_tokens=2,
    llm_output_usd_per_million_tokens=10,
)
RECORD = DnaRecord(
    signals=ReelSignals(
        length_s=20,
        cut_times_s=[3],
        pacing_cuts_per_10s=0.5,
        detected_language="ur",
        transcript=[],
        hook_candidate_text="",
        keyframe_paths=[],
        model_version="w",
    ),
    hook_type=HookType.LIST,
    hook_text="3 cafes in Gulberg",
    beats=[Beat(label="Hook", start_s=0, end_s=3, description="Promises a list.")],
    overlays=[],
    cta="Save this",
    model_version="m/dna-structure-v1",
)
DRAFT = {
    "hooks": [{"text": f"Hook {n}"} for n in range(5)],
    "angles": [{"title": f"Angle {n}", "summary": "One line."} for n in range(3)],
    "body": [{"beat": b, "line": f"{b} line", "shot": "Close-up"} for b in ("Hook", "Body", "CTA")],
}


def llm_route(answer: object = DRAFT, status: int = 200) -> Any:
    seen: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        if status != 200:
            return httpx.Response(status, json={})
        body = {
            "choices": [{"message": {"content": json.dumps(answer)}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
        return httpx.Response(200, json=body)

    handle.seen = seen  # type: ignore[attr-defined]
    return handle


async def _template(factory: async_sessionmaker[AsyncSession], caption: str | None = None) -> UUID:
    async with factory() as session:
        reel = Reel(user_id=USER_A.id, source=ReelSource.REFERENCE, title="cafes", r2_key="k")
        session.add(reel)
        if caption:
            session.add(
                Reel(user_id=USER_A.id, source=ReelSource.OWN, title="own", ig_media_id="m1", caption=caption)
            )
        await session.flush()
        row = DnaRecordRow(
            user_id=USER_A.id,
            reel_id=reel.id,
            schema_version="1.0",
            hook_type="list",
            hook_text=RECORD.hook_text,
            pacing_cuts_per_10s=0.5,
            length_s=20,
            cta="Save this",
            transcript="",
            record=RECORD.model_dump(mode="json"),
            model_version=RECORD.model_version,
            is_template=True,
        )
        session.add(row)
        await session.commit()
        return row.id


def _start(client: TestClient, template_id: UUID, **change: Any) -> httpx2.Response:
    body = {
        "template_id": str(template_id),
        "topic": "Best chai in Lahore",
        "language": "roman_urdu",
        **change,
    }
    return client.post("/api/v1/scripts/generate", json=body, headers=A)


def _run(factory: async_sessionmaker[AsyncSession], job_id: UUID, route: Any) -> Job:
    handler = make_generate_handler(lambda: httpx.AsyncClient(transport=httpx.MockTransport(route)))
    asyncio.run(run_job(factory, SETTINGS, job_id, handler, final_attempt=False))

    async def read() -> Job:
        async with factory() as session:
            job = await session.get(Job, job_id)
            assert job is not None
            return job

    return asyncio.run(read())


def test_generation_end_to_end(
    client: TestClient, queue: FakeQueue, factory: async_sessionmaker[AsyncSession]
) -> None:
    template_id = asyncio.run(_template(factory, caption="Chai ka asli maza yahan hai"))
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)

    started = _start(client, template_id)
    job_id = UUID(started.json()["job_id"])
    script_id = asyncio.run(_script_id(factory))
    not_ready = client.get(f"/api/v1/scripts/{script_id}", headers=A)
    route = llm_route()
    job = _run(factory, job_id, route)
    script = client.get(f"/api/v1/scripts/{script_id}", headers=A).json()

    assert started.status_code == 202
    assert queue.sent == [(TaskName.SCRIPTS_GENERATE, job_id)]
    assert not_ready.json()["error"]["code"] == "script_not_ready"
    assert (job.status, job.result) == (JobStatus.DONE, {"script_id": str(script_id)})
    assert len(script["hooks"]) == 5
    assert script["hooks"][0] == {"text": "Hook 0", "score": None, "top_factors": []}
    assert [beat["beat"] for beat in script["body"]] == ["Hook", "Body", "CTA"]
    assert script["model_version"] == "openai_compatible:test-model/script-v1"
    prompt = route.seen[0]["messages"][1]["content"]
    assert (
        "Lahore street food" in prompt
        and "Chai ka asli maza yahan hai" in prompt
        and "hook type list" in prompt
    )


async def _script_id(factory: async_sessionmaker[AsyncSession]) -> UUID:
    async with factory() as session:
        return (await session.execute(select(Script.id))).scalar_one()


def test_generation_needs_onboarding_first(
    client: TestClient, queue: FakeQueue, factory: async_sessionmaker[AsyncSession]
) -> None:
    template_id = asyncio.run(_template(factory))

    response = _start(client, template_id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "profile_missing"
    assert queue.sent == []


def test_someone_elses_template_is_not_found(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    template_id = asyncio.run(_template(factory))
    client.put("/api/v1/me/profile", json=PROFILE, headers=bearer("token-b"))

    response = client.post(
        "/api/v1/scripts/generate",
        json={"template_id": str(template_id), "topic": "Chai", "language": "english"},
        headers=bearer("token-b"),
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "change", [{"topic": "x"}, {"language": "french"}], ids=["short-topic", "bad-language"]
)
def test_bad_requests_are_refused(
    client: TestClient, factory: async_sessionmaker[AsyncSession], change: dict[str, Any]
) -> None:
    template_id = asyncio.run(_template(factory))
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)

    assert _start(client, template_id, **change).status_code == 422


def test_a_busy_llm_is_retried(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    template_id = asyncio.run(_template(factory))
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)
    job_id = UUID(_start(client, template_id).json()["job_id"])

    with pytest.raises(TransientJobError):
        _run(factory, job_id, llm_route(status=503))


def test_bad_answers_fail_with_a_code(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    template_id = asyncio.run(_template(factory))
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)
    job_id = UUID(_start(client, template_id).json()["job_id"])

    job = _run(factory, job_id, llm_route({"hooks": []}))

    assert (job.status, job.error) == (JobStatus.FAILED, "script_generation_failed")


def test_unknown_script_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/scripts/00000000-0000-4000-8000-000000000000", headers=A).status_code == 404
