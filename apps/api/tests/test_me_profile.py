from typing import Any

import pytest
from alembic import command
from app.core.security import get_token_verifier
from app.core.settings import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from tests.support import USER_A, FakeVerifier, alembic_config, bearer

PROFILE: dict[str, Any] = {
    "role": "creator",
    "niche": "Lahore street food",
    "language_mix": ["english", "roman_urdu"],
    "tone": "Honest reviewer",
    "goals": "Grow to 20K followers",
}
A = bearer("token-a")
B = bearer("token-b")


def test_me_before_onboarding_has_no_profile(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers=A)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(USER_A.id),
        "name": "Ayesha",
        "email": "a@example.com",
        "profile": None,
        "instagram": None,
    }


def test_saving_a_profile_returns_it_and_it_persists(client: TestClient) -> None:
    saved = client.put("/api/v1/me/profile", json=PROFILE, headers=A)

    assert saved.status_code == 200
    assert saved.json()["profile"] == PROFILE
    assert client.get("/api/v1/me", headers=A).json()["profile"] == PROFILE


def test_saving_again_updates_instead_of_failing(client: TestClient) -> None:
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)

    updated = client.put(
        "/api/v1/me/profile", json={**PROFILE, "role": "brand", "niche": "Skincare"}, headers=A
    )

    assert updated.status_code == 200
    assert updated.json()["profile"]["role"] == "brand"
    assert client.get("/api/v1/me", headers=A).json()["profile"]["niche"] == "Skincare"


def test_text_is_trimmed(client: TestClient) -> None:
    response = client.put("/api/v1/me/profile", json={**PROFILE, "niche": "  Skincare  "}, headers=A)

    assert response.json()["profile"]["niche"] == "Skincare"


@pytest.mark.parametrize(
    "change",
    [
        {"role": "admin"},
        {"niche": " x "},
        {"niche": "x" * 101},
        {"language_mix": []},
        {"language_mix": ["klingon"]},
        {"tone": "   "},
        {"goals": "hi"},
        {"goals": "x" * 1001},
    ],
    ids=[
        "role",
        "niche-short",
        "niche-long",
        "no-language",
        "bad-language",
        "blank-tone",
        "goals-short",
        "goals-long",
    ],
)
def test_invalid_profiles_are_rejected(client: TestClient, change: dict[str, Any]) -> None:
    response = client.put("/api/v1/me/profile", json={**PROFILE, **change}, headers=A)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert client.get("/api/v1/me", headers=A).json()["profile"] is None


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/v1/me"), ("put", "/api/v1/me/profile"), ("delete", "/api/v1/me")],
)
def test_every_route_requires_sign_in(client: TestClient, method: str, path: str) -> None:
    response = client.request(method, path, json=PROFILE if method == "put" else None)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_users_cannot_see_each_others_profiles(client: TestClient) -> None:
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)

    assert client.get("/api/v1/me", headers=B).json()["profile"] is None


def test_a_client_cannot_write_to_another_user_by_sending_an_id(client: TestClient) -> None:
    client.put(
        "/api/v1/me/profile", json={**PROFILE, "id": "22222222-2222-4222-8222-222222222222"}, headers=A
    )

    assert client.get("/api/v1/me", headers=B).json()["profile"] is None
    assert client.get("/api/v1/me", headers=A).json()["profile"] == PROFILE


def test_delete_removes_my_data_only(client: TestClient) -> None:
    client.put("/api/v1/me/profile", json=PROFILE, headers=A)
    client.put("/api/v1/me/profile", json=PROFILE, headers=B)

    response = client.delete("/api/v1/me", headers=A)

    assert response.status_code == 204
    assert client.get("/api/v1/me", headers=A).json()["profile"] is None
    assert client.get("/api/v1/me", headers=B).json()["profile"] == PROFILE


def test_delete_is_safe_to_repeat(client: TestClient) -> None:
    assert client.delete("/api/v1/me", headers=A).status_code == 204
    assert client.delete("/api/v1/me", headers=A).status_code == 204


def test_server_without_a_database_says_so() -> None:
    app = create_app(Settings(supabase_url="https://project.supabase.co", database_url=None))
    app.dependency_overrides[get_token_verifier] = FakeVerifier
    with TestClient(app) as no_database:
        response = no_database.get("/api/v1/me", headers=A)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_not_configured"


def test_migration_matches_the_models_and_can_be_undone(database_url: str) -> None:
    config = alembic_config(database_url)

    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
