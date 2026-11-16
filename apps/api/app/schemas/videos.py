from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from ml.edit.captions import CaptionStyle

HOOK_TEXT_MAX_LENGTH = 120


class VideoOut(BaseModel):
    id: UUID
    title: str
    # A link that lasts an hour. Null until the first edit finishes.
    output_url: str | None
    duration_s: float | None
    removed_silence_s: float | None


class VideoUpload(BaseModel):
    """PUT the file to `upload_url` with these headers, then call POST /videos/{id}/edit."""

    video: VideoOut
    upload_url: str
    upload_headers: dict[str, str]


class EditRequest(BaseModel):
    caption_style: CaptionStyle
    cut_silences: bool
    progress_bar: bool
    hook_overlay: bool
    # The line shown for the first 3 seconds when hook_overlay is on.
    hook_text: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=HOOK_TEXT_MAX_LENGTH)] | None
    ) = None
    # Captions in Roman Urdu even when Whisper heard Urdu script.
    roman_urdu_captions: bool = True


class EditResult(BaseModel):
    """The `result` of a videos.edit job. Field names match apps/web."""

    output_url: str
    duration_s: float
    removed_silence_s: float
