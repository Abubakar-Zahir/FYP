from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

STATUS_MAX_LENGTH = 20
LABEL_MAX_LENGTH = 4
FEATURE_MAX_LENGTH = 40
MEDIA_ID_MAX_LENGTH = 64
KEY_MAX_LENGTH = 300
ERROR_MAX_LENGTH = 200


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHING = "publishing"
    LIVE = "live"  # published, waiting for 72 h insights
    DONE = "done"  # winner picked


class VariantStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHING = "publishing"
    LIVE = "live"
    FAILED = "failed"


class Experiment(Base):
    """One video published as several variants (docs/backend.md, `experiments`)."""

    __tablename__ = "experiments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True)
    video_id: Mapped[UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    script_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(STATUS_MAX_LENGTH), default=ExperimentStatus.DRAFT)
    winner_variant_id: Mapped[UUID | None] = mapped_column(nullable=True)
    share_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(index=True)
    label: Mapped[str] = mapped_column(String(LABEL_MAX_LENGTH))
    hook_line: Mapped[str] = mapped_column(Text)
    hook_style: Mapped[str] = mapped_column(String(FEATURE_MAX_LENGTH))
    opener: Mapped[str] = mapped_column(Text)
    opener_type: Mapped[str] = mapped_column(String(FEATURE_MAX_LENGTH))
    caption: Mapped[str] = mapped_column(Text)
    caption_length: Mapped[str] = mapped_column(String(FEATURE_MAX_LENGTH))
    is_trial: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(STATUS_MAX_LENGTH), default=VariantStatus.DRAFT)
    r2_key: Mapped[str | None] = mapped_column(String(KEY_MAX_LENGTH), nullable=True)
    ig_media_id: Mapped[str | None] = mapped_column(String(MEDIA_ID_MAX_LENGTH), nullable=True)
    permalink: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(ERROR_MAX_LENGTH), nullable=True)

    def features(self) -> dict[str, str]:
        return {
            "hook_style": self.hook_style,
            "opener": self.opener_type,
            "caption_length": self.caption_length,
        }


class VariantInsight(Base):
    """Insights at 24 h (preliminary, data can lag) and 72 h (used to pick the winner)."""

    __tablename__ = "variant_insights"
    __table_args__ = (UniqueConstraint("variant_id", "window", name="uq_variant_insights_window"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    variant_id: Mapped[UUID] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(index=True)
    window: Mapped[str] = mapped_column(String(8))
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BanditBelief(Base):
    """A Beta belief per feature value. `user_id` null is the shared prior across creators."""

    __tablename__ = "bandit_beliefs"
    __table_args__ = (UniqueConstraint("user_id", "feature", "value", name="uq_bandit_beliefs"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(index=True, nullable=True)
    feature: Mapped[str] = mapped_column(String(FEATURE_MAX_LENGTH))
    value: Mapped[str] = mapped_column(String(FEATURE_MAX_LENGTH))
    alpha: Mapped[float] = mapped_column(Float)
    beta: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
