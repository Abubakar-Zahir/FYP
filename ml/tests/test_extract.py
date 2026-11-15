"""Runs only with the `video` group and FFmpeg installed: `uv run --group video pytest ml`."""

import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("faster_whisper")
pytest.importorskip("scenedetect")

from ml.dna.extract import (  # noqa: E402  (after the skips, so a missing group skips instead of failing)
    MAX_REEL_LENGTH_S,
    UnreadableVideo,
    detect_scenes,
    save_keyframes,
    video_length_s,
)

FFMPEG = shutil.which("ffmpeg")
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="FFmpeg is needed to make the test clip")


def _make_clip(path: Path) -> Path:
    """Three 2-second scenes in clearly different colours, so the cuts are unambiguous."""
    assert FFMPEG is not None
    inputs: list[str] = []
    for colour in ("red", "green", "blue"):
        inputs += ["-f", "lavfi", "-i", f"color=c={colour}:s=160x284:r=25:d=2"]
    command = [
        FFMPEG,
        "-y",
        "-loglevel",
        "error",
        *inputs,
        "-filter_complex",
        "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
        "-map",
        "[v]",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    subprocess.run(command, check=True)  # noqa: S603 (fixed arguments, test only)
    return path


@needs_ffmpeg
def test_length_cuts_and_keyframes_on_a_synthetic_clip(tmp_path: Path) -> None:
    clip = _make_clip(tmp_path / "clip.mp4")

    length = video_length_s(clip)
    scenes = detect_scenes(clip, length, threshold=27.0)
    keyframes = save_keyframes(clip, scenes.midpoints_s, tmp_path / "frames")

    assert length == pytest.approx(6.0, abs=0.1)
    assert scenes.cut_times_s == pytest.approx([2.0, 4.0], abs=0.1)
    assert len(keyframes) == 3
    assert all(Path(frame).exists() for frame in keyframes)


def test_a_file_that_is_not_a_video_is_rejected(tmp_path: Path) -> None:
    fake = tmp_path / "notes.mp4"
    fake.write_text("not a video")

    with pytest.raises(UnreadableVideo):
        video_length_s(fake)


def test_reel_limit_matches_the_upload_rule() -> None:
    assert MAX_REEL_LENGTH_S == 90.0
