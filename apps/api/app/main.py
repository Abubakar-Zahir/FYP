from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.analytics import router as analytics_router
from app.api.v1.comments import router as comments_router
from app.api.v1.dna import router as dna_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.health import router as health_router
from app.api.v1.instagram import router as instagram_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.me import router as me_router
from app.api.v1.reels import router as reels_router
from app.api.v1.scripts import router as scripts_router
from app.api.v1.videos import router as videos_router
from app.core.errors import register_error_handlers
from app.core.observability import init_sentry, request_log
from app.core.rate_limit import Counter, MemoryCounter, RedisCounter, make_middleware
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


def _rate_counter(settings: Settings) -> Counter:
    return RedisCounter(settings.redis_url) if settings.redis_url else MemoryCounter()


def create_app(settings: Settings, rate_counter: Counter | None = None) -> FastAPI:
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
    init_sentry(settings)
    # The middleware added last runs first. CORS is outermost, so even a 429 carries CORS headers
    # and the browser can read it. The request log wraps the rate limit.
    application.middleware("http")(make_middleware(rate_counter or _rate_counter(settings)))
    application.middleware("http")(request_log)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Retry-After", "X-Request-ID"],
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
    application.include_router(videos_router, prefix=API_PREFIX)
    application.include_router(experiments_router, prefix=API_PREFIX)
    application.include_router(analytics_router, prefix=API_PREFIX)
    return application


app = create_app(get_settings())
