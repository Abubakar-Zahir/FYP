"""The scripts.generate job (P1-06): DNA template plus the creator's voice in, a script out."""

import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dna import DnaRecordRow
from app.models.reel import Reel, ReelSource
from app.models.script import Script
from app.schemas.scripts import GenerateResult
from app.services import llm, users
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError
from ml.dna.schema import DnaRecord
from ml.scripts.generate import (
    MAX_OUTPUT_TOKENS,
    PROMPT_VERSION,
    CallLlm,
    ScriptGenerationError,
    ScriptPrompt,
    generate,
)
from ml.scripts.schema import MAX_VOICE_SAMPLES, CreatorVoice, ScriptLanguage, ScriptRequest

logger = logging.getLogger(__name__)

PURPOSE = "scripts.generate"
HttpFactory = Callable[[], httpx.AsyncClient]


async def recent_captions(session: AsyncSession, user_id: UUID) -> list[str]:
    """The creator's latest captions, as examples of how they write (voice matching v0)."""
    query = (
        select(Reel.caption)
        .where(Reel.user_id == user_id, Reel.source == ReelSource.OWN, Reel.caption.is_not(None))
        .order_by(Reel.posted_at.desc())
        .limit(MAX_VOICE_SAMPLES)
    )
    return [caption for caption in (await session.execute(query)).scalars() if caption and caption.strip()]


def _caller(client: llm.LlmClient, user_id: UUID) -> CallLlm:
    async def call(prompt: ScriptPrompt) -> str:
        return await client.complete(
            llm.LlmPrompt(system=prompt.system, user=prompt.user, max_output_tokens=MAX_OUTPUT_TOKENS),
            purpose=PURPOSE,
            prompt_version=PROMPT_VERSION,
            user_id=user_id,
        )

    return call


async def _request(session: AsyncSession, script: Script) -> ScriptRequest:
    user = await users.get_user(session, script.user_id)
    template = await session.get(DnaRecordRow, script.template_id)
    if user is None:
        raise JobFailure("profile_missing")
    if template is None or template.user_id != script.user_id:
        raise JobFailure("template_not_found")
    return ScriptRequest(
        topic=script.topic,
        language=ScriptLanguage(script.language),
        creator=CreatorVoice(
            niche=user.niche,
            tone=user.tone,
            goals=user.goals,
            sample_captions=await recent_captions(session, script.user_id),
        ),
        templates=[DnaRecord.model_validate(template.record)],
    )


async def _generate(context: JobContext, http_factory: HttpFactory) -> GenerateResult:
    session = context.session
    script = await session.get(Script, context.job.subject_id) if context.job.subject_id else None
    if script is None or script.user_id != context.job.user_id:
        raise JobFailure("script_not_found")
    request = await _request(session, script)
    async with http_factory() as http:
        try:
            client = llm.build_llm_client(context.settings, http, llm.DatabaseLedger(session))
            draft = await generate(request, _caller(client, script.user_id), client.model_version)
        except llm.LlmNotConfigured as error:
            raise JobFailure("llm_not_configured") from error
        except llm.LlmBudgetExceeded as error:
            raise JobFailure("llm_budget_exceeded") from error
        except llm.LlmUnavailable as error:
            raise TransientJobError("llm_unavailable") from error
        except (llm.LlmRequestRejected, llm.LlmBadResponse, ScriptGenerationError) as error:
            logger.warning("Script generation failed: %s", type(error).__name__)
            raise JobFailure("script_generation_failed") from error
    script.hooks = [{"text": hook.text, "score": None, "top_factors": []} for hook in draft.hooks]
    script.angles = [angle.model_dump() for angle in draft.angles]
    script.body = [beat.model_dump() for beat in draft.body]
    script.model_version = draft.model_version
    await session.commit()
    return GenerateResult(script_id=script.id)


def make_generate_handler(http_factory: HttpFactory) -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        return (await _generate(context, http_factory)).model_dump(mode="json")

    return handle
