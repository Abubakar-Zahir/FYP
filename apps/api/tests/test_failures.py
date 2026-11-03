import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from app.core.security import get_token_verifier
from app.core.settings import Settings
from app.db.session import create_engine, create_session_factory
from app.main import create_app
from app.models.user import User
from app.schemas.me import Language, Profile, Role
from app.services import users
from fastapi.testclient import TestClient
from tests.support import FakeVerifier, alembic_config, bearer

PROFILE = Profile(
    role=Role.CREATOR,
    niche="Skincare",
    language_mix=[Language.ENGLISH],
    tone="Calm",
    goals="Grow my audience",
)


def test_double_submitted_form_ends_as_an_update(database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both requests see no row. The second insert fails, and must then update instead of erroring."""
    command.upgrade(alembic_config(database_url), "head")
    user_id = uuid4()
    real_get_user = users.get_user
    calls = 0

    async def row_appears_after_first_look(session, wanted_id):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return None if calls == 1 else await real_get_user(session, wanted_id)

    async def run() -> User:
        engine = create_engine(database_url)
        factory = create_session_factory(engine)
        async with factory() as other_request:
            other_request.add(
                User(id=user_id, **PROFILE.model_copy(update={"niche": "First"}).model_dump(mode="json"))
            )
            await other_request.commit()
        monkeypatch.setattr(users, "get_user", row_appears_after_first_look)
        async with factory() as session:
            saved = await users.save_profile(session, user_id, PROFILE)
        await engine.dispose()
        return saved

    saved = asyncio.run(run())

    assert saved.niche == "Skincare"
    assert calls == 2


def test_database_outage_uses_the_error_shape_and_leaks_nothing(tmp_path: Path) -> None:
    unreachable = f"sqlite+aiosqlite:///{tmp_path}/missing-folder/nope.db"
    app = create_app(Settings(supabase_url="https://project.supabase.co", database_url=unreachable))
    app.dependency_overrides[get_token_verifier] = FakeVerifier

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/me", headers=bearer("token-a"))

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Something went wrong on our side.", "details": {}}
    }
    assert "missing-folder" not in response.text
