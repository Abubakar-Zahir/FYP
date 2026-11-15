"""Script generation v1: 5 hooks, 3 angles and a full script, grounded in DNA templates.

Grounding means the script follows the template's structure (beat order, hook type,
pacing and CTA) on the creator's own topic, in the creator's voice. It never copies the
template's words. The LLM is passed in, as in ml/dna/structure.py.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pydantic import BaseModel, Field

from ml.common.llm_json import LlmAnswerError, parse_json_answer
from ml.dna.schema import DnaRecord
from ml.scripts.schema import (
    ANGLE_COUNT,
    HOOK_COUNT,
    MIN_BEATS,
    Angle,
    Hook,
    ScriptBeat,
    ScriptDraft,
    ScriptLanguage,
    ScriptRequest,
)

PROMPT_VERSION = "script-v1"
MAX_OUTPUT_TOKENS = 2500
RETRY_INSTRUCTION = "Return a corrected JSON object only."

LANGUAGE_RULES: dict[ScriptLanguage, str] = {
    ScriptLanguage.ENGLISH: "Write in simple spoken English.",
    ScriptLanguage.ROMAN_URDU: (
        "Write in Roman Urdu: Urdu words in Latin letters, the way Pakistani creators type them "
        "(for example 'Ye jagah kamaal hai'). Never use Urdu script."
    ),
    ScriptLanguage.MIXED: (
        "Mix Roman Urdu and English the way Pakistani creators speak, switching mid-sentence where natural. "
        "Never use Urdu script."
    ),
}

SYSTEM_PROMPT = f"""You write short vertical video scripts (Instagram reels, under 60 s) for one creator.
You get the creator's niche, tone and some of their own captions, a topic, and one or more format templates.
Each template is the structure of a reel that worked:
its hook type, beats with timings, pacing and call to action.

Follow the template's structure on the new topic. Never copy the template's words.
Sound like the creator's own captions. Keep every line short enough to say in one breath.

Return one JSON object with exactly these keys:
- "hooks": {HOOK_COUNT} different opening lines, each {{"text": ...}}, first 3 seconds only.
- "angles": {ANGLE_COUNT} different ways to approach the topic,
  each {{"title": ..., "summary": one sentence}}.
- "body": the full script for the first angle as a list of at least {MIN_BEATS} beats in order, each
  {{"beat": the template beat it follows, such as "Hook",
    "line": what the creator says, "shot": what the camera shows}}.
Return only the JSON object, with no other text."""


class ScriptGenerationError(Exception):
    pass


class _LlmAnswer(BaseModel):
    hooks: list[Hook] = Field(min_length=HOOK_COUNT, max_length=HOOK_COUNT)
    angles: list[Angle] = Field(min_length=ANGLE_COUNT, max_length=ANGLE_COUNT)
    body: list[ScriptBeat] = Field(min_length=MIN_BEATS)


@dataclass(frozen=True)
class ScriptPrompt:
    system: str
    user: str


CallLlm = Callable[[ScriptPrompt], Awaitable[str]]


def describe_template(index: int, template: DnaRecord) -> str:
    beats = "\n".join(
        f"  - {beat.label} ({beat.start_s:.0f}-{beat.end_s:.0f} s): {beat.description}"
        for beat in template.beats
    )
    return (
        f"Template {index}: hook type {template.hook_type.value}, "
        f"{template.signals.length_s:.0f} s long, {template.signals.pacing_cuts_per_10s:.1f} cuts per 10 s.\n"
        f'  Hook used: "{template.hook_text or "(no speech)"}"\n'
        f"  Beats:\n{beats}\n"
        f'  Call to action: "{template.cta or "(none)"}"'
    )


def build_prompt(request: ScriptRequest) -> ScriptPrompt:
    creator = request.creator
    samples = "\n".join(f'- "{caption.strip()}"' for caption in creator.sample_captions if caption.strip())
    templates = "\n\n".join(describe_template(index, item) for index, item in enumerate(request.templates, 1))
    user = (
        f"Creator niche: {creator.niche}\n"
        f"Tone: {creator.tone}\n"
        f"Goals: {creator.goals}\n"
        f"Language: {LANGUAGE_RULES[request.language]}\n"
        f"Some of the creator's own captions:\n{samples or '(none yet)'}\n\n"
        f"Topic: {request.topic}\n\n"
        f"{templates}"
    )
    return ScriptPrompt(system=SYSTEM_PROMPT, user=user)


def _retry(prompt: ScriptPrompt, problem: str) -> ScriptPrompt:
    return ScriptPrompt(
        system=prompt.system,
        user=f"{prompt.user}\n\nYour previous answer was rejected: {problem} {RETRY_INSTRUCTION}",
    )


async def generate(request: ScriptRequest, call_llm: CallLlm, model_version: str) -> ScriptDraft:
    prompt = build_prompt(request)
    try:
        answer = parse_json_answer(await call_llm(prompt), _LlmAnswer)
    except LlmAnswerError as first_problem:
        try:
            answer = parse_json_answer(await call_llm(_retry(prompt, str(first_problem))), _LlmAnswer)
        except LlmAnswerError as error:
            raise ScriptGenerationError(str(error)) from error
    return ScriptDraft(
        hooks=answer.hooks,
        angles=answer.angles,
        body=answer.body,
        model_version=f"{model_version}/{PROMPT_VERSION}",
    )
