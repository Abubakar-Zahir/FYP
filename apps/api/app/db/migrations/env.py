import asyncio

from alembic import context
from app.core.settings import get_settings
from app.db.base import Base
from app.models import user  # noqa: F401  (registers the table on Base.metadata)
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine


def _database_url() -> str:
    url = context.config.get_main_option("sqlalchemy.url") or get_settings().database_url
    if not url:
        raise RuntimeError("Set DATABASE_URL before running migrations.")
    return url


def _run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def _run_online() -> None:
    engine = create_async_engine(_database_url(), hide_parameters=True)
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported.")
asyncio.run(_run_online())
