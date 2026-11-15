from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

MEDIA_ID_MAX_LENGTH = 64
SOURCE_MAX_LENGTH = 20
TITLE_MAX_LENGTH = 200
R2_KEY_MAX_LENGTH = 300
COMMENT_ID_MAX_LENGTH = 64


class ReelSource(StrEnum):
    OWN = "own"  # imported from the creator's connected account
    REFERENCE = "reference"  # a file the creator uploaded to study (never a scraped link)


class Reel(Base):
    """A reel the creator posted, or a reference reel they uploaded.

    Holds the latest metrics only. Per-variant history at 24 h and 72 h comes in Phase 3.
    Metrics are null when Instagram has no value yet, which is not the same as zero.
    """

    __tablename__ = "reels"
    __table_args__ = (UniqueConstraint("user_id", "ig_media_id", name="uq_reels_user_media"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    source: Mapped[str] = mapped_column(String(SOURCE_MAX_LENGTH))
    ig_media_id: Mapped[str | None] = mapped_column(String(MEDIA_ID_MAX_LENGTH), nullable=True)
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    permalink: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    r2_key: Mapped[str | None] = mapped_column(String(R2_KEY_MAX_LENGTH), nullable=True)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_watch_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    outlier_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (UniqueConstraint("user_id", "ig_comment_id", name="uq_comments_user_comment"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    reel_id: Mapped[UUID] = mapped_column(ForeignKey("reels.id", ondelete="CASCADE"), index=True)
    ig_comment_id: Mapped[str] = mapped_column(String(COMMENT_ID_MAX_LENGTH))
    text: Mapped[str] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
