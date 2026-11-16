from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

JOB_TYPE_MAX_LENGTH = 50
JOB_STATUS_MAX_LENGTH = 20
JOB_ERROR_MAX_LENGTH = 200


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Job(Base):
    """One row per piece of long work (docs/backend.md, Jobs). The client polls it."""

    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    type: Mapped[str] = mapped_column(String(JOB_TYPE_MAX_LENGTH))
    status: Mapped[str] = mapped_column(String(JOB_STATUS_MAX_LENGTH), default=JobStatus.QUEUED)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    # Any: each job type stores its own result shape, validated by that type's schema.
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # A stable error code, never a raw exception message, which can hold user data.
    error: Mapped[str | None] = mapped_column(String(JOB_ERROR_MAX_LENGTH), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
