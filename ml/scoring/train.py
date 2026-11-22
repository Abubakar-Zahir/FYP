"""Evaluates and trains the hook scorer from a JSONL export of real reels.

    PYTHONPATH=apps/api:. uv run python apps/api/scripts/export_hook_dataset.py data/hooks.jsonl
    uv run python -m ml.scoring.train data/hooks.jsonl --out data/models/hook_scorer

Prints the creator-split report (both baselines, both ablations), then trains the final model
on all hooks and saves it for HOOK_SCORER_PATH. Report correlation, never accuracy (SRS risks).
"""

import argparse
import json
from pathlib import Path

from ml.dna.schema import HookType
from ml.scoring.evaluate import full_report
from ml.scoring.model import HookExample, HookScorer

REPORT_FILE = "report.json"


def read_examples(path: Path) -> list[HookExample]:
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        examples.append(
            HookExample(
                text=str(row["text"]),
                hook_type=HookType(row["hook_type"]) if row.get("hook_type") else None,
                creator=str(row["creator"]),
                outlier_score=float(row["outlier_score"]),
            )
        )
    return examples


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("dataset", type=Path)
    arguments.add_argument("--out", type=Path, default=Path("data/models/hook_scorer"))
    args = arguments.parse_args()
    examples = read_examples(args.dataset)
    reports = full_report(examples)
    for report in reports:
        print(f"{report.model}: Spearman {report.spearman} ({report.spearman_low} to {report.spearman_high})")
    model = HookScorer.train(examples, with_wording=True)
    model.save(args.out)
    (args.out / REPORT_FILE).write_text(
        json.dumps([r.model_dump() for r in reports], indent=2), encoding="utf-8"
    )
    print(f"Saved {model.version} to {args.out}")


if __name__ == "__main__":
    main()
