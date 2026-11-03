"""Format DNA record, the contract between the extractor, the API and the script generator.

Owned by the video and ML area. Frozen at the end of week 4 (prd.md), after which any
change bumps SCHEMA_VERSION.

Version history:
    1.0: first version, from SRS FR-2.1 to FR-2.4.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = "1.0"


class HookType(StrEnum):
    QUESTION = "question"
    BOLD_CLAIM = "bold_claim"
    PATTERN_INTERRUPT = "pattern_interrupt"
    STORY = "story"
    LIST = "list"
    OTHER = "other"


class TranscriptSegment(BaseModel):
    start_s: float = Field(ge=0)
    end_s: float = Field(ge=0)
    text: str


class ReelSignals(BaseModel):
    """What the machine extracts directly, before any LLM structuring."""

    schema_version: str = SCHEMA_VERSION
    length_s: float = Field(gt=0)
    cut_times_s: list[float]
    pacing_cuts_per_10s: float = Field(ge=0)
    detected_language: str | None
    transcript: list[TranscriptSegment]
    hook_candidate_text: str
    keyframe_paths: list[str]
    model_version: str


class Beat(BaseModel):
    label: str
    start_s: float = Field(ge=0)
    end_s: float = Field(ge=0)
    description: str

    @model_validator(mode="after")
    def end_after_start(self) -> "Beat":
        if self.end_s <= self.start_s:
            raise ValueError("A beat must end after it starts")
        return self


class Overlay(BaseModel):
    at_s: float = Field(ge=0)
    text: str


class DnaRecord(BaseModel):
    """The structured record: machine signals plus the LLM's reading of them."""

    schema_version: str = SCHEMA_VERSION
    signals: ReelSignals
    hook_type: HookType
    hook_text: str
    beats: list[Beat] = Field(min_length=1)
    overlays: list[Overlay]
    cta: str
    model_version: str
