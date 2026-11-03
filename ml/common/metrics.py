import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

# \w covers Urdu script as well as Latin, so only punctuation is dropped.
_NON_WORD = re.compile(r"[^\w\s]", flags=re.UNICODE)


def normalise_words(text: str) -> list[str]:
    return _NON_WORD.sub(" ", text.casefold()).split()


def edit_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for row, reference_word in enumerate(reference, start=1):
        current = [row]
        for column, hypothesis_word in enumerate(hypothesis, start=1):
            substitution = previous[column - 1] + (reference_word != hypothesis_word)
            current.append(min(previous[column] + 1, current[column - 1] + 1, substitution))
        previous = current
    return previous[-1]


@dataclass(frozen=True)
class WerResult:
    errors: int
    reference_words: int

    @property
    def wer(self) -> float:
        return self.errors / self.reference_words


def corpus_wer(pairs: Iterable[tuple[str, str]]) -> WerResult:
    """Total errors over total reference words, so long clips are not outweighed by short ones."""
    errors = 0
    reference_words = 0
    for reference, hypothesis in pairs:
        reference_tokens = normalise_words(reference)
        if not reference_tokens:
            raise ValueError("Every clip needs a non-empty reference transcript")
        errors += edit_distance(reference_tokens, normalise_words(hypothesis))
        reference_words += len(reference_tokens)
    if reference_words == 0:
        raise ValueError("No clips to score")
    return WerResult(errors=errors, reference_words=reference_words)
