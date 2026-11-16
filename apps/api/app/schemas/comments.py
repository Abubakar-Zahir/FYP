from uuid import UUID

from pydantic import BaseModel

from ml.comments.labels import CommentLabel


class LabelCount(BaseModel):
    label: CommentLabel
    count: int


class CommentSummaryOut(BaseModel):
    """Labelled comments in the period. Comments not yet classified are not counted."""

    total: int
    period_days: int
    by_label: list[LabelCount]


class CommentThemeOut(BaseModel):
    id: UUID
    theme: str
    size: int
    dominant_label: CommentLabel
    examples: list[str]
    idea: str


class SyncResult(BaseModel):
    """The `result` of a comments.sync job."""

    labelled: int
    themes: int
