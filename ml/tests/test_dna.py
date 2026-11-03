import pytest
from pydantic import ValidationError

from ml.dna.schema import Beat, HookType, TranscriptSegment
from ml.dna.signals import cuts_per_window, hook_candidate


def test_pacing_is_cuts_per_ten_seconds() -> None:
    assert cuts_per_window([1.0, 2.0, 3.0, 4.0], length_s=20.0) == 2.0


def test_pacing_rejects_zero_length() -> None:
    with pytest.raises(ValueError, match="positive"):
        cuts_per_window([], length_s=0)


def test_hook_candidate_uses_opening_window() -> None:
    segments = [
        TranscriptSegment(start_s=0.0, end_s=1.5, text=" Sab se crispy "),
        TranscriptSegment(start_s=1.5, end_s=2.9, text="chaat?"),
        TranscriptSegment(start_s=3.0, end_s=5.0, text="Chalo dekhte hain"),
    ]

    assert hook_candidate(segments) == "Sab se crispy chaat?"


def test_hook_types_match_srs() -> None:
    assert {item.value for item in HookType} == {
        "question",
        "bold_claim",
        "pattern_interrupt",
        "story",
        "list",
        "other",
    }


def test_beat_must_end_after_it_starts() -> None:
    with pytest.raises(ValidationError):
        Beat(label="Hook", start_s=3, end_s=3, description="x")
