"""LLM structuring: turns machine signals into a DnaRecord (SRS FR-2.2 to FR-2.4).

The LLM call is passed in, so this module never knows the provider and stays free of
framework imports (rules.md 3.9). On a bad answer it retries once, telling the model what
was wrong, then gives up rather than storing a half-filled record.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, Field

from ml.common.llm_json import LlmAnswerError, parse_json_answer
from ml.dna.schema import Beat, DnaRecord, HookType, Overlay, ReelSignals

PROMPT_VERSION = "dna-structure-v1"
MAX_OUTPUT_TOKENS = 1500
RETRY_INSTRUCTION = "Return a corrected JSON object only."
# Beats may end a little after the measured length, because Whisper timings are approximate.
BEAT_END_TOLERANCE_S = 0.5

HOOK_DEFINITIONS: dict[HookType, str] = {
    HookType.QUESTION: (
        "Opens by asking the viewer something. Example: 'Lahore ki sab se crispy chaat kahan milti hai?'"
    ),
    HookType.BOLD_CLAIM: (
        "Opens with a strong statement, number or promise. "
        "Example: 'This 300 rupee biryani beats every 5-star hotel.'"
    ),
    HookType.PATTERN_INTERRUPT: (
        "Opens with something surprising to look at or hear before any explanation: a sudden action, sound, "
        "odd object or unexpected line. Example: dropping a phone into a pot, then 'Ruko, samjhata hoon.'"
    ),
    HookType.STORY: (
        "Opens by starting a personal story or a moment in time. "
        "Example: 'Kal raat 2 baje mujhe ek call aayi...'"
    ),
    HookType.LIST: "Opens by promising a set of items. Example: '3 cafes in Gulberg you have to try.'",
    HookType.OTHER: "None of the above, or there is too little speech to tell. Use this when unsure.",
}

SYSTEM_PROMPT = """You analyse the structure of short vertical videos (Instagram reels).
You get a reel's timed transcript and its cut times.
Speech may be English, Urdu, or Roman Urdu mixed with English.

Return one JSON object with exactly these keys:
- "hook_type": one of {hook_types}
- "hook_text": the words of the hook, copied from the transcript as spoken.
  Empty string if there is no speech.
- "beats": a list of the reel's parts in time order. Each beat is
  {{"label": short name such as "Hook", "Setup", "Reveal", "Payoff", "CTA",
    "start_s": number, "end_s": number, "description": one sentence on what happens}}.
  Beats must not overlap, must end after they start, and must lie within the reel's length.
- "cta": the call to action, copied as spoken, such as "Follow for part 2". Empty string if there is none.

Hook types:
{definitions}

Judge the hook from the first 3 seconds. Use "other" when unsure rather than guessing.
Return only the JSON object, with no other text."""


class StructuringError(Exception):
    """The model's answer could not be turned into a valid record."""


class _LlmAnswer(BaseModel):
    hook_type: HookType
    hook_text: str
    beats: list[Beat] = Field(min_length=1)
    cta: str


@dataclass(frozen=True)
class StructuringPrompt:
    system: str
    user: str


# Takes the system and user prompt, returns the model's raw text.
CallLlm = Callable[[StructuringPrompt], Awaitable[str]]


def _format_seconds(value: float) -> str:
    return f"{value:.1f}"


def build_prompt(signals: ReelSignals) -> StructuringPrompt:
    system = SYSTEM_PROMPT.format(
        hook_types=", ".join(f'"{item.value}"' for item in HookType),
        definitions="\n".join(f'- "{item.value}": {text}' for item, text in HOOK_DEFINITIONS.items()),
    )
    transcript = "\n".join(
        f"[{_format_seconds(segment.start_s)}-{_format_seconds(segment.end_s)}] {segment.text.strip()}"
        for segment in signals.transcript
    )
    cuts = ", ".join(_format_seconds(cut) for cut in signals.cut_times_s) or "none"
    user = (
        f"Reel length: {_format_seconds(signals.length_s)} s\n"
        f"Cuts at (s): {cuts}\n"
        f"Detected language: {signals.detected_language or 'unknown'}\n"
        f"Speech in the first 3 seconds: {signals.hook_candidate_text or '(none)'}\n\n"
        f"Transcript:\n{transcript or '(no speech)'}"
    )
    return StructuringPrompt(system=system, user=user)


def parse_response(raw: str, signals: ReelSignals) -> _LlmAnswer:
    try:
        answer = parse_json_answer(raw, _LlmAnswer)
    except LlmAnswerError as error:
        raise StructuringError(str(error)) from error
    _check_beats(answer.beats, signals.length_s)
    return answer


def _check_beats(beats: Sequence[Beat], length_s: float) -> None:
    for earlier, later in zip(beats, beats[1:], strict=False):
        if later.start_s < earlier.end_s:
            raise StructuringError(f"Beats '{earlier.label}' and '{later.label}' overlap.")
    if beats[-1].end_s > length_s + BEAT_END_TOLERANCE_S:
        raise StructuringError(f"The last beat ends after the reel's length of {length_s:.1f} s.")


def _retry_prompt(prompt: StructuringPrompt, problem: str) -> StructuringPrompt:
    return StructuringPrompt(
        system=prompt.system,
        user=f"{prompt.user}\n\nYour previous answer was rejected: {problem} {RETRY_INSTRUCTION}",
    )


async def structure(
    signals: ReelSignals,
    call_llm: CallLlm,
    model_version: str,
    overlays: Sequence[Overlay] = (),
) -> DnaRecord:
    """`overlays` come from OCR or a vision model when wired. The LLM is never asked to guess them."""
    prompt = build_prompt(signals)
    try:
        answer = parse_response(await call_llm(prompt), signals)
    except StructuringError as first_problem:
        answer = parse_response(await call_llm(_retry_prompt(prompt, str(first_problem))), signals)
    return DnaRecord(
        signals=signals,
        hook_type=answer.hook_type,
        hook_text=answer.hook_text,
        beats=answer.beats,
        overlays=list(overlays),
        cta=answer.cta,
        model_version=f"{model_version}/{PROMPT_VERSION}",
    )
