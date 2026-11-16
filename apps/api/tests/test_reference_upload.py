import asyncio
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from app.core.settings import Settings
from app.models.reel import Reel
from app.schemas.uploads import MAX_UPLOAD_BYTES
from app.services.reels import title_from_filename
from app.services.storage import R2Storage, build_storage, get_optional_storage, get_storage
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeStorage, bearer

A = bearer("token-a")
UPLOAD: dict[str, Any] = {
    "filename": "chaat-review.mp4",
    "content_type": "video/mp4",
    "size_bytes": 4_000_000,
}


def _reels(factory: async_sessionmaker[AsyncSession]) -> list[Reel]:
    async def read() -> list[Reel]:
        async with factory() as session:
            return list((await session.execute(select(Reel))).scalars())

    return asyncio.run(read())


def test_upload_creates_a_reference_reel_and_a_signed_url(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    response = client.post("/api/v1/reels/reference", json=UPLOAD, headers=A)

    assert response.status_code == 201
    body = response.json()
    assert body["reel"]["source"] == "reference"
    assert body["reel"]["title"] == "chaat-review"
    assert body["upload_headers"] == {"Content-Type": "video/mp4"}
    assert "size=4000000" in body["upload_url"]
    [reel] = _reels(factory)
    assert reel.r2_key == f"users/{USER_A.id}/reference/{reel.id}.mp4"


def test_quicktime_keeps_its_extension(client: TestClient, factory: async_sessionmaker[AsyncSession]) -> None:
    client.post("/api/v1/reels/reference", json={**UPLOAD, "content_type": "video/quicktime"}, headers=A)

    assert str(_reels(factory)[0].r2_key).endswith(".mov")


@pytest.mark.parametrize(
    "change",
    [
        {"content_type": "image/png"},
        {"content_type": "video/webm"},
        {"size_bytes": 0},
        {"size_bytes": MAX_UPLOAD_BYTES + 1},
        {"filename": "   "},
    ],
    ids=["image", "webm", "empty", "too-big", "blank-name"],
)
def test_bad_uploads_are_refused(
    client: TestClient, factory: async_sessionmaker[AsyncSession], change: dict[str, Any]
) -> None:
    response = client.post("/api/v1/reels/reference", json={**UPLOAD, **change}, headers=A)

    assert response.status_code == 422
    assert _reels(factory) == []


def test_links_are_not_accepted(client: TestClient) -> None:
    response = client.post(
        "/api/v1/reels/reference", json={**UPLOAD, "url": "https://instagram.com/reel/abc"}, headers=A
    )

    # The extra field is ignored and a file upload URL is returned, never a scrape of the link.
    assert "r2.example" in response.json()["upload_url"]


def test_server_without_storage_says_so(app: FastAPI, client: TestClient) -> None:
    def no_storage() -> None:
        from app.services.storage import storage_not_configured

        raise storage_not_configured()

    app.dependency_overrides[get_storage] = no_storage

    response = client.post("/api/v1/reels/reference", json=UPLOAD, headers=A)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_not_configured"


def test_deleting_a_reference_reel_deletes_the_file(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel_id = client.post("/api/v1/reels/reference", json=UPLOAD, headers=A).json()["reel"]["id"]
    [reel] = _reels(factory)
    storage.put(str(reel.r2_key), b"video")

    assert client.delete(f"/api/v1/reels/{reel_id}", headers=A).status_code == 204
    assert storage.objects == {}
    assert _reels(factory) == []


def test_other_users_reels_cannot_be_deleted(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    reel_id = client.post("/api/v1/reels/reference", json=UPLOAD, headers=A).json()["reel"]["id"]

    assert client.delete(f"/api/v1/reels/{reel_id}", headers=bearer("token-b")).status_code == 404
    assert len(_reels(factory)) == 1


def test_deleting_the_account_deletes_every_uploaded_file(
    client: TestClient, storage: FakeStorage, factory: async_sessionmaker[AsyncSession]
) -> None:
    for _ in range(2):
        client.post("/api/v1/reels/reference", json=UPLOAD, headers=A)
    keys = [str(reel.r2_key) for reel in _reels(factory)]
    for key in keys:
        storage.put(key, b"video")

    assert client.delete("/api/v1/me", headers=A).status_code == 204
    assert sorted(storage.deleted) == sorted(keys)
    assert _reels(factory) == []


def test_account_deletion_refuses_to_leave_files_behind(
    app: FastAPI, client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    client.post("/api/v1/reels/reference", json=UPLOAD, headers=A)
    app.dependency_overrides[get_optional_storage] = lambda: None

    response = client.delete("/api/v1/me", headers=A)

    assert response.status_code == 503
    assert len(_reels(factory)) == 1


@pytest.mark.parametrize(
    ("filename", "title"),
    [
        ("chaat.mp4", "chaat"),
        ("C:\\Users\\me\\Videos\\clip.mov", "clip"),
        ("../../etc.mp4", "etc"),
        (".mp4", ".mp4"),
    ],
)
def test_titles_drop_folders_and_extensions(filename: str, title: str) -> None:
    assert title_from_filename(filename) == title


def test_r2_upload_urls_are_signed_for_type_and_size() -> None:
    storage = R2Storage("account123", "access-key", "secret-key", "fyp-videos")

    url = urlparse(storage.upload_url("users/u/reference/r.mp4", "video/mp4", 1234))

    assert url.netloc == "account123.r2.cloudflarestorage.com"
    assert url.path == "/fyp-videos/users/u/reference/r.mp4"
    query = parse_qs(url.query)
    assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
    assert "content-length" in query["X-Amz-SignedHeaders"][0]
    assert "content-type" in query["X-Amz-SignedHeaders"][0]


def test_storage_is_off_until_every_r2_setting_is_present() -> None:
    assert build_storage(Settings(r2_account_id="a", r2_access_key="b", r2_bucket="c")) is None
    full = Settings(r2_account_id="a", r2_access_key="b", r2_secret_key=SecretStr("s"), r2_bucket="c")
    assert isinstance(build_storage(full), R2Storage)
