from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from app.core.security import get_token_verifier
from app.core.settings import Settings
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import FakeVerifier, alembic_config


@pytest.fixture
def database_url(tmp_path: Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / f'{uuid4().hex}.db'}"


@pytest.fixture
def app(database_url: str) -> FastAPI:
    # The schema comes from the real migration, so these tests cover the migration too.
    command.upgrade(alembic_config(database_url), "head")
    return create_app(
        Settings(
            supabase_url="https://project.supabase.co",
            database_url=database_url,
            cors_origins=["http://localhost:3000"],
        )
    )


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    app.dependency_overrides[get_token_verifier] = FakeVerifier
    with TestClient(app) as test_client:
        yield test_client
