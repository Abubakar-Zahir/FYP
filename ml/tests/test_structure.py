import asyncio
import json
from typing import Any

import pytest

from ml.dna.schema import HookType, Overlay, ReelSignals, TranscriptSegment
from ml.dna.structure import PROMPT_VERSION, StructuringError, StructuringPrompt, build_prompt, structure

SIGNALS = ReelSignals(
    length_s=12.0,
    cut_times_s=[3.2, 7.5],
    pacing_cuts_per_10s=1.67,
    detected_language="ur",
    transcript=[
        TranscriptSegment(start_s=0.0, end_s=2.8, text=" Lahore ki sab se crispy chaat kahan hai?"),
        TranscriptSegment(start_s=3.0, end_s=10.0, text="Main ne 10 jagah try ki."),
        TranscriptSegment(start_s=10.0, end_s=12.0, text="Follow karo part 2 ke liye"),
    ],
    hook_candidate_text="Lahore ki sab se crispy chaat kahan hai?",
    keyframe_paths=[],
    model_version="faster-whisper-small+int8",
)

GOOD_ANSWER: dict[str, Any] = {
    "hook_type": "question",
    "hook_text": "Lahore ki sab se crispy chaat kahan hai?",
    "beats": [
        {"label": "Hook", "start_s": 0.0, "end_s": 3.0, "description": "Asks where the best chaat is."},
        {"label": "Payoff", "start_s": 3.0, "end_s": 10.0, "description": "Reviews the places tried."},
        {"label": "CTA", "start_s": 10.0, "end_s": 12.0, "description": "Asks viewers to follow."},
    ],
    "cta": "Follow karo part 2 ke liye",
}


class ScriptedLlm:
    """Returns the given answers in order and remembers every prompt it saw."""

    def __init__(self, *answers: str) -> None:
        self._answers = list(answers)
        self.prompts: list[StructuringPrompt] = []

    async def __call__(self, prompt: StructuringPrompt) -> str:
        self.prompts.append(prompt)
        return self._answers.pop(0)


def _with(**changes: Any) -> str:
    return json.dumps({**GOOD_ANSWER, **changes})


def test_prompt_has_timed_transcript_cuts_and_every_hook_type() -> None:
    prompt = build_prompt(SIGNALS)

    assert "[0.0-2.8] Lahore ki sab se crispy chaat kahan hai?" in prompt.user
    assert "Cuts at (s): 3.2, 7.5" in prompt.user
    assert "Reel length: 12.0 s" in prompt.user
    for hook_type in HookType:
        assert f'"{hook_type.value}"' in prompt.system


def test_prompt_handles_a_silent_reel() -> None:
    silent = SIGNALS.model_copy(update={"transcript": [], "hook_candidate_text": "", "cut_times_s": []})

    prompt = build_prompt(silent)

    assert "(no speech)" in prompt.user
    assert "Cuts at (s): none" in prompt.user


def test_good_answer_becomes_a_record() -> None:
    llm = ScriptedLlm(_with())
    overlays = [Overlay(at_s=0.5, text="Rs 300 only")]

    record = asyncio.run(structure(SIGNALS, llm, "openai_compatible:m", overlays))

    assert record.hook_type == HookType.QUESTION
    assert [beat.label for beat in record.beats] == ["Hook", "Payoff", "CTA"]
    assert record.cta == "Follow karo part 2 ke liye"
    assert record.overlays == overlays
    assert record.signals == SIGNALS
    assert record.model_version == f"openai_compatible:m/{PROMPT_VERSION}"
    assert len(llm.prompts) == 1


def test_code_fences_around_the_json_are_accepted() -> None:
    record = asyncio.run(structure(SIGNALS, ScriptedLlm(f"```json\n{_with()}\n```"), "m"))

    assert record.hook_type == HookType.QUESTION


@pytest.mark.parametrize(
    ("bad_answer", "problem"),
    [
        ("Sure! Here is the analysis.", "not valid JSON"),
        (_with(hook_type="clickbait"), "hook_type"),
        (_with(beats=[]), "beats"),
        (
            _with(beats=[{"label": "Hook", "start_s": 3.0, "end_s": 2.0, "description": "x"}]),
            "end after it starts",
        ),
        (
            _with(
                beats=[
                    {"label": "Hook", "start_s": 0.0, "end_s": 5.0, "description": "x"},
                    {"label": "Body", "start_s": 4.0, "end_s": 8.0, "description": "x"},
                ]
            ),
            "overlap",
        ),
        (_with(beats=[{"label": "Hook", "start_s": 0.0, "end_s": 30.0, "description": "x"}]), "length"),
    ],
    ids=["not-json", "unknown-hook-type", "no-beats", "beat-backwards", "beats-overlap", "beat-too-long"],
)
def test_a_bad_answer_is_retried_with_the_problem(bad_answer: str, problem: str) -> None:
    llm = ScriptedLlm(bad_answer, _with())

    record = asyncio.run(structure(SIGNALS, llm, "m"))

    assert record.hook_type == HookType.QUESTION
    assert len(llm.prompts) == 2
    assert problem in llm.prompts[1].user
    assert llm.prompts[1].system == llm.prompts[0].system


def test_two_bad_answers_give_up_instead_of_saving_a_partial_record() -> None:
    with pytest.raises(StructuringError):
        asyncio.run(structure(SIGNALS, ScriptedLlm("nope", "still nope"), "m"))
