"""Trains and evaluates the CPU comment models on a Label Studio export.

    uv run python -m ml.comments.train data/labels/comments.json --out data/models/comments

Writes the main model (`char_ngram.joblib`) and `report.json` with both models' held-out
scores. The LLM zero-shot baseline is scored by apps/api/scripts/evaluate_zero_shot.py,
because it needs the budget-guarded LLM client. Never commit the export or the model.
"""

import argparse
import json
from pathlib import Path

from ml.comments.dataset import from_label_studio, split_by_group
from ml.comments.evaluate import EvaluationReport, evaluate
from ml.comments.models import CharNgramClassifier, EnglishOnlyBaseline

MAIN_MODEL_FILE = "char_ngram.joblib"
REPORT_FILE = "report.json"


def train_and_report(tasks: list[dict[str, object]], out: Path) -> list[EvaluationReport]:
    items = from_label_studio(tasks)
    train, test = split_by_group(items)
    if not train or not test:
        raise SystemExit("Too few labelled comments to split into train and test")
    truth = [item.label.value for item in test]
    texts = [item.text for item in test]
    reports = []
    for model in (CharNgramClassifier(), EnglishOnlyBaseline()):
        model.fit(train)
        reports.append(evaluate(model.name, truth, [label.value for label in model.predict(texts)]))
        if isinstance(model, CharNgramClassifier):
            model.save(out / MAIN_MODEL_FILE)
    summary = {
        "train_size": len(train),
        "test_size": len(test),
        "split": "by reel, sha256 bucket, seed v1, 20% test",
        "reports": [report.model_dump() for report in reports],
    }
    (out / REPORT_FILE).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return reports


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("export", type=Path, help="Label Studio JSON export")
    arguments.add_argument("--out", type=Path, default=Path("data/models/comments"))
    args = arguments.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    tasks = json.loads(args.export.read_text(encoding="utf-8"))
    for report in train_and_report(tasks, args.out):
        print(f"{report.model}: macro F1 {report.macro_f1} ({report.macro_f1_low} to {report.macro_f1_high})")


if __name__ == "__main__":
    main()
