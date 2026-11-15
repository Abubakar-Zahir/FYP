"""Async client for the Instagram API with Instagram Login.

Ported from spikes/instagram/ig_client.py. Endpoints, scopes and fields follow Meta's docs
as read on 2026-11-03. The spike README lists what the first real run must confirm.
Publishing stays in the spike until Phase 3.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
SHORT_LIVED_TOKEN_URL = "https://api.instagram.com/oauth/access_token"  # noqa: S105
GRAPH_HOST = "https://graph.instagram.com"
API_VERSION = "v26.0"
GRAPH_URL = f"{GRAPH_HOST}/{API_VERSION}"
HTTP_TIMEOUT_S = 30.0

SCOPES = (
    "instagram_business_basic",
    "instagram_business_content_publish",
    "instagram_business_manage_insights",
    "instagram_business_manage_comments",
)
REEL_METRICS = ("views", "reach", "saved", "shares", "total_interactions", "ig_reels_avg_watch_time")
REEL_PRODUCT_TYPE = "REELS"
MEDIA_PAGE_SIZE = 50
COMMENTS_PAGE_SIZE = 50
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class InstagramError(Exception):
    """Carries Meta's message only. Request URLs hold the token, so they never appear here."""


class InstagramUnavailable(InstagramError):
    """Timeouts, rate limits and server errors. Worth retrying later."""


class ShortLivedToken(BaseModel):
    access_token: str
    user_id: str


class LongLivedToken(BaseModel):
    access_token: str
    expires_in: int

    def expires_at(self, now: datetime) -> datetime:
        return now.astimezone(UTC) + timedelta(seconds=self.expires_in)


class Account(BaseModel):
    user_id: str
    username: str
    account_type: str
    media_count: int | None = None


class Media(BaseModel):
    id: str
    media_type: str
    media_product_type: str | None = None
    caption: str | None = None
    permalink: str | None = None
    timestamp: str | None = None


class Comment(BaseModel):
    id: str
    text: str
    timestamp: str | None = None


def build_authorize_url(app_id: str, redirect_uri: str, state: str) -> str:
    query = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ",".join(SCOPES),
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(query)}"


def clean_authorization_code(code: str) -> str:
    """Instagram appends `#_` to the redirect, and it is not part of the code."""
    return code.removesuffix("#_")


def _body(response: httpx.Response) -> dict[str, Any]:
    if response.status_code in RETRYABLE_STATUS_CODES:
        raise InstagramUnavailable(f"Instagram answered {response.status_code}")
    try:
        body = response.json()
    except ValueError as error:
        raise InstagramError(f"Non-JSON response, status {response.status_code}") from error
    if response.is_error or "error" in body:
        details = body.get("error") if isinstance(body.get("error"), dict) else body
        message = details.get("message") or details.get("error_message") or "unknown error"
        raise InstagramError(f"Status {response.status_code}: {message}")
    # Any: Meta's JSON, validated into the models above by each caller.
    result: dict[str, Any] = body
    return result


async def _send(http: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    try:
        response = await http.request(method, url, timeout=HTTP_TIMEOUT_S, **kwargs)
    except httpx.TransportError as error:
        raise InstagramUnavailable("Instagram could not be reached") from error
    return _body(response)


async def exchange_code(
    http: httpx.AsyncClient, app_id: str, app_secret: str, redirect_uri: str, code: str
) -> ShortLivedToken:
    body = await _send(
        http,
        "POST",
        SHORT_LIVED_TOKEN_URL,
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": clean_authorization_code(code),
        },
    )
    # Meta has returned this both flat and wrapped in `data`.
    entry = body["data"][0] if "data" in body else body
    return ShortLivedToken(access_token=entry["access_token"], user_id=str(entry["user_id"]))


async def exchange_for_long_lived(
    http: httpx.AsyncClient, app_secret: str, short_lived_token: str
) -> LongLivedToken:
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": app_secret,
        "access_token": short_lived_token,
    }
    return LongLivedToken.model_validate(
        await _send(http, "GET", f"{GRAPH_HOST}/access_token", params=params)
    )


async def refresh_long_lived(http: httpx.AsyncClient, token: str) -> LongLivedToken:
    params = {"grant_type": "ig_refresh_token", "access_token": token}
    return LongLivedToken.model_validate(
        await _send(http, "GET", f"{GRAPH_HOST}/refresh_access_token", params=params)
    )


class InstagramClient:
    def __init__(self, http: httpx.AsyncClient, token: str) -> None:
        self._http = http
        self._token = token

    async def _get(self, path: str, **params: str | int) -> dict[str, Any]:
        return await _send(
            self._http, "GET", f"{GRAPH_URL}/{path}", params={**params, "access_token": self._token}
        )

    async def account(self) -> Account:
        return Account.model_validate(
            await self._get("me", fields="user_id,username,account_type,media_count")
        )

    async def recent_reels(self, limit: int) -> list[Media]:
        fields = "id,caption,media_type,media_product_type,permalink,timestamp"
        reels: list[Media] = []
        params: dict[str, str | int] = {"fields": fields, "limit": MEDIA_PAGE_SIZE}
        while len(reels) < limit:
            body = await self._get("me/media", **params)
            media = [Media.model_validate(item) for item in body.get("data", [])]
            # Published reels report media_type VIDEO. Only media_product_type identifies them.
            reels += [item for item in media if item.media_product_type == REEL_PRODUCT_TYPE]
            after = body.get("paging", {}).get("cursors", {}).get("after")
            if not after or not body.get("paging", {}).get("next"):
                break
            params["after"] = after
        return reels[:limit]

    async def reel_insights(self, media_id: str) -> dict[str, float]:
        """Empty data means unavailable, not zero, and values can lag by up to 48 hours."""
        body = await self._get(f"{media_id}/insights", metric=",".join(REEL_METRICS))
        return {
            item["name"]: float(item["values"][0]["value"])
            for item in body.get("data", [])
            if item.get("values")
        }

    async def comments(self, media_id: str) -> list[Comment]:
        body = await self._get(f"{media_id}/comments", fields="id,text,timestamp", limit=COMMENTS_PAGE_SIZE)
        return [Comment.model_validate(item) for item in body.get("data", [])]

    async def media_url(self, media_id: str) -> str:
        """A fresh download link for one of the account's own videos. These links expire."""
        body = await self._get(media_id, fields="media_url")
        url = body.get("media_url")
        if not isinstance(url, str):
            raise InstagramError("No media_url for this media")
        return url
