"""The LLM zero-shot baseline (rules.md 7.6): the label guideline as a prompt, no training.

Comments are sent in batches with numeric ids, never usernames. A comment the model skips is
returned as None, so the evaluation counts it as wrong instead of guessing a label for it.
"""

from collections.abc import Awaitable, Callable, Sequence

from pydantic import BaseModel

from ml.comments.labels import CommentLabel
from ml.common.llm_json import LlmAnswerError, parse_json_answer

PROMPT_VERSION = "comments-zero-shot-v1"
BATCH_SIZE = 25
MAX_OUTPUT_TOKENS = 1200

SYSTEM_PROMPT = """You label Instagram comments for a creator. Comments may be English, Urdu script,
or Roman Urdu mixed with English. Give each comment exactly one label. Go down this list and stop
at the first yes:
1. Ad, scam, bot text, follow-for-follow, gibberish, or a bare @tag with no words: "spam"
2. The commenter is unhappy with something: "complaint"
3. They say something in the video is wrong or untrue: "objection"
4. They ask for information: "question"
5. They ask the creator to do something: "request"
6. Otherwise, if positive: "praise"
Sarcasm counts as what it means. A question that wants no answer ("Ye kya bakwas hai?") is a complaint.
Return only JSON: {"labels": [{"id": <number>, "label": "<label>"}, ...]} with one entry per comment."""


class _Item(BaseModel):
    id: int
    label: CommentLabel


class _Answer(BaseModel):
    labels: list[_Item]


CallLlm = Callable[[str, str], Awaitable[str]]  # (system, user) -> raw text


def build_user_prompt(texts: Sequence[str]) -> str:
    lines = [f"{index}: {text.replace(chr(10), ' ').strip()}" for index, text in enumerate(texts)]
    return "Comments:\n" + "\n".join(lines)


def parse_labels(raw: str, count: int) -> list[CommentLabel | None]:
    answer = parse_json_answer(raw, _Answer)
    labels: list[CommentLabel | None] = [None] * count
    for item in answer.labels:
        if 0 <= item.id < count:
            labels[item.id] = item.label
    return labels


async def classify(texts: Sequence[str], call_llm: CallLlm) -> list[CommentLabel | None]:
    """One call per batch. A batch with an unreadable answer is left as missing, not guessed."""
    labels: list[CommentLabel | None] = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        try:
            labels += parse_labels(await call_llm(SYSTEM_PROMPT, build_user_prompt(batch)), len(batch))
        except LlmAnswerError:
            labels += [None] * len(batch)
    return labels
