"""Inputs and outputs of script generation (SRS FR-3, prd.md Member C deliverable 6)."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from ml.dna.schema import DnaRecord

HOOK_COUNT = 5
ANGLE_COUNT = 3
MIN_BEATS = 3
MAX_TEMPLATES = 3
MAX_VOICE_SAMPLES = 8
TOPIC_MAX_LENGTH = 300


class ScriptLanguage(StrEnum):
    ENGLISH = "english"
    ROMAN_URDU = "roman_urdu"  # Urdu words in Latin letters, as creators type them
    MIXED = "mixed"  # Roman Urdu and English in one script


class CreatorVoice(BaseModel):
    niche: str
    tone: str
    goals: str
    # The creator's own captions, so the script sounds like them (voice matching v0).
    sample_captions: list[str] = Field(default_factory=list, max_length=MAX_VOICE_SAMPLES)


class ScriptRequest(BaseModel):
    topic: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=TOPIC_MAX_LENGTH)]
    language: ScriptLanguage
    creator: CreatorVoice
    templates: list[DnaRecord] = Field(min_length=1, max_length=MAX_TEMPLATES)


class Hook(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Angle(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    summary: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ScriptBeat(BaseModel):
    beat: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    line: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    shot: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ScriptDraft(BaseModel):
    hooks: list[Hook] = Field(min_length=HOOK_COUNT, max_length=HOOK_COUNT)
    angles: list[Angle] = Field(min_length=ANGLE_COUNT, max_length=ANGLE_COUNT)
    body: list[ScriptBeat] = Field(min_length=MIN_BEATS)
    model_version: str
