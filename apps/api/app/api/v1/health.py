from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.settings import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health")
async def read_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", version=settings.api_version)
