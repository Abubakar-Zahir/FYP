"""Machine signals from one reel video: transcript, cuts, pacing, hook speech and keyframes.

Needs the optional `video` dependency group (`uv sync --group video`). The Whisper model is
loaded once per Extractor, so a worker keeps one Extractor for its whole life.
"""

from dataclasses import dataclass
from pathlib import Path

import cv2
from faster_whisper import WhisperModel
from scenedetect import ContentDetector, detect

from ml.dna.errors import UnreadableVideo, VideoTooLong
from ml.dna.schema import ReelSignals, TranscriptSegment
from ml.dna.signals import cuts_per_window, hook_candidate
from ml.edit.cuts import Word

# PySceneDetect's default. It averages hue, saturation and brightness change, so a cut
# between scenes of similar brightness can score under this and be missed.
DEFAULT_CUT_THRESHOLD = 27.0
DEFAULT_WHISPER_MODEL = "small"
COMPUTE_TYPE = "int8"
# rules.md 6.3 and docs/backend.md: reels are at most 90 seconds.
MAX_REEL_LENGTH_S = 90.0
KEYFRAME_NAME = "scene_{index:03d}.jpg"

__all__ = ["Extractor", "ExtractOptions", "UnreadableVideo", "VideoTooLong"]


@dataclass(frozen=True)
class ExtractOptions:
    whisper_model: str = DEFAULT_WHISPER_MODEL
    language: str | None = None
    cut_threshold: float = DEFAULT_CUT_THRESHOLD
    max_length_s: float = MAX_REEL_LENGTH_S


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
    if fps <= 0 or frames <= 0:
        raise UnreadableVideo("The file is not a readable video")
    return float(frames / fps)


def detect_scenes(path: Path, length_s: float, threshold: float) -> Scenes:
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
                frame_path = output_dir / KEYFRAME_NAME.format(index=index)
                cv2.imwrite(str(frame_path), frame)
                saved.append(str(frame_path))
    finally:
        capture.release()
    return saved


class Extractor:
    def __init__(self, options: ExtractOptions) -> None:
        self.options = options
        self._model = WhisperModel(options.whisper_model, device="cpu", compute_type=COMPUTE_TYPE)

    @property
    def model_version(self) -> str:
        return f"faster-whisper-{self.options.whisper_model}+{COMPUTE_TYPE}"

    def transcribe(self, path: Path) -> tuple[list[TranscriptSegment], str | None]:
        segments, info = self._model.transcribe(
            str(path), language=self.options.language, word_timestamps=True
        )
        transcript = [
            TranscriptSegment(start_s=item.start, end_s=item.end, text=item.text) for item in segments
        ]
        return transcript, info.language

    def words(self, path: Path) -> tuple[list[Word], float]:
        """Word timings for auto-edit, and the video length. Rejects reels over the limit."""
        length_s = video_length_s(path)
        if length_s > self.options.max_length_s:
            raise VideoTooLong(
                f"The video is {length_s:.0f} s, over the {self.options.max_length_s:.0f} s limit"
            )
        segments, _ = self._model.transcribe(str(path), language=self.options.language, word_timestamps=True)
        words = [
            Word(start_s=float(word.start), end_s=float(word.end), text=word.word.strip())
            for segment in segments
            for word in (segment.words or [])
            if word.word.strip()
        ]
        return words, length_s

    def extract(self, path: Path, keyframe_dir: Path) -> ReelSignals:
        length_s = video_length_s(path)
        if length_s > self.options.max_length_s:
            raise VideoTooLong(
                f"The reel is {length_s:.0f} s, over the {self.options.max_length_s:.0f} s limit"
            )
        scenes = detect_scenes(path, length_s, self.options.cut_threshold)
        transcript, detected_language = self.transcribe(path)
        return ReelSignals(
            length_s=round(length_s, 3),
            cut_times_s=scenes.cut_times_s,
            pacing_cuts_per_10s=cuts_per_window(scenes.cut_times_s, length_s),
            detected_language=detected_language,
            transcript=transcript,
            hook_candidate_text=hook_candidate(transcript),
            keyframe_paths=save_keyframes(path, scenes.midpoints_s, keyframe_dir),
            model_version=self.model_version,
        )
