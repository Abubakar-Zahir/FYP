"""Writes the API's OpenAPI schema, which the web app generates its types from (rules.md 4.5).

Run from the repo root:

    PYTHONPATH=apps/api:. uv run python apps/api/scripts/export_openapi.py apps/web/openapi.json

No server, database or secret is needed. CI fails if the committed file is out of date.
"""

import argparse
import json
from pathlib import Path

from app.core.settings import Settings
from app.main import create_app


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("output", type=Path)
    output: Path = arguments.parse_args().output
    schema = create_app(Settings()).openapi()
    output.write_text(
        json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
