"""Builds and runs the FFmpeg command for one edit (SRS FR-5.2, FR-5.3, FR-5.5; NFR-2).

Cuts use the select and aselect filters, so the whole edit is one FFmpeg run with one encode.
Captions and the hook overlay are burned in from the ASS file. The progress bar is a drawbox
whose width grows with time. Output is H.264 and AAC, which Instagram accepts.
"""

import subprocess
from collections.abc import Sequence
from pathlib import Path

from ml.edit.cuts import Segment

PROGRESS_BAR_HEIGHT = 14
RENDER_TIMEOUT_S = 15 * 60
PRESET = "veryfast"  # NFR-2: a 60 s clip in under 5 minutes on CPU
CRF = "23"


def _between(segments: Sequence[Segment]) -> str:
    return "+".join(f"between(t,{segment.start_s:.3f},{segment.end_s:.3f})" for segment in segments)


def _ass_path(path: Path) -> str:
    """The subtitles filter needs ':' and '\\' escaped inside its argument (Windows paths)."""
    return path.as_posix().replace(":", "\\:").replace("'", "\\'")


def build_command(
    ffmpeg: str,
    source: Path,
    output: Path,
    segments: Sequence[Segment] | None,
    captions: Path | None,
    progress_bar: bool,
    output_length_s: float,
) -> list[str]:
    video: list[str] = []
    audio: list[str] = []
    if segments:
        keep = _between(segments)
        video += [f"select='{keep}'", "setpts=N/FRAME_RATE/TB"]
        audio += [f"aselect='{keep}'", "asetpts=N/SR/TB"]
    if captions is not None:
        video.append(f"ass='{_ass_path(captions)}'")
    if progress_bar and output_length_s > 0:
        video.append(
            f"drawbox=x=0:y=ih-{PROGRESS_BAR_HEIGHT}:w=iw*t/{output_length_s:.3f}:"
            f"h={PROGRESS_BAR_HEIGHT}:color=white@0.85:t=fill"
        )
    command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(source)]
    if video:
        command += ["-vf", ",".join(video)]
    if audio:
        command += ["-af", ",".join(audio)]
    return command + [
        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output),
    ]  # fmt: skip


class RenderFailed(RuntimeError):
    pass


def run(command: Sequence[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=RENDER_TIMEOUT_S)  # noqa: S603
    except subprocess.CalledProcessError as error:
        # FFmpeg's message names only our temp files, never user data.
        raise RenderFailed(error.stderr.decode(errors="replace")[-500:]) from error
    except subprocess.TimeoutExpired as error:
        raise RenderFailed("FFmpeg took longer than the time limit") from error
