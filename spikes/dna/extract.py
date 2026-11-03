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
"""Extracts ReelSignals from each video in a folder. Run from the repo root, see README.md."""

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
from faster_whisper import WhisperModel
from scenedetect import ContentDetector, detect

from ml.dna.schema import ReelSignals, TranscriptSegment
from ml.dna.signals import cuts_per_window, hook_candidate

VIDEO_SUFFIXES = {".mp4", ".mov"}
COMPUTE_TYPE = "int8"
# PySceneDetect's default. It averages hue, saturation and brightness change, so a cut
# between scenes of similar brightness can score under this and be missed.
DEFAULT_CUT_THRESHOLD = 27.0


@dataclass(frozen=True)
class Scenes:
    length_s: float
    cut_times_s: list[float]
    midpoints_s: list[float]


def video_length_s(path: Path) -> float:
    capture = cv2.VideoCapture(str(path))
    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    finally:
        capture.release()
    if fps <= 0:
        raise ValueError(f"Could not read video: {path.name}")
    return float(frames / fps)


def detect_scenes(path: Path, threshold: float) -> Scenes:
    length_s = video_length_s(path)
    scenes = detect(str(path), ContentDetector(threshold=threshold))
    bounds = [(start.seconds, end.seconds) for start, end in scenes] or [(0.0, length_s)]
    return Scenes(
        length_s=length_s,
        cut_times_s=[round(start, 3) for start, _ in bounds[1:]],
        midpoints_s=[(start + end) / 2 for start, end in bounds],
    )


def save_keyframes(path: Path, midpoints_s: list[float], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(path))
    saved: list[str] = []
    try:
        for index, midpoint in enumerate(midpoints_s):
            capture.set(cv2.CAP_PROP_POS_MSEC, midpoint * 1000)
            ok, frame = capture.read()
            if ok:
                frame_path = output_dir / f"scene_{index:03d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                saved.append(str(frame_path))
    finally:
        capture.release()
    return saved


def transcribe(model: WhisperModel, path: Path, language: str | None) -> tuple[list[TranscriptSegment], str]:
    segments, info = model.transcribe(str(path), language=language, word_timestamps=True)
    transcript = [TranscriptSegment(start_s=item.start, end_s=item.end, text=item.text) for item in segments]
    return transcript, info.language


def extract(model: WhisperModel, path: Path, args: argparse.Namespace) -> ReelSignals:
    scenes = detect_scenes(path, args.threshold)
    transcript, detected_language = transcribe(model, path, args.language)
    return ReelSignals(
        length_s=round(scenes.length_s, 3),
        cut_times_s=scenes.cut_times_s,
        pacing_cuts_per_10s=cuts_per_window(scenes.cut_times_s, scenes.length_s),
        detected_language=detected_language,
        transcript=transcript,
        hook_candidate_text=hook_candidate(transcript),
        keyframe_paths=save_keyframes(path, scenes.midpoints_s, args.output / path.stem),
        model_version=f"faster-whisper-{args.model}+{COMPUTE_TYPE}",
    )


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument(
        "videos", type=Path, help="folder of reels. Keep it under data/, which git ignores"
    )
    arguments.add_argument("--output", type=Path, default=Path("data/dna_spike"))
    arguments.add_argument("--model", default="small")
    arguments.add_argument("--language", default=None, help="for example ur or en. Default: auto-detect")
    arguments.add_argument(
        "--threshold", type=float, default=DEFAULT_CUT_THRESHOLD, help="lower finds more cuts"
    )
    args = arguments.parse_args()

    paths = sorted(path for path in args.videos.iterdir() if path.suffix.lower() in VIDEO_SUFFIXES)
    if not paths:
        raise SystemExit(f"No .mp4 or .mov files in {args.videos}")

    model = WhisperModel(args.model, device="cpu", compute_type=COMPUTE_TYPE)
    args.output.mkdir(parents=True, exist_ok=True)
    timings = []
    for path in paths:
        started = time.perf_counter()
        signals = extract(model, path, args)
        elapsed = round(time.perf_counter() - started, 1)
        (args.output / f"{path.stem}.json").write_text(signals.model_dump_json(indent=2))
        timings.append({"reel": path.name, "length_s": signals.length_s, "seconds_to_process": elapsed})
        print(f"{path.name}: {signals.length_s}s, {len(signals.cut_times_s)} cuts, processed in {elapsed}s")
    (args.output / "timings.json").write_text(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
