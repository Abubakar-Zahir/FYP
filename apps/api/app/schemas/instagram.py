from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.jobs import JobAccepted

CODE_MAX_LENGTH = 2000
STATE_MAX_LENGTH = 500


class InstagramAuthorizeUrl(BaseModel):
    authorize_url: str


class InstagramCallback(BaseModel):
    """What the web app's callback page forwards from Instagram's redirect."""

    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CODE_MAX_LENGTH)]
    state: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=STATE_MAX_LENGTH)]


class InstagramAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    account_type: str
    # Unknown until the first Trial Reel publish answers (P0-09 and Phase 3).
    trial_reels_eligible: bool | None = None


class InstagramConnected(JobAccepted):
    """The account, plus the reel import job that connecting starts."""

    instagram: InstagramAccountOut
