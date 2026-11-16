import asyncio
import json
from typing import Any

import pytest

from ml.dna.schema import HookType
from ml.variants.generate import (
    Candidate,
    OpenerType,
    VariantBrief,
    VariantGenerationError,
    distinct,
    generate_candidates,
)

BRIEF = VariantBrief(
    topic="Best chai in Lahore",
    niche="Food",
    tone="Honest",
    hooks=["Lahore ki sab se achhi chai?"],
    script_lines=["Teen jagah try ki."],
    language_rule="Mix Roman Urdu and English.",
)


def _candidate(n: int, **change: Any) -> dict[str, Any]:
    return {
        "hook_line": f"Hook {n}",
        "hook_style": "question",
        "opener": "Close-up of the cup",
        "opener_type": "product",
        "caption": f"Caption {n}",
        "hashtags": ["chai", "#lahore"],
        **change,
    }


def test_features_and_caption_with_hashtags() -> None:
    candidate = Candidate.model_validate(_candidate(1))
    long = Candidate.model_validate(_candidate(2, caption="x" * 200))

    assert candidate.features() == {"hook_style": "question", "opener": "product", "caption_length": "short"}
    assert long.features()["caption_length"] == "long"
    assert candidate.full_caption() == "Caption 1\n\n#chai #lahore"
    assert candidate.opener_type == OpenerType.PRODUCT and candidate.hook_style == HookType.QUESTION


def test_repeated_hooks_or_captions_are_dropped() -> None:
    items = [Candidate.model_validate(_candidate(n)) for n in range(3)]
    repeat_hook = Candidate.model_validate(_candidate(9, hook_line="hook 0"))
    repeat_caption = Candidate.model_validate(_candidate(8, caption="CAPTION 1"))

    assert distinct([*items, repeat_hook, repeat_caption]) == items


def test_generation_returns_enough_distinct_candidates() -> None:
    async def llm(system: str, user: str) -> str:
        assert "Write 6 candidates" in user
        return json.dumps({"candidates": [_candidate(n) for n in range(6)]})

    candidates = asyncio.run(generate_candidates(BRIEF, 3, llm))

    assert len(candidates) == 6


def test_a_bad_answer_is_retried_and_repeats_are_asked_again() -> None:
    answers = iter(
        [
            "not json",
            json.dumps({"candidates": [_candidate(1), _candidate(1), _candidate(1)]}),
            json.dumps({"candidates": [_candidate(n) for n in range(3)]}),
        ]
    )

    async def llm(system: str, user: str) -> str:
        return next(answers)

    with pytest.raises(VariantGenerationError):
        asyncio.run(generate_candidates(BRIEF, 3, llm))


def test_variant_count_is_bounded() -> None:
    async def llm(system: str, user: str) -> str:
        return ""

    with pytest.raises(ValueError):
        asyncio.run(generate_candidates(BRIEF, 6, llm))
