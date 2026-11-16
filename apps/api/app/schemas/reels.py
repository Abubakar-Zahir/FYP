from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.reel import Reel, ReelSource
from ml.dna.schema import HookType


class ReelOut(BaseModel):
    """Metrics are null when Instagram has no value yet. Null is not zero."""

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
    # Set once the reel has a DNA record (dna.analyse).
    hook_type: HookType | None

    @classmethod
    def from_reel(cls, reel: Reel, hook_type: str | None = None) -> "ReelOut":
        values = {name: getattr(reel, name) for name in cls.model_fields if name != "hook_type"}
        return cls(**values, hook_type=HookType(hook_type) if hook_type else None)


class ImportResult(BaseModel):
    """The `result` of an instagram.import job."""

    reels: int
    comments: int
