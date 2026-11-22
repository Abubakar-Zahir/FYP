"""Urdu script to Roman Urdu for captions (roadmap Phase 2, item 3). Version 1, rule based.

Whisper writes Urdu speech in Urdu script, but creators caption in Roman Urdu. Common words get
their usual Roman spelling. Other words go letter by letter, which is readable but not always
how a creator would spell it. An Urdu speaker should review and extend COMMON_WORDS
(docs/manual-work.md), and caption quality is scored per language (SRS evaluation table).
"""

import re

COMMON_WORDS: dict[str, str] = {
    "یہ": "ye",
    "وہ": "woh",
    "ہے": "hai",
    "ہیں": "hain",
    "کیا": "kya",
    "کہاں": "kahan",
    "کیوں": "kyun",
    "کیسے": "kaise",
    "کون": "kaun",
    "نہیں": "nahi",
    "ہاں": "haan",
    "اور": "aur",
    "میں": "main",
    "آپ": "aap",
    "ہم": "hum",
    "تم": "tum",
    "کا": "ka",
    "کی": "ki",
    "کے": "ke",
    "کو": "ko",
    "سے": "se",
    "پر": "par",
    "بھی": "bhi",
    "تو": "to",
    "بہت": "bohot",
    "اچھا": "achha",
    "اچھی": "achhi",
    "سب": "sab",
    "یار": "yaar",
    "بھائی": "bhai",
    "زبردست": "zabardast",
    "شکریہ": "shukriya",
}

LETTERS: dict[str, str] = {
    "ا": "a", "آ": "aa", "ب": "b", "پ": "p", "ت": "t", "ٹ": "t", "ث": "s", "ج": "j", "چ": "ch",
    "ح": "h", "خ": "kh", "د": "d", "ڈ": "d", "ذ": "z", "ر": "r", "ڑ": "r", "ز": "z", "ژ": "zh",
    "س": "s", "ش": "sh", "ص": "s", "ض": "z", "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f",
    "ق": "q", "ک": "k", "گ": "g", "ل": "l", "م": "m", "ن": "n", "ں": "n", "و": "o", "ہ": "h",
    "ھ": "h", "ء": "", "ی": "i", "ے": "e", "ئ": "i", "ۓ": "e", "ة": "a", "ك": "k", "ي": "i",
    "۔": ".", "،": ",", "؟": "?",
}  # fmt: skip

# Letters only: Arabic letters, then the extra Urdu letters. Urdu punctuation is handled apart,
# so "ہے؟" is the word "ہے" followed by a question mark.
_URDU_WORD = re.compile(f"[{chr(0x0621)}-{chr(0x064A)}{chr(0x0670)}-{chr(0x06D3)}]+")
PUNCTUATION = {chr(0x060C): ",", chr(0x061F): "?", chr(0x06D4): "."}


def _word(word: str) -> str:
    if word in COMMON_WORDS:
        return COMMON_WORDS[word]
    return "".join(LETTERS.get(letter, "") for letter in word)


def to_roman_urdu(text: str) -> str:
    """Leaves English, numbers and emoji as they are."""
    roman = _URDU_WORD.sub(lambda match: _word(match.group(0)), text)
    return "".join(PUNCTUATION.get(character, character) for character in roman)
