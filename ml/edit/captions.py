"""Word-level captions as an ASS subtitle file (SRS FR-5.2), burned in by FFmpeg's libass.

Words are grouped into short lines that are easy to read on a phone. Each style matches one
the editor offers. Karaoke highlights each word as it is spoken. The hook overlay (FR-5.5) is
an extra line at the top for the first seconds.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from ml.edit.cuts import Word

PLAY_WIDTH = 1080
PLAY_HEIGHT = 1920
MAX_WORDS_PER_LINE = 3
MAX_LINE_S = 1.6
HOOK_OVERLAY_S = 3.0
CENTISECONDS = 100


class CaptionStyle(StrEnum):
    BOLD_POP = "bold_pop"
    KARAOKE = "karaoke"
    MINIMAL = "minimal"
    BOXED = "boxed"


@dataclass(frozen=True)
class CaptionLine:
    start_s: float
    end_s: float
    words: list[Word]


# Font, size, primary and secondary colour (&HAABBGGRR), outline colour, back colour, bold,
# border style (1 outline, 3 box), outline, shadow, alignment (2 bottom centre), vertical margin.
_STYLES: dict[CaptionStyle, str] = {
    CaptionStyle.BOLD_POP: "Arial,96,&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,-1,1,6,2,2,520",
    CaptionStyle.KARAOKE: "Arial,84,&H0000E5FF,&H00FFFFFF,&H00000000,&H64000000,-1,1,5,1,2,520",
    CaptionStyle.MINIMAL: "Arial,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,1,2,1,2,420",
    CaptionStyle.BOXED: "Arial,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,-1,3,14,0,2,420",
}
_HOOK_STYLE = "Arial,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,-1,3,18,0,8,180"


def group_lines(words: Sequence[Word]) -> list[CaptionLine]:
    lines: list[CaptionLine] = []
    current: list[Word] = []
    for word in words:
        too_long = current and (word.end_s - current[0].start_s > MAX_LINE_S)
        if current and (len(current) >= MAX_WORDS_PER_LINE or too_long):
            lines.append(CaptionLine(current[0].start_s, current[-1].end_s, current))
            current = []
        current.append(word)
    if current:
        lines.append(CaptionLine(current[0].start_s, current[-1].end_s, current))
    return lines


def _time(seconds: float) -> str:
    total = max(0, round(seconds * CENTISECONDS))
    hours, rest = divmod(total, 3600 * CENTISECONDS)
    minutes, rest = divmod(rest, 60 * CENTISECONDS)
    secs, centis = divmod(rest, CENTISECONDS)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _escape(text: str) -> str:
    """ASS treats braces as override tags and a backslash-N as a line break."""
    return text.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def _line_text(line: CaptionLine, style: CaptionStyle) -> str:
    words = [_escape(word.text) for word in line.words]
    if style == CaptionStyle.BOLD_POP:
        return " ".join(words).upper()
    if style == CaptionStyle.KARAOKE:
        parts = []
        for word, text in zip(line.words, words, strict=True):
            centis = max(1, round((word.end_s - word.start_s) * CENTISECONDS))
            parts.append(f"{{\\k{centis}}}{text}")
        return " ".join(parts)
    return " ".join(words)


def build_ass(words: Sequence[Word], style: CaptionStyle, hook_text: str | None = None) -> str:
    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {PLAY_WIDTH}",
        f"PlayResY: {PLAY_HEIGHT}",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
        "BorderStyle, Outline, Shadow, Alignment, MarginV",
        f"Style: Caption,{_STYLES[style]}",
        f"Style: Hook,{_HOOK_STYLE}",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Text",
    ]
    events = [
        f"Dialogue: 0,{_time(line.start_s)},{_time(line.end_s)},Caption,{_line_text(line, style)}"
        for line in group_lines(words)
    ]
    if hook_text and hook_text.strip():
        events.insert(0, f"Dialogue: 1,{_time(0)},{_time(HOOK_OVERLAY_S)},Hook,{_escape(hook_text)}")
    return "\n".join(header + events) + "\n"
