import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ml.edit.captions import CaptionStyle, build_ass, group_lines
from ml.edit.cuts import Segment, Word, keep_segments, remap, remap_words, removed_seconds
from ml.edit.pipeline import EditOptions, edit_video, plan
from ml.edit.render import build_command
from ml.edit.transliterate import to_roman_urdu

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
WORDS = [Word(0.2, 0.6, "Sab"), Word(0.7, 1.1, "se"), Word(1.2, 1.8, "crispy"), Word(4.2, 4.9, "chaat?")]


def test_long_pauses_are_cut_with_padding() -> None:
    segments = keep_segments(WORDS, length_s=6.0)

    assert segments == [Segment(0.05, 1.95), Segment(4.05, 5.05)]
    assert removed_seconds(segments, 6.0) == pytest.approx(3.1)


def test_no_speech_keeps_everything() -> None:
    assert keep_segments([], length_s=5.0) == [Segment(0.0, 5.0)]


def test_times_move_to_the_cut_timeline() -> None:
    segments = [Segment(0.0, 2.0), Segment(4.0, 5.0)]

    assert remap(1.0, segments) == 1.0
    assert remap(4.5, segments) == 2.5
    assert remap(3.0, segments) is None
    assert [word.start_s for word in remap_words(WORDS, keep_segments(WORDS, 6.0))] == [
        0.15,
        0.65,
        1.15,
        2.05,
    ]


def test_words_group_into_short_lines() -> None:
    lines = group_lines(WORDS)

    assert [[word.text for word in line.words] for line in lines] == [["Sab", "se", "crispy"], ["chaat?"]]


def test_ass_file_has_style_events_karaoke_and_hook() -> None:
    karaoke = build_ass(WORDS, CaptionStyle.KARAOKE, hook_text="Sab se crispy chaat?")
    bold = build_ass([Word(0, 1, "a{b}c\\N")], CaptionStyle.BOLD_POP)

    assert "PlayResY: 1920" in karaoke
    assert "Dialogue: 1,0:00:00.00,0:00:03.00,Hook,Sab se crispy chaat?" in karaoke
    assert "{\\k40}Sab {\\k40}se {\\k60}crispy" in karaoke
    assert "Caption,A(B)C/N" in bold  # braces and line breaks can't inject ASS tags


@pytest.mark.parametrize(
    ("urdu", "roman"),
    [
        ("یہ کہاں ہے؟", "ye kahan hai?"),
        ("بہت زبردست bhai 😍", "bohot zabardast bhai 😍"),
        ("Price 300", "Price 300"),
    ],
)
def test_transliteration(urdu: str, roman: str) -> None:
    assert to_roman_urdu(urdu) == roman


def test_command_has_cuts_captions_and_progress_bar(tmp_path: Path) -> None:
    command = build_command(
        "ffmpeg",
        tmp_path / "in.mp4",
        tmp_path / "out.mp4",
        [Segment(0, 2), Segment(4, 5)],
        tmp_path / "c.ass",
        True,
        3.0,
    )
    video = command[command.index("-vf") + 1]

    assert "between(t,0.000,2.000)+between(t,4.000,5.000)" in video
    assert "ass=" in video and "drawbox" in video and "iw*t/3.000" in video
    assert "aselect" in command[command.index("-af") + 1]
    assert command[-1].endswith("out.mp4")


def test_plan_without_cutting_keeps_the_timeline() -> None:
    segments, words = plan(WORDS, 6.0, cut_silences=False)

    assert segments == [Segment(0.0, 6.0)]
    assert words == WORDS


def _duration(path: Path) -> float:
    assert FFPROBE is not None
    out = subprocess.run(  # noqa: S603
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True,
        capture_output=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


@pytest.mark.skipif(FFMPEG is None or FFPROBE is None, reason="FFmpeg is needed for the render test")
def test_a_real_render_cuts_the_silence(tmp_path: Path) -> None:
    assert FFMPEG is not None
    source = tmp_path / "raw.mp4"
    # 6 s of vertical video. Tone for 2 s, silence for 2 s, tone for 2 s.
    subprocess.run(  # noqa: S603
        [
            FFMPEG, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=blue:s=360x640:r=25:d=6",
            "-f", "lavfi", "-i", "sine=f=440:d=2", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono:d=2",
            "-f", "lavfi", "-i", "sine=f=440:d=2",
            "-filter_complex", "[1:a][2:a][3:a]concat=n=3:v=0:a=1[a]",
            "-map", "0:v", "-map", "[a]", "-shortest", "-pix_fmt", "yuv420p", str(source),
        ],
        check=True,
    )  # fmt: skip
    words = [Word(0.1, 0.9, "Sab"), Word(1.0, 1.9, "se"), Word(4.1, 5.9, "crispy")]
    options = EditOptions(CaptionStyle.BOXED, cut_silences=True, progress_bar=True, hook_overlay=True)

    outcome = edit_video(FFMPEG, source, tmp_path / "out.mp4", words, 6.0, options, "Hook")

    assert outcome.removed_silence_s == pytest.approx(1.9, abs=0.05)
    assert _duration(tmp_path / "out.mp4") == pytest.approx(outcome.duration_s, abs=0.3)
