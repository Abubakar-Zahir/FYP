import pytest

from ml.common.metrics import corpus_wer, edit_distance, normalise_words


def test_normalise_drops_punctuation_and_case() -> None:
    assert normalise_words("Ye KAHAN hai, bhai?") == ["ye", "kahan", "hai", "bhai"]


def test_normalise_keeps_urdu_script() -> None:
    assert normalise_words("یہ کہاں ہے؟") == ["یہ", "کہاں", "ہے"]


@pytest.mark.parametrize(
    ("reference", "hypothesis", "expected"),
    [
        (["a", "b"], ["a", "b"], 0),
        (["a", "b"], ["a", "x"], 1),
        (["a", "b"], ["a"], 1),
        (["a"], ["a", "b"], 1),
        (["a", "b"], [], 2),
    ],
)
def test_edit_distance(reference: list[str], hypothesis: list[str], expected: int) -> None:
    assert edit_distance(reference, hypothesis) == expected


def test_corpus_wer_weights_by_reference_words() -> None:
    result = corpus_wer([("one two three four", "one two three four"), ("five", "wrong")])

    assert result.errors == 1
    assert result.reference_words == 5
    assert result.wer == pytest.approx(0.2)


def test_wer_can_exceed_one_with_insertions() -> None:
    assert corpus_wer([("a", "x y z")]).wer == pytest.approx(3.0)


def test_empty_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        corpus_wer([("  ", "a")])


def test_no_clips_is_rejected() -> None:
    with pytest.raises(ValueError, match="No clips"):
        corpus_wer([])
