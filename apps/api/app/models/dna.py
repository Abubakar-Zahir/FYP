from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SCHEMA_VERSION_MAX_LENGTH = 10
HOOK_TYPE_MAX_LENGTH = 30
MODEL_VERSION_MAX_LENGTH = 200


class DnaRecordRow(Base):
    """One format DNA record per reel (docs/backend.md, `dna_records`).

    The searchable fields are columns. `record` keeps the full ml.dna.schema.DnaRecord,
    so the script generator reads exactly what the extractor produced.
    """

    __tablename__ = "dna_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    reel_id: Mapped[UUID] = mapped_column(ForeignKey("reels.id", ondelete="CASCADE"), unique=True, index=True)
    schema_version: Mapped[str] = mapped_column(String(SCHEMA_VERSION_MAX_LENGTH))
    hook_type: Mapped[str] = mapped_column(String(HOOK_TYPE_MAX_LENGTH))
    hook_text: Mapped[str] = mapped_column(Text)
    pacing_cuts_per_10s: Mapped[float] = mapped_column(Float)
    length_s: Mapped[float] = mapped_column(Float)
    cta: Mapped[str] = mapped_column(Text)
    transcript: Mapped[str] = mapped_column(Text)
    # Any: the dumped DnaRecord, validated with ml.dna.schema.DnaRecord when read.
    record: Mapped[dict[str, Any]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(MODEL_VERSION_MAX_LENGTH))
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
