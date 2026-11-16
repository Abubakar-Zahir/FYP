# /// script
# requires-python = "==3.12.*"
# dependencies = ["httpx>=0.27", "pydantic>=2.9"]
# ///
"""Runs the Instagram spike against a real account. See README.md."""

import argparse
import time
from pathlib import Path

import httpx
from ig_client import GraduationStrategy, InstagramClient

# Written by hand from the README, never by this script, so the token is never printed.
CREDENTIALS_FILE = Path(__file__).parent / ".env.instagram"
TOKEN_KEY = "IG_ACCESS_TOKEN"  # noqa: S105
USER_ID_KEY = "IG_USER_ID"
HTTP_TIMEOUT_SECONDS = 60.0
REELS_TO_IMPORT = 50


def load_credentials() -> dict[str, str]:
    if not CREDENTIALS_FILE.exists():
        raise SystemExit(f"No {CREDENTIALS_FILE.name} file. Create it as spikes/instagram/README.md shows.")
    lines = CREDENTIALS_FILE.read_text(encoding="utf-8-sig").splitlines()
    pairs = (line.split("=", 1) for line in lines if "=" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def credential(credentials: dict[str, str], key: str) -> str:
    value = credentials.get(key)
    if not value:
        raise SystemExit(f"{key} is missing from {CREDENTIALS_FILE.name}.")
    return value


def client(http: httpx.Client) -> tuple[InstagramClient, str]:
    """The client plus the Instagram account id that every call except `accounts` needs."""
    credentials = load_credentials()
    ig = InstagramClient(http, credential(credentials, TOKEN_KEY), time.sleep)
    return ig, credential(credentials, USER_ID_KEY)


def cmd_accounts(_: argparse.Namespace, http: httpx.Client) -> None:
    token = credential(load_credentials(), TOKEN_KEY)
    for account in InstagramClient(http, token, time.sleep).assigned_accounts():
        print(account.model_dump())


def cmd_account(_: argparse.Namespace, http: httpx.Client) -> None:
    ig, user_id = client(http)
    print(ig.account(user_id).model_dump())


def cmd_import(_: argparse.Namespace, http: httpx.Client) -> None:
    """Prints counts and metric names only, so comments and captions stay out of terminal logs."""
    ig, user_id = client(http)
    reels = ig.recent_reels(user_id, REELS_TO_IMPORT)
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
    commands.add_parser("accounts", help="list the Instagram accounts the token may use").set_defaults(
        run=cmd_accounts
    )
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
