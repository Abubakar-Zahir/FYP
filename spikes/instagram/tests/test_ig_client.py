import json
from collections.abc import Callable

import httpx
import pytest

from spikes.instagram.ig_client import (
    STATUS_MAX_POLLS,
    GraduationStrategy,
    InstagramClient,
    InstagramError,
)

TOKEN = "secret-token"  # noqa: S105
IG_ID = "17841400000000000"
Handler = Callable[[httpx.Request], httpx.Response]


def make_client(handler: Handler, sleeps: list[float] | None = None) -> InstagramClient:
    recorded = sleeps if sleeps is not None else []
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return InstagramClient(http, TOKEN, recorded.append)


def recording(body: dict[str, object], requests: list[httpx.Request]) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=body)

    return handler


def test_calls_go_to_the_facebook_graph_host() -> None:
    requests: list[httpx.Request] = []

    make_client(recording({"data": []}, requests)).assigned_accounts()

    assert requests[0].url.host == "graph.facebook.com"
    assert requests[0].url.path == "/v27.0/me/assigned_instagram_accounts"


def test_assigned_accounts_lists_id_and_username() -> None:
    body = {"data": [{"id": IG_ID, "username": "test.account"}]}

    accounts = make_client(lambda _: httpx.Response(200, json=body)).assigned_accounts()

    assert [(account.id, account.username) for account in accounts] == [(IG_ID, "test.account")]


def test_account_reads_the_instagram_id_not_me() -> None:
    requests: list[httpx.Request] = []
    body = {"id": IG_ID, "username": "test.account", "followers_count": 1200, "media_count": 40}

    account = make_client(recording(body, requests)).account(IG_ID)

    assert requests[0].url.path == f"/v27.0/{IG_ID}"
    assert account.followers_count == 1200


def test_recent_reels_reads_the_instagram_id_not_me() -> None:
    requests: list[httpx.Request] = []

    make_client(recording({"data": []}, requests)).recent_reels(IG_ID, 10)

    assert requests[0].url.path == f"/v27.0/{IG_ID}/media"


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
        client.account(IG_ID)

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
                "paging": {"cursors": {"after": "abc"}, "next": "https://graph.facebook.com/next"},
            },
            {"data": [{"id": "3", "media_type": "VIDEO", "media_product_type": "REELS"}]},
        ]
    )
    client = make_client(lambda _: httpx.Response(200, json=next(pages)))

    assert [reel.id for reel in client.recent_reels(IG_ID, 10)] == ["1", "3"]


def test_insights_treat_missing_values_as_unavailable() -> None:
    body = {"data": [{"name": "views", "values": [{"value": 12}]}, {"name": "reach", "values": []}]}
    client = make_client(lambda _: httpx.Response(200, json=body))

    assert client.reel_insights("1") == {"views": 12}
