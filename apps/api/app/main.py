from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.me import router as me_router
from app.core.errors import register_error_handlers
from app.core.security import TokenVerifier
from app.core.settings import Settings, get_settings

API_PREFIX = "/api/v1"


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient() as http:
            issuer = settings.supabase_issuer
            application.state.token_verifier = TokenVerifier(issuer, http) if issuer else None
            yield

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
    return application


app = create_app(get_settings())
