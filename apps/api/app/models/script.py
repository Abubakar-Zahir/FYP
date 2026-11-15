from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

LANGUAGE_MAX_LENGTH = 20
MODEL_VERSION_MAX_LENGTH = 200


class Script(Base):
    """A generated script (docs/backend.md, `scripts`).

    The row is created when generation starts, with the topic and language. The worker fills
    hooks, angles and body. Until then they are null and the script is not ready.
    """

    __tablename__ = "scripts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    template_id: Mapped[UUID] = mapped_column(ForeignKey("dna_records.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(LANGUAGE_MAX_LENGTH))
    # Any: lists of ml.scripts.schema models, dumped to JSON. Validated when read.
    hooks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    angles: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    body: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(MODEL_VERSION_MAX_LENGTH), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
