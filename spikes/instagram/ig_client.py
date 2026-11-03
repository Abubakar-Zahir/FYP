"""Minimal client for the Instagram API with Instagram Login.

Endpoints, scopes and fields follow Meta's docs, read on 2026-11-03. The README
lists the ones the docs did not fully confirm for this login type.
"""

from collections.abc import Callable
from enum import StrEnum
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
SHORT_LIVED_TOKEN_URL = "https://api.instagram.com/oauth/access_token"  # noqa: S105
GRAPH_HOST = "https://graph.instagram.com"
API_VERSION = "v26.0"
GRAPH_URL = f"{GRAPH_HOST}/{API_VERSION}"

SCOPES = (
    "instagram_business_basic",
    "instagram_business_content_publish",
    "instagram_business_manage_insights",
    "instagram_business_manage_comments",
)
REEL_METRICS = ("views", "reach", "saved", "shares", "total_interactions", "ig_reels_avg_watch_time")
REEL_PRODUCT_TYPE = "REELS"
MEDIA_PAGE_SIZE = 50

# Meta recommends checking once per minute for no more than 5 minutes.
STATUS_POLL_SECONDS = 60
STATUS_MAX_POLLS = 5
FINISHED_STATUS = "FINISHED"
FAILED_STATUSES = frozenset({"ERROR", "EXPIRED"})


class GraduationStrategy(StrEnum):
    MANUAL = "MANUAL"
    SS_PERFORMANCE = "SS_PERFORMANCE"


class InstagramError(Exception):
    """Carries Meta's message only. The request URL holds the token, so it must never appear here."""


class ShortLivedToken(BaseModel):
    access_token: str
    user_id: str


class LongLivedToken(BaseModel):
    access_token: str
    expires_in: int


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


class PublishingLimit(BaseModel):
    quota_usage: int
    quota_total: int | None = None


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
    try:
        body = response.json()
    except ValueError as error:
        raise InstagramError(f"Non-JSON response, status {response.status_code}") from error
    if response.is_error or "error" in body:
        details = body.get("error") if isinstance(body.get("error"), dict) else body
        message = details.get("message") or details.get("error_message") or "unknown error"
        raise InstagramError(f"Status {response.status_code}: {message}")
    result: dict[str, Any] = body
    return result


def exchange_code(
    http: httpx.Client, app_id: str, app_secret: str, redirect_uri: str, code: str
) -> ShortLivedToken:
    response = http.post(
        SHORT_LIVED_TOKEN_URL,
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": clean_authorization_code(code),
        },
    )
    body = _body(response)
    # Meta has returned this both flat and wrapped in `data`.
    entry = body["data"][0] if "data" in body else body
    return ShortLivedToken(access_token=entry["access_token"], user_id=str(entry["user_id"]))


def exchange_for_long_lived(http: httpx.Client, app_secret: str, short_lived_token: str) -> LongLivedToken:
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": app_secret,
        "access_token": short_lived_token,
    }
    return LongLivedToken.model_validate(_body(http.get(f"{GRAPH_HOST}/access_token", params=params)))


def refresh_long_lived(http: httpx.Client, token: str) -> LongLivedToken:
    params = {"grant_type": "ig_refresh_token", "access_token": token}
    return LongLivedToken.model_validate(_body(http.get(f"{GRAPH_HOST}/refresh_access_token", params=params)))


class InstagramClient:
    def __init__(self, http: httpx.Client, token: str, sleep: Callable[[float], None]) -> None:
        self._http = http
        self._token = token
        self._sleep = sleep

    def _get(self, path: str, **params: str | int) -> dict[str, Any]:
        return _body(self._http.get(f"{GRAPH_URL}/{path}", params={**params, "access_token": self._token}))

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return _body(
            self._http.post(f"{GRAPH_URL}/{path}", params={"access_token": self._token}, json=payload)
        )

    def account(self) -> Account:
        return Account.model_validate(self._get("me", fields="user_id,username,account_type,media_count"))

    def recent_reels(self, limit: int) -> list[Media]:
        fields = "id,caption,media_type,media_product_type,permalink,timestamp"
        reels: list[Media] = []
        params: dict[str, str | int] = {"fields": fields, "limit": MEDIA_PAGE_SIZE}
        while len(reels) < limit:
            body = self._get("me/media", **params)
            media = [Media.model_validate(item) for item in body.get("data", [])]
            # Published reels report media_type VIDEO. Only media_product_type identifies them.
            reels += [item for item in media if item.media_product_type == REEL_PRODUCT_TYPE]
            after = body.get("paging", {}).get("cursors", {}).get("after")
            if not after or not body.get("paging", {}).get("next"):
                break
            params["after"] = after
        return reels[:limit]

    def reel_insights(self, media_id: str) -> dict[str, int | float]:
        """Empty data means unavailable, not zero, and values can lag by up to 48 hours."""
        body = self._get(f"{media_id}/insights", metric=",".join(REEL_METRICS))
        return {
            item["name"]: item["values"][0]["value"] for item in body.get("data", []) if item.get("values")
        }

    def comments(self, media_id: str) -> list[Comment]:
        body = self._get(f"{media_id}/comments", fields="id,text,timestamp")
        return [Comment.model_validate(item) for item in body.get("data", [])]

    def publishing_limit(self, ig_id: str) -> PublishingLimit:
        body = self._get(f"{ig_id}/content_publishing_limit", fields="quota_usage,config")
        entry = body["data"][0]
        return PublishingLimit(
            quota_usage=entry["quota_usage"],
            quota_total=entry.get("config", {}).get("quota_total"),
        )

    def create_reel_container(
        self, ig_id: str, video_url: str, caption: str, trial: GraduationStrategy | None
    ) -> str:
        payload: dict[str, Any] = {"media_type": "REELS", "video_url": video_url, "caption": caption}
        if trial is not None:
            payload["trial_params"] = {"graduation_strategy": trial.value}
        return str(self._post(f"{ig_id}/media", payload)["id"])

    def wait_until_finished(self, container_id: str) -> None:
        last_status = "unknown"
        for attempt in range(STATUS_MAX_POLLS):
            if attempt > 0:
                self._sleep(STATUS_POLL_SECONDS)
            last_status = str(self._get(container_id, fields="status_code").get("status_code"))
            if last_status == FINISHED_STATUS:
                return
            if last_status in FAILED_STATUSES:
                raise InstagramError(f"Container ended with status {last_status}")
        raise InstagramError(f"Container still {last_status} after {STATUS_MAX_POLLS} checks")

    def publish(self, ig_id: str, container_id: str) -> str:
        return str(self._post(f"{ig_id}/media_publish", {"creation_id": container_id})["id"])
