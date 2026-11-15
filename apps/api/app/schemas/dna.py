from uuid import UUID

from pydantic import BaseModel

from app.models.reel import ReelSource
from ml.dna.schema import Beat, HookType, Overlay


class AnalyseRequest(BaseModel):
    reel_id: UUID


class DnaRecordOut(BaseModel):
    """What the DNA library and detail screens show. Field names match apps/web."""

    id: UUID
    reel_id: UUID
    schema_version: str
    title: str
    source: ReelSource
    hook_type: HookType
    hook_text: str
    pacing_cuts_per_10s: float
    length_s: float
    beats: list[Beat]
    overlays: list[Overlay]
    cta: str
    # Null for reference reels and for accounts with too few reels to compare.
    outlier_score: float | None
    transcript: str
    is_template: bool
    model_version: str


class AnalyseResult(BaseModel):
    """The `result` of a dna.analyse job."""

    dna_id: UUID
