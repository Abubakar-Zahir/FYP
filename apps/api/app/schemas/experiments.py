from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.experiment import ExperimentStatus, VariantStatus
from ml.variants.generate import MAX_VARIANTS, MIN_VARIANTS

SHARE_INSTRUCTIONS = (
    "Instagram's API can't share a Trial Reel with followers. Open the winning reel in the Instagram app, "
    "tap the three dots, then 'Share to followers'."
)


class InsightWindow(StrEnum):
    DAY = "24h"
    THREE_DAYS = "72h"


class CreateExperimentRequest(BaseModel):
    video_id: UUID
    # The script whose hooks seed the variants. Optional: without it the LLM works from the video title.
    script_id: UUID | None = None
    variant_count: int = Field(default=MIN_VARIANTS, ge=MIN_VARIANTS, le=MAX_VARIANTS)


class VariantInsightOut(BaseModel):
    window: InsightWindow
    views: int | None
    reach: int | None
    saves: int | None
    shares: int | None


class VariantOut(BaseModel):
    """Field names match apps/web."""

    id: UUID
    label: str
    hook_line: str
    hook_style: str
    opener: str
    caption: str
    is_trial: bool
    status: VariantStatus
    permalink: str | None
    error: str | None
    insights: list[VariantInsightOut]


class ExperimentOut(BaseModel):
    id: UUID
    video_title: str
    strategy: Literal["thompson_sampling"]
    status: ExperimentStatus
    winner_variant_id: UUID | None
    # Set once a winner exists, because sharing it is a step the creator takes in the app.
    share_instructions: str | None
    variants: list[VariantOut]


class CreateResult(BaseModel):
    """The `result` of an experiments.create job."""

    experiment_id: UUID
