"""Silence cutting from Whisper word timings (SRS FR-5.3).

Speech is wherever words are. Gaps between words longer than MIN_SILENCE_S are cut, keeping a
little padding so words don't start abruptly. Working from word timings, not loudness, means
background music doesn't stop a pause from being cut.
"""

from collections.abc import Sequence
from dataclasses import dataclass

MIN_SILENCE_S = 0.6
PAD_S = 0.15


@dataclass(frozen=True)
class Word:
    start_s: float
    end_s: float
    text: str


@dataclass(frozen=True)
class Segment:
    start_s: float
    end_s: float

    @property
    def length_s(self) -> float:
        return self.end_s - self.start_s


def keep_segments(
    words: Sequence[Word], length_s: float, min_silence_s: float = MIN_SILENCE_S, pad_s: float = PAD_S
) -> list[Segment]:
    """The parts of the video to keep. With no speech, the whole video is kept."""
    if not words:
        return [Segment(0.0, length_s)]
    segments: list[Segment] = []
    start = max(0.0, words[0].start_s - pad_s)
    end = words[0].end_s
    for word in words[1:]:
        if word.start_s - end > min_silence_s:
            segments.append(Segment(start, min(length_s, end + pad_s)))
            start = max(0.0, word.start_s - pad_s)
        end = max(end, word.end_s)
    segments.append(Segment(start, min(length_s, end + pad_s)))
    return [Segment(round(s.start_s, 3), round(s.end_s, 3)) for s in _merge_touching(segments)]


def _merge_touching(segments: list[Segment]) -> list[Segment]:
    merged = [segments[0]]
    for segment in segments[1:]:
        if segment.start_s <= merged[-1].end_s:
            merged[-1] = Segment(merged[-1].start_s, max(merged[-1].end_s, segment.end_s))
        else:
            merged.append(segment)
    return merged


def removed_seconds(segments: Sequence[Segment], length_s: float) -> float:
    return round(max(0.0, length_s - sum(segment.length_s for segment in segments)), 2)


def remap(time_s: float, segments: Sequence[Segment]) -> float | None:
    """Where a moment of the original lands in the cut video. None if it was cut out."""
    offset = 0.0
    for segment in segments:
        if segment.start_s <= time_s <= segment.end_s:
            return round(offset + time_s - segment.start_s, 3)
        offset += segment.length_s
    return None


def remap_words(words: Sequence[Word], segments: Sequence[Segment]) -> list[Word]:
    moved = []
    for word in words:
        start, end = remap(word.start_s, segments), remap(word.end_s, segments)
        if start is not None and end is not None and end > start:
            moved.append(Word(start, end, word.text))
    return moved
