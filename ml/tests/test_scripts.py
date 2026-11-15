import asyncio
import json
from typing import Any

import pytest

from ml.dna.schema import Beat, DnaRecord, HookType, ReelSignals, TranscriptSegment
from ml.scripts.generate import PROMPT_VERSION, ScriptGenerationError, ScriptPrompt, build_prompt, generate
from ml.scripts.schema import CreatorVoice, ScriptLanguage, ScriptRequest

TEMPLATE = DnaRecord(
    signals=ReelSignals(
        length_s=24.0,
        cut_times_s=[3.0, 9.0, 18.0],
        pacing_cuts_per_10s=1.25,
        detected_language="ur",
        transcript=[TranscriptSegment(start_s=0, end_s=3, text="Lahore ki sab se crispy chaat kahan hai?")],
        hook_candidate_text="Lahore ki sab se crispy chaat kahan hai?",
        keyframe_paths=[],
        model_version="faster-whisper-small+int8",
    ),
    hook_type=HookType.QUESTION,
    hook_text="Lahore ki sab se crispy chaat kahan hai?",
    beats=[
        Beat(label="Hook", start_s=0, end_s=3, description="Asks a question."),
        Beat(label="Reveal", start_s=3, end_s=18, description="Shows three places."),
        Beat(label="CTA", start_s=18, end_s=24, description="Asks to follow."),
    ],
    overlays=[],
    cta="Follow karo part 2 ke liye",
    model_version="m/dna-structure-v1",
)
REQUEST = ScriptRequest(
    topic="Best budget biryani in Karachi",
    language=ScriptLanguage.ROMAN_URDU,
    creator=CreatorVoice(
        niche="Food reviews",
        tone="Honest reviewer",
        goals="Grow to 20K followers",
        sample_captions=["Paisa vasool ya nahi? Batao comments mein"],
    ),
    templates=[TEMPLATE],
)
GOOD: dict[str, Any] = {
    "hooks": [{"text": f"Hook {n}"} for n in range(5)],
    "angles": [{"title": f"Angle {n}", "summary": "One line."} for n in range(3)],
    "body": [
        {"beat": "Hook", "line": "Karachi ki sab se sasti biryani?", "shot": "Close-up of the plate"},
        {"beat": "Reveal", "line": "Teen jagah try ki.", "shot": "Walking into each shop"},
        {"beat": "CTA", "line": "Part 2 ke liye follow karo.", "shot": "Talking to camera"},
    ],
}


class ScriptedLlm:
    def __init__(self, *answers: str) -> None:
        self._answers = list(answers)
        self.prompts: list[ScriptPrompt] = []

    async def __call__(self, prompt: ScriptPrompt) -> str:
        self.prompts.append(prompt)
        return self._answers.pop(0)


def test_prompt_carries_the_template_structure_voice_and_language() -> None:
    prompt = build_prompt(REQUEST)

    assert "Topic: Best budget biryani in Karachi" in prompt.user
    assert "hook type question" in prompt.user
    assert "Reveal (3-18 s): Shows three places." in prompt.user
    assert '"Follow karo part 2 ke liye"' in prompt.user
    assert "Paisa vasool ya nahi?" in prompt.user
    assert "Never use Urdu script" in prompt.user
    assert "Never copy the template's words" in prompt.system


def test_a_good_answer_becomes_a_draft() -> None:
    draft = asyncio.run(generate(REQUEST, ScriptedLlm(json.dumps(GOOD)), "openai_compatible:m"))

    assert len(draft.hooks) == 5
    assert len(draft.angles) == 3
    assert [beat.beat for beat in draft.body] == ["Hook", "Reveal", "CTA"]
    assert draft.model_version == f"openai_compatible:m/{PROMPT_VERSION}"


@pytest.mark.parametrize(
    "bad",
    [
        "not json",
        json.dumps({**GOOD, "hooks": GOOD["hooks"][:4]}),
        json.dumps({**GOOD, "angles": []}),
        json.dumps({**GOOD, "body": GOOD["body"][:2]}),
        json.dumps({**GOOD, "body": [{"beat": "Hook", "line": "  ", "shot": "x"}] * 3}),
    ],
    ids=["not-json", "four-hooks", "no-angles", "two-beats", "blank-line"],
)
def test_bad_answers_are_retried_once_with_the_problem(bad: str) -> None:
    llm = ScriptedLlm(bad, json.dumps(GOOD))

    draft = asyncio.run(generate(REQUEST, llm, "m"))

    assert len(draft.hooks) == 5
    assert "previous answer was rejected" in llm.prompts[1].user


def test_two_bad_answers_raise() -> None:
    with pytest.raises(ScriptGenerationError):
        asyncio.run(generate(REQUEST, ScriptedLlm("nope", "still nope"), "m"))


def test_requests_need_a_template() -> None:
    with pytest.raises(ValueError, match="templates"):
        ScriptRequest(topic="x y", language=ScriptLanguage.ENGLISH, creator=REQUEST.creator, templates=[])
