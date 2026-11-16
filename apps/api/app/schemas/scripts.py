from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from ml.scripts.schema import TOPIC_MAX_LENGTH, Angle, ScriptBeat, ScriptLanguage


class GenerateScriptRequest(BaseModel):
    template_id: UUID
    topic: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=TOPIC_MAX_LENGTH)]
    language: ScriptLanguage


class ScoreFactor(BaseModel):
    label: str
    impact: float


class ScoredHook(BaseModel):
    text: str
    # The hook scorer arrives in Phase 2 (P2). Until then hooks are not scored.
    score: float | None = None
    top_factors: list[ScoreFactor] = Field(default_factory=list)


class ScriptOut(BaseModel):
    """Field names match apps/web."""

    id: UUID
    template_id: UUID
    topic: str
    language: ScriptLanguage
    hooks: list[ScoredHook]
    angles: list[Angle]
    body: list[ScriptBeat]
    model_version: str


class GenerateResult(BaseModel):
    """The `result` of a scripts.generate job."""

    script_id: UUID
