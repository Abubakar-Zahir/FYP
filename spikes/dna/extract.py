# /// script
# requires-python = "==3.12.*"
# dependencies = [
#     "av>=17,<18",
#     "faster-whisper>=1.1",
#     "opencv-python-headless>=4.10",
#     "pydantic>=2.9",
#     "scenedetect>=0.7.2",
# ]
# ///
"""Extracts ReelSignals from each video in a folder. Run from the repo root, see README.md.

The extraction itself lives in ml/dna/extract.py, which the DNA worker also uses.
"""

import argparse
import json
import time
from pathlib import Path

from ml.dna.extract import DEFAULT_CUT_THRESHOLD, DEFAULT_WHISPER_MODEL, ExtractOptions, Extractor

VIDEO_SUFFIXES = {".mp4", ".mov"}


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument(
        "videos", type=Path, help="folder of reels. Keep it under data/, which git ignores"
    )
    arguments.add_argument("--output", type=Path, default=Path("data/dna_spike"))
    arguments.add_argument("--model", default=DEFAULT_WHISPER_MODEL)
    arguments.add_argument("--language", default=None, help="for example ur or en. Default: auto-detect")
    arguments.add_argument(
        "--threshold", type=float, default=DEFAULT_CUT_THRESHOLD, help="lower finds more cuts"
    )
    args = arguments.parse_args()

    paths = sorted(path for path in args.videos.iterdir() if path.suffix.lower() in VIDEO_SUFFIXES)
    if not paths:
        raise SystemExit(f"No .mp4 or .mov files in {args.videos}")

    extractor = Extractor(
        ExtractOptions(whisper_model=args.model, language=args.language, cut_threshold=args.threshold)
    )
    args.output.mkdir(parents=True, exist_ok=True)
    timings = []
    for path in paths:
        started = time.perf_counter()
        signals = extractor.extract(path, args.output / path.stem)
        elapsed = round(time.perf_counter() - started, 1)
        (args.output / f"{path.stem}.json").write_text(signals.model_dump_json(indent=2))
        timings.append({"reel": path.name, "length_s": signals.length_s, "seconds_to_process": elapsed})
        print(f"{path.name}: {signals.length_s}s, {len(signals.cut_times_s)} cuts, processed in {elapsed}s")
    (args.output / "timings.json").write_text(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
