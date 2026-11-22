import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from app.core.settings import Settings
from app.models.job import Job, JobStatus
from app.models.video import Video
from app.services.video_editing import EditDependencies, make_edit_handler
from app.workers.runner import run_job
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import FakeQueue, FakeStorage, bearer

from ml.dna.errors import VideoTooLong
from ml.edit.cuts import Word

A = bearer("token-a")
UPLOAD = {"filename": "raw-take.mp4", "content_type": "video/mp4", "size_bytes": 2_000_000}
EDIT = {
    "caption_style": "karaoke",
    "cut_silences": True,
    "progress_bar": True,
    "hook_overlay": True,
    "hook_text": "Sab se crispy?",
}
FFMPEG = shutil.which("ffmpeg")


def _make_clip(path: Path) -> bytes:
    assert FFMPEG is not None
    subprocess.run(  # noqa: S603
        [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=360x640:r=25:d=4",
         "-f", "lavfi", "-i", "sine=f=330:d=4", "-shortest", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )  # fmt: skip
    return path.read_bytes()


def _upload(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession], data: bytes
) -> UUID:
    video_id = UUID(client.post("/api/v1/videos/upload-url", json=UPLOAD, headers=A).json()["video"]["id"])

    async def key() -> str:
        async with factory() as session:
            return (await session.execute(select(Video.source_r2_key))).scalar_one()

    storage.put(asyncio.run(key()), data)
    return video_id


def _run(
    factory: async_sessionmaker[AsyncSession], storage: FakeStorage, job_id: UUID, transcribe: Any
) -> Job:
    handler = make_edit_handler(EditDependencies(transcribe=transcribe, storage=storage))

    async def run() -> Job:
        await run_job(factory, Settings(ffmpeg_path=FFMPEG or "ffmpeg"), job_id, handler, final_attempt=True)
        async with factory() as session:
            job = await session.get(Job, job_id)
            assert job is not None
            return job

    return asyncio.run(run())


def test_upload_url_creates_a_video(client: TestClient) -> None:
    response = client.post("/api/v1/videos/upload-url", json=UPLOAD, headers=A)

    assert response.status_code == 201
    body = response.json()
    assert body["video"]["title"] == "raw-take"
    assert body["video"]["output_url"] is None
    assert "videos/" in body["upload_url"]


def test_edit_needs_the_upload_first(client: TestClient, queue: FakeQueue) -> None:
    video_id = client.post("/api/v1/videos/upload-url", json=UPLOAD, headers=A).json()["video"]["id"]

    response = client.post(f"/api/v1/videos/{video_id}/edit", json=EDIT, headers=A)

    assert response.status_code == 409
    assert queue.sent == []


@pytest.mark.skipif(FFMPEG is None, reason="FFmpeg is needed for the render")
def test_edit_job_renders_and_stores_the_output(
    client: TestClient,
    queue: FakeQueue,
    storage: FakeStorage,
    factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    video_id = _upload(client, storage, factory, _make_clip(tmp_path / "clip.mp4"))
    started = client.post(f"/api/v1/videos/{video_id}/edit", json=EDIT, headers=A)
    job_id = UUID(started.json()["job_id"])

    def transcribe(_: Path) -> tuple[list[Word], float]:
        return [Word(0.1, 0.8, "Sab"), Word(0.9, 1.2, "se"), Word(3.0, 3.8, "crispy")], 4.0

    job = _run(factory, storage, job_id, transcribe)

    assert queue.sent == [(TaskName.VIDEOS_EDIT, job_id)]
    assert job.status == JobStatus.DONE, job.error
    assert job.result is not None and job.result["removed_silence_s"] == pytest.approx(
        1.55, abs=0.05
    )  # keeps 0-1.35 and 2.85-3.95
    output_keys = [key for key in storage.objects if key.endswith("edited.mp4")]
    assert len(output_keys) == 1 and storage.objects[output_keys[0]][:4] != b""
    video = client.get(f"/api/v1/videos/{video_id}", headers=A).json()
    assert video["output_url"] and video["duration_s"] == job.result["duration_s"]


def test_a_too_long_video_fails_with_a_code(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    video_id = _upload(client, storage, factory, b"not checked here")
    job_id = UUID(client.post(f"/api/v1/videos/{video_id}/edit", json=EDIT, headers=A).json()["job_id"])

    def too_long(_: Path) -> tuple[list[Word], float]:
        raise VideoTooLong("120 s")

    job = _run(factory, storage, job_id, too_long)

    assert (job.status, job.error) == (JobStatus.FAILED, "video_too_long")


def test_videos_are_private_and_deleted_with_the_account(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    video_id = _upload(client, storage, factory, b"raw")

    assert client.get(f"/api/v1/videos/{video_id}", headers=bearer("token-b")).status_code == 404
    assert client.delete("/api/v1/me", headers=A).status_code == 204
    assert storage.objects == {}


@pytest.mark.parametrize("change", [{"caption_style": "comic"}, {"hook_text": "x" * 121}])
def test_bad_edit_options_are_refused(client: TestClient, change: dict[str, object]) -> None:
    video_id = client.post("/api/v1/videos/upload-url", json=UPLOAD, headers=A).json()["video"]["id"]

    assert (
        client.post(f"/api/v1/videos/{video_id}/edit", json={**EDIT, **change}, headers=A).status_code == 422
    )
