"""Hook features (prd.md Member D deliverable 5): readable signals plus a small wording vector.

Every readable feature has a label a creator understands, so the top factors behind a score
can be shown as-is (NFR-10). The wording vector is hashed character n-grams: no download, no
GPU, and it copes with Roman Urdu spelling. Its parts are reported together as one factor.
"""

import re
from collections.abc import Sequence

import numpy
from sklearn.feature_extraction.text import HashingVectorizer

from ml.comments.normalise import VARIANTS, normalise
from ml.dna.schema import HookType

WORDING_SIZE = 64
WORDING_PREFIX = "wording_"
WORDING_LABEL = "Wording pattern"

_WORD = re.compile(r"\w+", flags=re.UNICODE)
_NUMBER = re.compile(r"\d")
_PRICE = re.compile(r"\b(rs|pkr|rupees?|rupay|price|\d+\s?k)\b|₨|\$", flags=re.IGNORECASE)
_EMOJI = re.compile(f"[{chr(0x1F300)}-{chr(0x1FAFF)}{chr(0x2600)}-{chr(0x27BF)}]")
_URDU_SCRIPT = re.compile(f"[{chr(0x0600)}-{chr(0x06FF)}]")  # the Arabic block, which Urdu uses
QUESTION_WORDS = {
    "kya",
    "kahan",
    "kaun",
    "kyun",
    "kab",
    "kaise",
    "kitna",
    "kitne",
    "what",
    "why",
    "how",
    "where",
    "who",
    "which",
}
SECOND_PERSON = {"you", "your", "aap", "ap", "tum", "tu", "apko", "aapko"}
ROMAN_URDU_WORDS = (
    set(VARIANTS) | set(VARIANTS.values()) | {"ye", "hai", "ka", "ki", "ke", "ko", "se", "aur", "bhi", "sab"}
)

READABLE: dict[str, str] = {
    "word_count": "Hook length in words",
    "has_question": "Asks a question",
    "starts_with_question_word": "Opens with a question word",
    "has_number": "Uses a number",
    "has_price": "Mentions a price",
    "speaks_to_viewer": "Talks to the viewer directly",
    "exclamation": "Uses an exclamation",
    "emoji_count": "Emoji",
    "roman_urdu_share": "Roman Urdu share",
    "urdu_script": "Written in Urdu script",
    **{f"hook_type_{item.value}": f"{item.value.replace('_', ' ').capitalize()} hook" for item in HookType},
}
READABLE_NAMES = list(READABLE)

_hasher = HashingVectorizer(
    analyzer="char_wb", ngram_range=(2, 4), n_features=WORDING_SIZE, alternate_sign=False, norm="l2"
)


def readable_features(text: str, hook_type: HookType | None) -> list[float]:
    words = [word.casefold() for word in _WORD.findall(text)]
    values = {
        "word_count": float(len(words)),
        "has_question": float("?" in text or "؟" in text),
        "starts_with_question_word": float(bool(words) and words[0] in QUESTION_WORDS),
        "has_number": float(bool(_NUMBER.search(text))),
        "has_price": float(bool(_PRICE.search(text))),
        "speaks_to_viewer": float(any(word in SECOND_PERSON for word in words)),
        "exclamation": float("!" in text),
        "emoji_count": float(len(_EMOJI.findall(text))),
        "roman_urdu_share": sum(word in ROMAN_URDU_WORDS for word in words) / len(words) if words else 0.0,
        "urdu_script": float(bool(_URDU_SCRIPT.search(text))),
    }
    for item in HookType:
        values[f"hook_type_{item.value}"] = float(hook_type == item)
    return [values[name] for name in READABLE_NAMES]


def feature_names(with_wording: bool) -> list[str]:
    return READABLE_NAMES + (
        [f"{WORDING_PREFIX}{index}" for index in range(WORDING_SIZE)] if with_wording else []
    )


def feature_matrix(
    texts: Sequence[str], hook_types: Sequence[HookType | None], with_wording: bool
) -> numpy.ndarray:
    readable = numpy.array(
        [readable_features(text, kind) for text, kind in zip(texts, hook_types, strict=True)]
    )
    if not with_wording:
        return readable
    wording = _hasher.transform([normalise(text) for text in texts]).toarray()
    return numpy.hstack([readable, wording])


def label_for(name: str) -> str:
    return WORDING_LABEL if name.startswith(WORDING_PREFIX) else READABLE.get(name, name)
