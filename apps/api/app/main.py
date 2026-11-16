from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.comments import router as comments_router
from app.api.v1.dna import router as dna_router
from app.api.v1.health import router as health_router
from app.api.v1.instagram import router as instagram_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.me import router as me_router
from app.api.v1.reels import router as reels_router
from app.api.v1.scripts import router as scripts_router
from app.core.errors import register_error_handlers
from app.core.security import TokenVerifier
from app.core.settings import Settings, get_settings
from app.db.session import create_engine, create_session_factory
from app.services.storage import build_storage
from app.workers.queue import CeleryJobQueue, JobQueue

API_PREFIX = "/api/v1"


def _job_queue(settings: Settings) -> JobQueue | None:
    if not settings.redis_url:
        return None
    # Imported here so a server without Redis never builds a Celery app.
    from app.workers.celery_app import create_celery

    return CeleryJobQueue(create_celery(settings))


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url) if settings.database_url else None
        application.state.session_factory = create_session_factory(engine) if engine else None
        application.state.job_queue = _job_queue(settings)
        application.state.storage = build_storage(settings)
        async with httpx.AsyncClient() as http:
            application.state.http = http
            issuer = settings.supabase_issuer
            application.state.token_verifier = TokenVerifier(issuer, http) if issuer else None
            yield
        if engine:
            await engine.dispose()

    application = FastAPI(title=settings.app_name, version=settings.api_version, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_error_handlers(application)
    application.include_router(health_router, prefix=API_PREFIX)
    application.include_router(me_router, prefix=API_PREFIX)
    application.include_router(jobs_router, prefix=API_PREFIX)
    application.include_router(instagram_router, prefix=API_PREFIX)
    application.include_router(reels_router, prefix=API_PREFIX)
    application.include_router(dna_router, prefix=API_PREFIX)
    application.include_router(scripts_router, prefix=API_PREFIX)
    application.include_router(comments_router, prefix=API_PREFIX)
    return application


app = create_app(get_settings())
