from app.core.settings import Settings
from app.main import create_app
from fastapi import Body, FastAPI
from fastapi.testclient import TestClient


def test_missing_token_uses_the_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {"code": "not_authenticated", "message": "Sign in to continue.", "details": {}}
    }


def test_bad_token_is_rejected_and_not_echoed(client: TestClient) -> None:
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
