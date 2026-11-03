# /// script
# requires-python = "==3.12.*"
# dependencies = ["httpx>=0.27", "pydantic>=2.9"]
# ///
"""Runs the Instagram spike against a real account. See README.md."""

import argparse
import os
import secrets
import time
from pathlib import Path

import httpx
from ig_client import (
    GraduationStrategy,
    InstagramClient,
    build_authorize_url,
    exchange_code,
    exchange_for_long_lived,
)

CREDENTIALS_FILE = Path(__file__).parent / ".env.instagram"
HTTP_TIMEOUT_SECONDS = 60.0
REELS_TO_IMPORT = 50


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Set {name} first. See spikes/instagram/README.md.")
    return value


def save_credentials(token: str, user_id: str) -> None:
    CREDENTIALS_FILE.touch(mode=0o600)
    CREDENTIALS_FILE.write_text(f"IG_ACCESS_TOKEN={token}\nIG_USER_ID={user_id}\n")


def load_credentials() -> dict[str, str]:
    if not CREDENTIALS_FILE.exists():
        raise SystemExit("No saved token. Run the `login` and `exchange` commands first.")
    lines = CREDENTIALS_FILE.read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line)


def client(http: httpx.Client) -> tuple[InstagramClient, str]:
    credentials = load_credentials()
    return InstagramClient(http, credentials["IG_ACCESS_TOKEN"], time.sleep), credentials["IG_USER_ID"]


def cmd_login(_: argparse.Namespace, __: httpx.Client) -> None:
    state = secrets.token_urlsafe(16)
    print(build_authorize_url(require_env("IG_APP_ID"), require_env("IG_REDIRECT_URI"), state))
    print(f"\nOpen the URL, approve, then check that the redirect's state is: {state}")


def cmd_exchange(args: argparse.Namespace, http: httpx.Client) -> None:
    app_secret = require_env("IG_APP_SECRET")
    short = exchange_code(
        http, require_env("IG_APP_ID"), app_secret, require_env("IG_REDIRECT_URI"), args.code
    )
    long_lived = exchange_for_long_lived(http, app_secret, short.access_token)
    save_credentials(long_lived.access_token, short.user_id)
    print(f"Saved to {CREDENTIALS_FILE.name}. Token expires in {long_lived.expires_in // 86400} days.")


def cmd_account(_: argparse.Namespace, http: httpx.Client) -> None:
    ig, _user_id = client(http)
    print(ig.account().model_dump())


def cmd_import(_: argparse.Namespace, http: httpx.Client) -> None:
    """Prints counts and metric names only, so comments and captions stay out of terminal logs."""
    ig, _user_id = client(http)
    reels = ig.recent_reels(REELS_TO_IMPORT)
    print(f"Reels found: {len(reels)}")
    if not reels:
        return
    first = reels[0]
    print(f"Metrics on the newest reel: {sorted(ig.reel_insights(first.id))}")
    print(f"Comments on the newest reel: {len(ig.comments(first.id))}")


def cmd_limit(_: argparse.Namespace, http: httpx.Client) -> None:
    ig, user_id = client(http)
    print(ig.publishing_limit(user_id).model_dump())


def cmd_publish(args: argparse.Namespace, http: httpx.Client) -> None:
    ig, user_id = client(http)
    print(f"Publishing limit before: {ig.publishing_limit(user_id).model_dump()}")
    trial = None if args.normal else GraduationStrategy(args.graduation)
    container_id = ig.create_reel_container(user_id, args.video_url, args.caption, trial)
    print(f"Container {container_id} created. Waiting for processing, checked once a minute.")
    ig.wait_until_finished(container_id)
    media_id = ig.publish(user_id, container_id)
    kind = "a normal reel" if trial is None else f"a Trial Reel ({trial.value})"
    print(f"Published media {media_id} as {kind}.")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(required=True)
    commands.add_parser("login", help="print the authorization URL").set_defaults(run=cmd_login)
    exchange = commands.add_parser("exchange", help="trade the code for a long-lived token")
    exchange.add_argument("code")
    exchange.set_defaults(run=cmd_exchange)
    commands.add_parser("account", help="show the connected account").set_defaults(run=cmd_account)
    commands.add_parser("import", help="read reels, insights and comments").set_defaults(run=cmd_import)
    commands.add_parser("limit", help="show publishing quota").set_defaults(run=cmd_limit)
    publish = commands.add_parser("publish", help="publish one reel from a public video URL")
    publish.add_argument("video_url")
    publish.add_argument("caption")
    publish.add_argument(
        "--graduation", choices=[item.value for item in GraduationStrategy], default="MANUAL"
    )
    publish.add_argument("--normal", action="store_true", help="publish a normal reel, the FR-6.8 fallback")
    publish.set_defaults(run=cmd_publish)
    return root


def main() -> None:
    args = parser().parse_args()
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as http:
        args.run(args, http)


if __name__ == "__main__":
    main()
