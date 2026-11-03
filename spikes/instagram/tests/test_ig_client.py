import json
from collections.abc import Callable
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from spikes.instagram.ig_client import (
    STATUS_MAX_POLLS,
    GraduationStrategy,
    InstagramClient,
    InstagramError,
    build_authorize_url,
    clean_authorization_code,
    exchange_code,
)

TOKEN = "secret-token"  # noqa: S105
Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler, sleeps: list[float] | None = None) -> InstagramClient:
    recorded = sleeps if sleeps is not None else []
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return InstagramClient(http, TOKEN, recorded.append)


def test_authorize_url_requests_every_scope() -> None:
    query = parse_qs(urlparse(build_authorize_url("app", "https://x.dev/cb", "st")).query)

    assert query["response_type"] == ["code"]
    assert query["state"] == ["st"]
    assert "instagram_business_content_publish" in query["scope"][0]
    assert "instagram_business_manage_insights" in query["scope"][0]


def test_clean_authorization_code_strips_fragment() -> None:
    assert clean_authorization_code("abc#_") == "abc"


@pytest.mark.parametrize(
    "body",
    [
        {"access_token": "t", "user_id": 7},
        {"data": [{"access_token": "t", "user_id": 7, "permissions": "x"}]},
    ],
)
def test_exchange_code_accepts_both_shapes(body: dict[str, object]) -> None:
    http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)))

    token = exchange_code(http, "app", "secret", "https://x.dev/cb", "abc#_")

    assert token.user_id == "7"


def test_trial_container_sends_trial_params() -> None:
    sent: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"id": "c1"})

    container = make_client(handler).create_reel_container(
        "9", "https://v/a.mp4", "hi", GraduationStrategy.MANUAL
    )

    assert container == "c1"
    assert sent["media_type"] == "REELS"
    assert sent["trial_params"] == {"graduation_strategy": "MANUAL"}


def test_normal_reel_omits_trial_params() -> None:
    sent: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"id": "c1"})

    make_client(handler).create_reel_container("9", "https://v/a.mp4", "hi", None)

    assert "trial_params" not in sent


def test_wait_polls_until_finished() -> None:
    statuses = iter(["IN_PROGRESS", "FINISHED"])
    sleeps: list[float] = []
    client = make_client(lambda _: httpx.Response(200, json={"status_code": next(statuses)}), sleeps)

    client.wait_until_finished("c1")

    assert sleeps == [60]


def test_wait_stops_on_error_status() -> None:
    client = make_client(lambda _: httpx.Response(200, json={"status_code": "ERROR"}))

    with pytest.raises(InstagramError, match="ERROR"):
        client.wait_until_finished("c1")


def test_wait_gives_up_after_max_polls() -> None:
    sleeps: list[float] = []
    client = make_client(lambda _: httpx.Response(200, json={"status_code": "IN_PROGRESS"}), sleeps)

    with pytest.raises(InstagramError, match="IN_PROGRESS"):
        client.wait_until_finished("c1")

    assert len(sleeps) == STATUS_MAX_POLLS - 1


def test_errors_never_contain_the_token() -> None:
    client = make_client(
        lambda _: httpx.Response(400, json={"error": {"message": "bad request", "code": 100}})
    )

    with pytest.raises(InstagramError) as caught:
        client.account()

    assert "bad request" in str(caught.value)
    assert TOKEN not in str(caught.value)


def test_recent_reels_keeps_only_reels_and_follows_pages() -> None:
    pages = iter(
        [
            {
                "data": [
                    {"id": "1", "media_type": "VIDEO", "media_product_type": "REELS"},
                    {"id": "2", "media_type": "IMAGE", "media_product_type": "FEED"},
                ],
                "paging": {"cursors": {"after": "abc"}, "next": "https://graph.instagram.com/next"},
            },
            {"data": [{"id": "3", "media_type": "VIDEO", "media_product_type": "REELS"}]},
        ]
    )
    client = make_client(lambda _: httpx.Response(200, json=next(pages)))

    assert [reel.id for reel in client.recent_reels(10)] == ["1", "3"]


def test_insights_treat_missing_values_as_unavailable() -> None:
    body = {"data": [{"name": "views", "values": [{"value": 12}]}, {"name": "reach", "values": []}]}
    client = make_client(lambda _: httpx.Response(200, json=body))

    assert client.reel_insights("1") == {"views": 12}
