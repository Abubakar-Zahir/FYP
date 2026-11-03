from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.errors import ApiError


def create_engine(database_url: str) -> AsyncEngine:
    # hide_parameters keeps profile text out of error messages and logs (rules.md 3.11).
    return create_async_engine(database_url, pool_pre_ping=True, hide_parameters=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] | None = request.app.state.session_factory
    if factory is None:
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "database_not_configured",
            "The database is not configured on this server.",
        )
    async with factory() as session:
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_session)]
