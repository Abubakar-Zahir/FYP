"""Roman Urdu normalisation (prd.md Member C deliverable 3).

Roman Urdu has no standard spelling, so "kya", "kia" and "kyaa" are the same word. Mapping
common variants to one form lets a model see them as one feature. Urdu script and English
pass through unchanged except for case and noise.
"""

import re

# Variant -> canonical form. Variants that are also English words ("he", "me") are left out on purpose.
# An Urdu speaker on the team should review and extend this list (docs/manual-work.md).
VARIANTS: dict[str, str] = {
    "kia": "kya",
    "kyaa": "kya",
    "kiya": "kya",
    "h": "hai",
    "hy": "hai",
    "hay": "hai",
    "hae": "hai",
    "nai": "nahi",
    "nahin": "nahi",
    "nhi": "nahi",
    "ni": "nahi",
    "bohat": "bohot",
    "bht": "bohot",
    "boht": "bohot",
    "bahut": "bohot",
    "acha": "achha",
    "acchi": "achhi",
    "achi": "achhi",
    "kahaan": "kahan",
    "kidhar": "kahan",
    "yeh": "ye",
    "yh": "ye",
    "wo": "woh",
    "vo": "woh",
    "mein": "main",
    "mai": "main",
    "kr": "kar",
    "kro": "karo",
    "krna": "karna",
    "plz": "please",
    "pls": "please",
    "plzz": "please",
    "bhae": "bhai",
    "yr": "yaar",
    "yar": "yaar",
    "zbrdst": "zabardast",
    "zabardst": "zabardast",
    "shukria": "shukriya",
    "thx": "thanks",
}

_URL = re.compile(r"https?://\S+|www\.\S+")
_MENTION = re.compile(r"@\w+")
# Three or more of the same character become two: "sooooo" -> "soo", "!!!!" -> "!!".
_REPEAT = re.compile(r"(.)\1{2,}")
_TOKEN = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)
# Plain words, so the tokenizer keeps each placeholder in one piece.
URL_PLACEHOLDER = "urltag"
MENTION_PLACEHOLDER = "usertag"


def normalise(text: str) -> str:
    text = _URL.sub(f" {URL_PLACEHOLDER} ", text.casefold())
    text = _MENTION.sub(f" {MENTION_PLACEHOLDER} ", text)
    text = _REPEAT.sub(r"\1\1", text)
    tokens = [VARIANTS.get(token, token) for token in _TOKEN.findall(text)]
    return " ".join(tokens)
