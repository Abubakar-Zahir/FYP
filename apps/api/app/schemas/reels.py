from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.reel import ReelSource


class ReelOut(BaseModel):
    """Metrics are null when Instagram has no value yet. Null is not zero."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: ReelSource
    title: str
    caption: str | None
    permalink: str | None
    posted_at: datetime | None
    views: int | None
    reach: int | None
    saves: int | None
    shares: int | None
    avg_watch_time_s: float | None
    outlier_score: float | None
    # Filled once the reel has a DNA record (dna.analyse).
    hook_type: str | None = None


class ImportResult(BaseModel):
    """The `result` of an instagram.import job."""

    reels: int
    comments: int
