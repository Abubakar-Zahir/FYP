from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    status: JobStatus
    progress: float = Field(ge=0, le=1)
    # Any: the shape depends on `type`, and each job's own endpoint documents it.
    result: dict[str, Any] | None
    error: str | None


class JobAccepted(BaseModel):
    """The 202 body for every endpoint that starts long work (rules.md 3b.2)."""

    job_id: UUID
