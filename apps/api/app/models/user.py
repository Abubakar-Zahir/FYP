from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ROLE_MAX_LENGTH = 20
NICHE_MAX_LENGTH = 100
TONE_MAX_LENGTH = 100


class User(Base):
    """A row exists once onboarding is complete. Email and name stay in Supabase (rules.md 6.5)."""

    __tablename__ = "users"

    # The Supabase user id, so it is never generated here.
    id: Mapped[UUID] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(ROLE_MAX_LENGTH))
    niche: Mapped[str] = mapped_column(String(NICHE_MAX_LENGTH))
    language_mix: Mapped[list[str]] = mapped_column(JSON)
    tone: Mapped[str] = mapped_column(String(TONE_MAX_LENGTH))
    goals: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
