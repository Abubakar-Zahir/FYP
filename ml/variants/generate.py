"""Variant candidates for one video (SRS FR-6.1 and FR-6.3).

The LLM writes more candidates than will be published, each with a different hook line,
opening frame and caption with hashtags. The variant learner then picks which ones to test
(ml/bandit/thompson.py). Variants must differ in hook, opener and caption, not just be
re-uploads, because near-duplicates risk Instagram's unoriginal-content penalty (SRS risks).
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from ml.common.llm_json import LlmAnswerError, parse_json_answer
from ml.dna.schema import HookType

PROMPT_VERSION = "variants-v1"
MAX_OUTPUT_TOKENS = 2500
MIN_VARIANTS = 3
MAX_VARIANTS = 5
CANDIDATES_PER_VARIANT = 2
SHORT_CAPTION_CHARS = 120
MAX_HASHTAGS = 8
REPEATED_INSTRUCTION = "Your previous candidates repeated each other. Make each one different."


class OpenerType(StrEnum):
    FACE = "face"  # the creator talking to camera
    PRODUCT = "product"  # the thing the reel is about
    TEXT = "text"  # a bold text card


class Candidate(BaseModel):
    hook_line: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    hook_style: HookType
    opener: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    opener_type: OpenerType
    caption: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    hashtags: list[str] = Field(default_factory=list, max_length=MAX_HASHTAGS)

    def features(self) -> dict[str, str]:
        """What the variant learner sees (ml/bandit/simulator.py FEATURES)."""
        return {
            "hook_style": self.hook_style.value,
            "opener": self.opener_type.value,
            "caption_length": "short" if len(self.caption) <= SHORT_CAPTION_CHARS else "long",
        }

    def full_caption(self) -> str:
        tags = " ".join(f"#{tag.lstrip('#')}" for tag in self.hashtags if tag.strip("# "))
        return f"{self.caption}\n\n{tags}".strip()


class _Answer(BaseModel):
    candidates: list[Candidate] = Field(min_length=MIN_VARIANTS)


@dataclass(frozen=True)
class VariantBrief:
    topic: str
    niche: str
    tone: str
    hooks: list[str]
    script_lines: list[str]
    language_rule: str


CallLlm = Callable[[str, str], Awaitable[str]]

SYSTEM_PROMPT = """You write Instagram Trial Reel variants of one finished video for a creator.
Each variant must be clearly different from the others in all three of: the hook line shown on screen
in the first 3 seconds, the opening frame, and the caption. Never just reword the same idea.
Return only JSON: {"candidates": [{"hook_line": "...",
"hook_style": "question|bold_claim|pattern_interrupt|story|list|other",
"opener": "<what the first frame shows>", "opener_type": "face|product|text", "caption": "...",
"hashtags": ["...", ...]}]}. Use at most 8 hashtags, without the # sign."""


def build_user_prompt(brief: VariantBrief, count: int) -> str:
    return (
        f"Write {count} candidates.\n"
        f"Niche: {brief.niche}\nTone: {brief.tone}\nLanguage: {brief.language_rule}\n"
        f"Topic: {brief.topic}\n"
        "Hooks already written for this script:\n" + "\n".join(f"- {hook}" for hook in brief.hooks) + "\n"
        "Script:\n" + "\n".join(brief.script_lines)
    )


class VariantGenerationError(Exception):
    pass


def distinct(candidates: Sequence[Candidate]) -> list[Candidate]:
    """Drops candidates whose hook line or caption repeats an earlier one."""
    seen_hooks: set[str] = set()
    seen_captions: set[str] = set()
    kept = []
    for candidate in candidates:
        hook, caption = candidate.hook_line.casefold(), candidate.caption.casefold()
        if hook in seen_hooks or caption in seen_captions:
            continue
        seen_hooks.add(hook)
        seen_captions.add(caption)
        kept.append(candidate)
    return kept


async def generate_candidates(brief: VariantBrief, variant_count: int, call_llm: CallLlm) -> list[Candidate]:
    if not MIN_VARIANTS <= variant_count <= MAX_VARIANTS:
        raise ValueError(f"Variant count must be {MIN_VARIANTS} to {MAX_VARIANTS}")
    wanted = variant_count * CANDIDATES_PER_VARIANT
    prompt = build_user_prompt(brief, wanted)
    for attempt in range(2):
        try:
            candidates = distinct(
                parse_json_answer(await call_llm(SYSTEM_PROMPT, prompt), _Answer).candidates
            )
        except LlmAnswerError as error:
            prompt = f"{build_user_prompt(brief, wanted)}\n\nYour previous answer was rejected: {error}"
            if attempt:
                raise VariantGenerationError(str(error)) from error
            continue
        if len(candidates) >= variant_count:
            return candidates
        prompt = f"{build_user_prompt(brief, wanted)}\n\n{REPEATED_INSTRUCTION}"
    raise VariantGenerationError("Not enough distinct candidates")
