"""Cursor pagination for list endpoints (rules.md 3b.4).

Lists are ordered newest first by (timestamp, id). The cursor is the last item's pair,
base64 encoded, so it is opaque to the client and stable when new rows arrive.
"""

import base64
import binascii
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Query, status
from pydantic import BaseModel

from app.core.errors import ApiError

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
SEPARATOR = "|"


class Page[Item: BaseModel](BaseModel):
    items: list[Item]
    next_cursor: str | None


class Cursor(BaseModel):
    at: datetime
    id: UUID


def encode_cursor(at: datetime, item_id: UUID) -> str:
    return base64.urlsafe_b64encode(f"{at.isoformat()}{SEPARATOR}{item_id}".encode()).decode()


def decode_cursor(value: str) -> Cursor:
    try:
        at, item_id = base64.urlsafe_b64decode(value.encode()).decode().split(SEPARATOR)
        return Cursor(at=datetime.fromisoformat(at), id=UUID(item_id))
    except (ValueError, binascii.Error, UnicodeDecodeError) as error:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST, "invalid_cursor", "The page cursor is not valid."
        ) from error


LimitQuery = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]
CursorQuery = Annotated[str | None, Query(max_length=200)]
