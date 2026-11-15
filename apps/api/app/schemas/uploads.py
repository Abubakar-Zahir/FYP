from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.reels import ReelOut

# rules.md 6.3: validate type and size. Duration (max 90 s) is checked by the DNA worker,
# because only reading the file can tell it.
MAX_UPLOAD_BYTES = 200 * 1024 * 1024
FILENAME_MAX_LENGTH = 200


class VideoContentType(StrEnum):
    MP4 = "video/mp4"
    QUICKTIME = "video/quicktime"


EXTENSIONS: dict[VideoContentType, str] = {VideoContentType.MP4: ".mp4", VideoContentType.QUICKTIME: ".mov"}


class ReferenceUploadRequest(BaseModel):
    filename: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=FILENAME_MAX_LENGTH)
    ]
    content_type: VideoContentType
    size_bytes: int = Field(gt=0, le=MAX_UPLOAD_BYTES)


class ReferenceUpload(BaseModel):
    """PUT the file to `upload_url` with exactly these headers, then call POST /dna/analyse."""

    reel: ReelOut
    upload_url: str
    upload_headers: dict[str, str]
