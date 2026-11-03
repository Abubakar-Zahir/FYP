from collections.abc import Sequence

from ml.dna.schema import TranscriptSegment

PACING_WINDOW_S = 10.0
HOOK_WINDOW_S = 3.0


def cuts_per_window(
    cut_times_s: Sequence[float], length_s: float, window_s: float = PACING_WINDOW_S
) -> float:
    if length_s <= 0:
        raise ValueError("length_s must be positive")
    return round(len(cut_times_s) / length_s * window_s, 2)


def hook_candidate(segments: Sequence[TranscriptSegment], window_s: float = HOOK_WINDOW_S) -> str:
    """Speech that starts inside the opening window, which the structuring step reads as the hook."""
    return " ".join(segment.text.strip() for segment in segments if segment.start_s < window_s).strip()
