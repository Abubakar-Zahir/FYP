from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.instagram_account import InstagramAccount
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
    username: str
    account_type: str
    # Null until the first publish shows whether Instagram accepts Trial Reels from this account.
    trial_reels_eligible: bool | None

    @classmethod
    def from_account(cls, account: InstagramAccount) -> "InstagramAccountOut":
        return cls(
            username=account.username,
            account_type=account.account_type,
            trial_reels_eligible=account.trial_reels_eligible,
        )


class InstagramConnected(JobAccepted):
    """The account, plus the reel import job that connecting starts."""

    instagram: InstagramAccountOut
