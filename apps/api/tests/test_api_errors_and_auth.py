from collections.abc import Iterator
from uuid import uuid4

import pytest
from app.core.errors import ApiError
from app.core.security import CurrentUser, TokenVerifier, get_token_verifier
from app.core.settings import Settings
from app.main import create_app
from fastapi import Body, FastAPI
from fastapi.testclient import TestClient

USER = CurrentUser(id=uuid4(), email="ayesha@example.com", name="Ayesha Khan")
GOOD_TOKEN = "good-token"  # noqa: S105


class FakeVerifier(TokenVerifier):
    def __init__(self) -> None:
        pass

    async def verify(self, token: str) -> CurrentUser:
        if token == GOOD_TOKEN:
            return USER
        raise ApiError(401, "invalid_token", "The access token is not valid.")


@pytest.fixture
def app() -> FastAPI:
    return create_app(
        Settings(supabase_url="https://project.supabase.co", cors_origins=["http://localhost:3000"])
    )


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    app.dependency_overrides[get_token_verifier] = FakeVerifier
    with TestClient(app) as test_client:
        yield test_client


def test_me_returns_the_signed_in_user(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {GOOD_TOKEN}"})

    assert response.status_code == 200
    assert response.json() == {"id": str(USER.id), "email": USER.email, "name": USER.name}


def test_me_without_token_uses_the_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {"code": "not_authenticated", "message": "Sign in to continue.", "details": {}}
    }


def test_me_with_bad_token_is_rejected_and_not_echoed(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer stolen-looking-value"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
    assert "stolen-looking-value" not in response.text


def test_health_stays_public(client: TestClient) -> None:
    assert client.get("/api/v1/health").status_code == 200


def test_unknown_route_uses_the_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_validation_errors_use_the_shape_and_do_not_echo_input(app: FastAPI, client: TestClient) -> None:
    @app.post("/echo")
    async def echo(age: int = Body(embed=True)) -> int:
        return age

    response = client.post("/echo", json={"age": "private-value"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]["fields"][0]["location"] == ["body", "age"]
    assert "private-value" not in response.text


def test_server_without_supabase_config_says_so() -> None:
    app = create_app(Settings(supabase_url=None))
    with TestClient(app) as client:
        response = client.get("/api/v1/me", headers={"Authorization": "Bearer anything"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "auth_not_configured"


def test_cors_allows_the_frontend_only(client: TestClient) -> None:
    allowed = client.options(
        "/api/v1/me",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    blocked = client.options(
        "/api/v1/me",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in blocked.headers
