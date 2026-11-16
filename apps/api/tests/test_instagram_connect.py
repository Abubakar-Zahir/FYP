import asyncio
import time
from collections.abc import Callable, Iterator
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import httpx
import httpx2
import pytest
from app.core.crypto import OAUTH_STATE_MAX_AGE_S, STATE_PREFIX, DecryptionFailed, TokenCipher
from app.core.http import get_http_client
from app.core.settings import Settings, get_settings
from app.models.instagram_account import InstagramAccount
from app.workers.tasks import TaskName
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, USER_B, FakeQueue, bearer

KEY = Fernet.generate_key().decode()
CIPHER = TokenCipher(KEY)
SETTINGS = Settings(
    token_encryption_key=SecretStr(KEY),
    instagram_app_id="app-123",
    instagram_app_secret=SecretStr("app-secret"),
    instagram_redirect_uri="https://app.example/connect/instagram",
)
A = bearer("token-a")
PROFILE = {"user_id": "1784", "username": "ayesha.eats.lahore", "account_type": "MEDIA_CREATOR"}

Handler = Callable[[httpx.Request], httpx.Response]


def instagram_ok(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if url.startswith("https://api.instagram.com/oauth/access_token"):
        return httpx.Response(200, json={"access_token": "short-token", "user_id": 1784})
    if url.startswith("https://graph.instagram.com/access_token"):
        return httpx.Response(200, json={"access_token": "long-token", "expires_in": 5_184_000})
    if url.startswith("https://graph.instagram.com/v26.0/me"):
        return httpx.Response(200, json=PROFILE)
    return httpx.Response(404, json={"error": {"message": f"unexpected {url}"}})


@pytest.fixture
def instagram_handler() -> list[Handler]:
    """A one-item list, so a test can swap the handler before calling."""
    return [instagram_ok]


@pytest.fixture
def ig_client(app: FastAPI, client: TestClient, instagram_handler: list[Handler]) -> Iterator[TestClient]:
    transport = httpx.MockTransport(lambda request: instagram_handler[0](request))
    app.dependency_overrides[get_settings] = lambda: SETTINGS
    app.dependency_overrides[get_http_client] = lambda: httpx.AsyncClient(transport=transport)
    yield client


def _accounts(factory: async_sessionmaker[AsyncSession]) -> list[InstagramAccount]:
    async def read() -> list[InstagramAccount]:
        async with factory() as session:
            return list((await session.execute(select(InstagramAccount))).scalars())

    return asyncio.run(read())


def _connect(client: TestClient, state: str | None = None) -> httpx2.Response:
    return client.post(
        "/api/v1/instagram/callback",
        json={"code": "auth-code#_", "state": state or CIPHER.oauth_state(USER_A.id)},
        headers=A,
    )


def test_connect_url_carries_app_scopes_and_a_signed_state(ig_client: TestClient) -> None:
    response = ig_client.get("/api/v1/instagram/connect", headers=A)

    assert response.status_code == 200
    url = urlparse(response.json()["authorize_url"])
    query = parse_qs(url.query)
    assert url.netloc == "www.instagram.com"
    assert query["client_id"] == ["app-123"]
    assert query["redirect_uri"] == ["https://app.example/connect/instagram"]
    assert "instagram_business_content_publish" in query["scope"][0]
    assert CIPHER.user_from_oauth_state(query["state"][0]) == USER_A.id


def test_callback_stores_an_encrypted_token_and_starts_the_import(
    ig_client: TestClient, queue: FakeQueue, factory: async_sessionmaker[AsyncSession]
) -> None:
    response = _connect(ig_client)

    assert response.status_code == 202
    body = response.json()
    assert body["instagram"] == {
        "username": "ayesha.eats.lahore",
        "account_type": "MEDIA_CREATOR",
        "trial_reels_eligible": None,
    }
    assert queue.sent == [(TaskName.INSTAGRAM_IMPORT, UUID(body["job_id"]))]
    [account] = _accounts(factory)
    assert account.encrypted_token != "long-token"  # noqa: S105
    assert CIPHER.decrypt(account.encrypted_token) == "long-token"
    assert ig_client.get("/api/v1/me", headers=A).json()["instagram"]["username"] == "ayesha.eats.lahore"


def test_the_trailing_hash_is_removed_from_the_code(
    ig_client: TestClient, instagram_handler: list[Handler]
) -> None:
    sent_codes: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if "oauth/access_token" in str(request.url):
            sent_codes.append(parse_qs(request.content.decode())["code"][0])
        return instagram_ok(request)

    instagram_handler[0] = handler
    _connect(ig_client)

    assert sent_codes == ["auth-code"]


def test_reconnecting_replaces_the_token_instead_of_adding_a_row(
    ig_client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    _connect(ig_client)
    _connect(ig_client)

    assert len(_accounts(factory)) == 1


def test_a_state_started_by_someone_else_is_refused(
    ig_client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    response = _connect(ig_client, CIPHER.oauth_state(USER_B.id))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_oauth_state"
    assert _accounts(factory) == []


def test_a_forged_state_is_refused(ig_client: TestClient) -> None:
    forged = TokenCipher(Fernet.generate_key().decode()).oauth_state(USER_A.id)

    assert _connect(ig_client, forged).json()["error"]["code"] == "invalid_oauth_state"


@pytest.mark.parametrize(
    ("status", "code", "expected_status"),
    [(400, "instagram_rejected", 502), (503, "instagram_unavailable", 503)],
)
def test_instagram_errors_save_nothing(
    ig_client: TestClient,
    instagram_handler: list[Handler],
    queue: FakeQueue,
    factory: async_sessionmaker[AsyncSession],
    status: int,
    code: str,
    expected_status: int,
) -> None:
    instagram_handler[0] = lambda _: httpx.Response(status, json={"error": {"message": "nope"}})

    response = _connect(ig_client)

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == code
    assert _accounts(factory) == []
    assert queue.sent == []


def test_import_needs_a_connected_account(ig_client: TestClient, queue: FakeQueue) -> None:
    assert ig_client.post("/api/v1/instagram/import", headers=A).status_code == 404

    _connect(ig_client)
    response = ig_client.post("/api/v1/instagram/import", headers=A)

    assert response.status_code == 202
    assert [task for task, _ in queue.sent] == [TaskName.INSTAGRAM_IMPORT, TaskName.INSTAGRAM_IMPORT]


def test_disconnect_removes_the_account(
    ig_client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    _connect(ig_client)

    assert ig_client.delete("/api/v1/instagram/account", headers=A).status_code == 204
    assert ig_client.delete("/api/v1/instagram/account", headers=A).status_code == 204
    assert _accounts(factory) == []
    assert ig_client.get("/api/v1/me", headers=A).json()["instagram"] is None


def test_deleting_the_user_removes_their_instagram_account_and_jobs(
    ig_client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    job_id = _connect(ig_client).json()["job_id"]

    assert ig_client.delete("/api/v1/me", headers=A).status_code == 204
    assert _accounts(factory) == []
    assert ig_client.get(f"/api/v1/jobs/{job_id}", headers=A).status_code == 404


def test_server_without_instagram_settings_says_so(app: FastAPI, client: TestClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(token_encryption_key=SecretStr(KEY))

    response = client.get("/api/v1/instagram/connect", headers=A)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "instagram_not_configured"


def test_old_states_expire() -> None:
    old = Fernet(KEY.encode()).encrypt_at_time(
        f"{STATE_PREFIX}{USER_A.id}".encode(), int(time.time()) - OAUTH_STATE_MAX_AGE_S - 60
    )

    with pytest.raises(DecryptionFailed):
        CIPHER.decrypt(old.decode(), max_age_s=OAUTH_STATE_MAX_AGE_S)
