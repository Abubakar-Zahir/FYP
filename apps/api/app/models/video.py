from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.reel import R2_KEY_MAX_LENGTH, TITLE_MAX_LENGTH


class Video(Base):
    """Raw footage the creator uploads to auto-edit (docs/backend.md, `videos` and `edit_jobs`).

    The latest edit's output and options live on the row. The job row tracks the run itself.
    """

    __tablename__ = "videos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    source_r2_key: Mapped[str] = mapped_column(String(R2_KEY_MAX_LENGTH))
    output_r2_key: Mapped[str | None] = mapped_column(String(R2_KEY_MAX_LENGTH), nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    removed_silence_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Any: the EditRequest that made the output, for reproducing it.
    options: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
