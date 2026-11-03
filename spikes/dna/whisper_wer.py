# /// script
# requires-python = "==3.12.*"
# dependencies = ["av>=17,<18", "faster-whisper>=1.1"]
# ///
"""Measures Whisper word error rate per language from a labelled manifest. See README.md."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from faster_whisper import WhisperModel

from ml.common.metrics import corpus_wer

COMPUTE_TYPE = "int8"
REQUIRED_COLUMNS = {"audio_path", "group", "whisper_language", "reference"}


def transcribe(model: WhisperModel, path: Path, language: str | None) -> str:
    segments, _ = model.transcribe(str(path), language=language or None)
    return " ".join(segment.text.strip() for segment in segments)


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument(
        "manifest", type=Path, help="CSV with audio_path, group, whisper_language, reference"
    )
    arguments.add_argument("--model", default="small")
    arguments.add_argument("--output", type=Path, default=Path("data/wer_results.json"))
    args = arguments.parse_args()

    with args.manifest.open(newline="", encoding="utf-8") as manifest:
        rows = list(csv.DictReader(manifest))
    if not rows or not REQUIRED_COLUMNS <= set(rows[0]):
        raise SystemExit(f"The manifest needs these columns: {sorted(REQUIRED_COLUMNS)}")

    model = WhisperModel(args.model, device="cpu", compute_type=COMPUTE_TYPE)
    pairs_by_group: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in rows:
        audio_path = args.manifest.parent / row["audio_path"]
        hypothesis = transcribe(model, audio_path, row["whisper_language"])
        pairs_by_group[row["group"]].append((row["reference"], hypothesis))

    report = {
        "model": f"faster-whisper-{args.model}+{COMPUTE_TYPE}",
        "manifest": args.manifest.name,
        "metric": "corpus WER: total word errors / total reference words",
        "groups": {},
    }
    for group, pairs in sorted(pairs_by_group.items()):
        result = corpus_wer(pairs)
        report["groups"][group] = {
            "clips": len(pairs),
            "reference_words": result.reference_words,
            "errors": result.errors,
            "wer": round(result.wer, 4),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
