from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.user import NICHE_MAX_LENGTH, TONE_MAX_LENGTH

GOALS_MIN_LENGTH = 5
GOALS_MAX_LENGTH = 1000
NICHE_MIN_LENGTH = 2


class Role(StrEnum):
    CREATOR = "creator"
    BRAND = "brand"


class Language(StrEnum):
    ENGLISH = "english"
    URDU = "urdu"
    ROMAN_URDU = "roman_urdu"


class Profile(BaseModel):
    """Same fields and limits as the onboarding form in apps/web."""

    model_config = ConfigDict(from_attributes=True)

    role: Role
    niche: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=NICHE_MIN_LENGTH, max_length=NICHE_MAX_LENGTH),
    ]
    language_mix: Annotated[list[Language], Field(min_length=1, max_length=len(Language))]
    tone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TONE_MAX_LENGTH)]
    goals: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=GOALS_MIN_LENGTH, max_length=GOALS_MAX_LENGTH),
    ]


class MeResponse(BaseModel):
    id: UUID
    name: str | None
    email: str | None
    profile: Profile | None
    # Filled in once Instagram connect ships (P1-03). Kept so the frontend contract is stable.
    instagram: None = None
