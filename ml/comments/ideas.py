"""Turns comment themes into a short name and a next-video idea each (SRS FR-7.5)."""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel

from ml.comments.labels import CommentLabel
from ml.common.llm_json import LlmAnswerError, parse_json_answer

PROMPT_VERSION = "comment-ideas-v1"
MAX_OUTPUT_TOKENS = 1200

SYSTEM_PROMPT = """You help an Instagram creator turn what their comments keep saying into reel ideas.
For each numbered theme you get its key words, its most common comment type, and example comments
(English, Urdu or Roman Urdu). Return only JSON:
{"themes": [{"id": <number>, "name": "<3 to 6 word name, in the comments' language>",
"idea": "<one sentence: a specific next reel that answers this theme>"}]}"""


@dataclass(frozen=True)
class ThemeInput:
    terms: list[str]
    dominant_label: CommentLabel
    examples: list[str]


@dataclass(frozen=True)
class ThemeIdea:
    name: str
    idea: str


class _Item(BaseModel):
    id: int
    name: str
    idea: str


class _Answer(BaseModel):
    themes: list[_Item]


CallLlm = Callable[[str, str], Awaitable[str]]


def fallback_idea(theme: ThemeInput) -> ThemeIdea:
    """Used without an LLM, or when its answer is unreadable. Plain, but never invented."""
    name = " / ".join(theme.terms[:3])
    example = theme.examples[0] if theme.examples else name
    if theme.dominant_label in (CommentLabel.QUESTION, CommentLabel.REQUEST):
        return ThemeIdea(name=name, idea=f'Make a reel that answers: "{example}"')
    return ThemeIdea(name=name, idea=f'Make a reel about "{name}", which many comments mention')


def build_user_prompt(niche: str, themes: Sequence[ThemeInput]) -> str:
    blocks = [
        f"{index}: words: {', '.join(theme.terms)}; mostly {theme.dominant_label.value}; examples: "
        + " | ".join(example.replace("\n", " ") for example in theme.examples)
        for index, theme in enumerate(themes)
    ]
    return f"Creator niche: {niche}\n\nThemes:\n" + "\n".join(blocks)


async def name_themes(niche: str, themes: Sequence[ThemeInput], call_llm: CallLlm | None) -> list[ThemeIdea]:
    ideas = [fallback_idea(theme) for theme in themes]
    if call_llm is None or not themes:
        return ideas
    try:
        answer = parse_json_answer(await call_llm(SYSTEM_PROMPT, build_user_prompt(niche, themes)), _Answer)
    except LlmAnswerError:
        return ideas
    for item in answer.themes:
        if 0 <= item.id < len(ideas) and item.name.strip() and item.idea.strip():
            ideas[item.id] = ThemeIdea(name=item.name.strip(), idea=item.idea.strip())
    return ideas
