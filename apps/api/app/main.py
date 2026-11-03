from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.settings import get_settings

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version=settings.api_version)
    application.include_router(health_router, prefix=API_PREFIX)
    return application


app = create_app()
