"""One auto-edit, end to end: words in, a finished vertical video out (roadmap Phase 2, item 3)."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ml.edit.captions import CaptionStyle, build_ass
from ml.edit.cuts import Segment, Word, keep_segments, remap_words, removed_seconds
from ml.edit.render import build_command, run
from ml.edit.transliterate import to_roman_urdu

CAPTIONS_FILE = "captions.ass"


@dataclass(frozen=True)
class EditOptions:
    caption_style: CaptionStyle
    cut_silences: bool
    progress_bar: bool
    hook_overlay: bool
    roman_urdu_captions: bool = True


@dataclass(frozen=True)
class EditOutcome:
    duration_s: float
    removed_silence_s: float
    segments: list[Segment]


def plan(words: Sequence[Word], length_s: float, cut_silences: bool) -> tuple[list[Segment], list[Word]]:
    if not cut_silences:
        return [Segment(0.0, length_s)], list(words)
    segments = keep_segments(words, length_s)
    return segments, remap_words(words, segments)


def edit_video(
    ffmpeg: str,
    source: Path,
    output: Path,
    words: Sequence[Word],
    length_s: float,
    options: EditOptions,
    hook_text: str | None,
) -> EditOutcome:
    segments, timed_words = plan(words, length_s, options.cut_silences)
    if options.roman_urdu_captions:
        timed_words = [Word(w.start_s, w.end_s, to_roman_urdu(w.text)) for w in timed_words]
    captions = output.parent / CAPTIONS_FILE
    overlay = hook_text if options.hook_overlay else None
    captions.write_text(build_ass(timed_words, options.caption_style, overlay), encoding="utf-8")
    duration = round(sum(segment.length_s for segment in segments), 3)
    command = build_command(
        ffmpeg,
        source,
        output,
        segments if options.cut_silences else None,
        captions,
        options.progress_bar,
        duration,
    )
    run(command)
    return EditOutcome(
        duration_s=duration, removed_silence_s=removed_seconds(segments, length_s), segments=segments
    )
