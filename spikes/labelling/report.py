"""Prints Cohen's kappa for two labellers from a Label Studio JSON export.

Run from the repo root: PYTHONPATH=. uv run python spikes/labelling/report.py export.json 1 2
"""

import argparse
import json
from pathlib import Path

from ml.comments.agreement import cohen_kappa, paired_labels


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("export", type=Path, help="Label Studio export in JSON format")
    arguments.add_argument("first_labeller", type=int, help="Label Studio user id")
    arguments.add_argument("second_labeller", type=int, help="Label Studio user id")
    args = arguments.parse_args()

    tasks = json.loads(args.export.read_text(encoding="utf-8"))
    first, second = paired_labels(tasks, args.first_labeller, args.second_labeller)
    if not first:
        raise SystemExit("These two labellers share no completed comments.")
    print(f"Shared comments: {len(first)}")
    print(f"Cohen's kappa: {cohen_kappa(first, second):.3f}")


if __name__ == "__main__":
    main()
