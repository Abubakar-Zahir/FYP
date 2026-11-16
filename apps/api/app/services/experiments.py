"""Experiments: create variants for a video, read them back (SRS FR-6.1 to FR-6.3)."""

import random
import string
from collections.abc import Callable
from typing import Any
from uuid import UUID

import httpx
from fastapi import status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.pagination import Page, decode_cursor, encode_cursor
from app.models.experiment import Experiment, ExperimentStatus, Variant, VariantInsight, VariantStatus
from app.models.job import Job
from app.models.script import Script
from app.models.user import User
from app.models.video import Video
from app.schemas.experiments import (
    SHARE_INSTRUCTIONS,
    CreateExperimentRequest,
    CreateResult,
    ExperimentOut,
    InsightWindow,
    VariantInsightOut,
    VariantOut,
)
from app.services import jobs, llm, videos
from app.services.bandit_store import state_for
from app.services.reels import as_utc
from app.workers.queue import JobQueue
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError
from app.workers.tasks import TaskName
from ml.bandit.thompson import choose
from ml.scripts.generate import LANGUAGE_RULES
from ml.scripts.schema import ScriptLanguage
from ml.variants.generate import (
    MAX_OUTPUT_TOKENS,
    PROMPT_VERSION,
    CallLlm,
    VariantBrief,
    VariantGenerationError,
    generate_candidates,
)

HttpFactory = Callable[[], httpx.AsyncClient]
LABELS = string.ascii_uppercase


def experiment_not_found() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "experiment_not_found", "No such experiment.")


async def get_for_user(session: AsyncSession, experiment_id: UUID, user_id: UUID) -> Experiment:
    experiment = await session.get(Experiment, experiment_id)
    if experiment is None or experiment.user_id != user_id:
        raise experiment_not_found()
    return experiment


async def to_out(session: AsyncSession, experiment: Experiment) -> ExperimentOut:
    video = await session.get(Video, experiment.video_id)
    variants = list(
        (
            await session.execute(
                select(Variant).where(Variant.experiment_id == experiment.id).order_by(Variant.label)
            )
        ).scalars()
    )
    insights = list(
        (
            await session.execute(
                select(VariantInsight).where(VariantInsight.variant_id.in_([v.id for v in variants]))
            )
        ).scalars()
    )
    by_variant: dict[UUID, list[VariantInsightOut]] = {}
    for row in sorted(insights, key=lambda item: item.window):
        by_variant.setdefault(row.variant_id, []).append(
            VariantInsightOut(
                window=InsightWindow(row.window),
                views=row.views,
                reach=row.reach,
                saves=row.saves,
                shares=row.shares,
            )
        )
    return ExperimentOut(
        id=experiment.id,
        video_title=video.title if video else "Deleted video",
        strategy="thompson_sampling",
        status=ExperimentStatus(experiment.status),
        winner_variant_id=experiment.winner_variant_id,
        share_instructions=SHARE_INSTRUCTIONS if experiment.winner_variant_id else None,
        variants=[
            VariantOut(
                id=variant.id,
                label=variant.label,
                hook_line=variant.hook_line,
                hook_style=variant.hook_style,
                opener=variant.opener,
                caption=variant.caption,
                is_trial=variant.is_trial,
                status=VariantStatus(variant.status),
                permalink=variant.permalink,
                error=variant.error,
                insights=by_variant.get(variant.id, []),
            )
            for variant in variants
        ],
    )


async def list_for_user(
    session: AsyncSession, user_id: UUID, limit: int, cursor: str | None
) -> Page[ExperimentOut]:
    query = select(Experiment).where(Experiment.user_id == user_id)
    if cursor is not None:
        position = decode_cursor(cursor)
        query = query.where(
            or_(
                Experiment.created_at < position.at,
                and_(Experiment.created_at == position.at, Experiment.id < position.id),
            )
        )
    rows = list(
        (
            await session.execute(
                query.order_by(Experiment.created_at.desc(), Experiment.id.desc()).limit(limit + 1)
            )
        ).scalars()
    )
    page = rows[:limit]
    next_cursor = encode_cursor(as_utc(page[-1].created_at), page[-1].id) if len(rows) > limit else None
    return Page[ExperimentOut](items=[await to_out(session, item) for item in page], next_cursor=next_cursor)


async def start_creation(
    session: AsyncSession, queue: JobQueue, user_id: UUID, request: CreateExperimentRequest
) -> Job:
    video = await videos.get_for_user(session, request.video_id, user_id)
    if not video.output_r2_key:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "video_not_edited",
            "Edit the video first, so every variant uses the same cut.",
        )
    if request.script_id is not None:
        script = await session.get(Script, request.script_id)
        if script is None or script.user_id != user_id:
            raise ApiError(status.HTTP_404_NOT_FOUND, "script_not_found", "No such script.")
    return await jobs.start_job(
        session, queue, user_id, TaskName.EXPERIMENTS_CREATE, payload=request.model_dump(mode="json")
    )


async def _brief(session: AsyncSession, user_id: UUID, video: Video, script: Script | None) -> VariantBrief:
    user = await session.get(User, user_id)
    if user is None:
        raise JobFailure("profile_missing")
    language = ScriptLanguage(script.language) if script else ScriptLanguage.MIXED
    return VariantBrief(
        topic=script.topic if script else video.title,
        niche=user.niche,
        tone=user.tone,
        hooks=[str(hook["text"]) for hook in (script.hooks or [])] if script else [],
        script_lines=[str(beat["line"]) for beat in (script.body or [])] if script else [],
        language_rule=LANGUAGE_RULES[language],
    )


def _caller(client: llm.LlmClient, user_id: UUID) -> CallLlm:
    async def call(system: str, user: str) -> str:
        return await client.complete(
            llm.LlmPrompt(system=system, user=user, max_output_tokens=MAX_OUTPUT_TOKENS),
            purpose="experiments.variants",
            prompt_version=PROMPT_VERSION,
            user_id=user_id,
        )

    return call


def make_create_handler(http_factory: HttpFactory, rng: random.Random | None = None) -> JobHandler:
    chooser = rng or random.Random()  # noqa: S311 (exploration, not security)

    async def handle(context: JobContext) -> dict[str, Any]:
        session, user_id = context.session, context.job.user_id
        request = CreateExperimentRequest.model_validate(context.job.payload or {})
        video = await session.get(Video, request.video_id)
        if video is None or video.user_id != user_id:
            raise JobFailure("video_not_found")
        script = await session.get(Script, request.script_id) if request.script_id else None
        brief = await _brief(session, user_id, video, script)
        async with http_factory() as http:
            try:
                client = llm.build_llm_client(context.settings, http, llm.DatabaseLedger(session))
                candidates = await generate_candidates(brief, request.variant_count, _caller(client, user_id))
            except llm.LlmNotConfigured as error:
                raise JobFailure("llm_not_configured") from error
            except llm.LlmBudgetExceeded as error:
                raise JobFailure("llm_budget_exceeded") from error
            except llm.LlmUnavailable as error:
                raise TransientJobError("llm_unavailable") from error
            except (llm.LlmRequestRejected, llm.LlmBadResponse, VariantGenerationError) as error:
                raise JobFailure("variant_generation_failed") from error
        state = await state_for(session, user_id)
        picks = choose(state, [c.features() for c in candidates], request.variant_count, chooser)
        experiment = Experiment(user_id=user_id, video_id=video.id, script_id=request.script_id)
        session.add(experiment)
        await session.flush()
        for label, index in zip(LABELS, picks, strict=False):
            candidate = candidates[index]
            features = candidate.features()
            session.add(
                Variant(
                    experiment_id=experiment.id,
                    user_id=user_id,
                    label=label,
                    hook_line=candidate.hook_line,
                    hook_style=features["hook_style"],
                    opener=candidate.opener,
                    opener_type=features["opener"],
                    caption=candidate.full_caption(),
                    caption_length=features["caption_length"],
                )
            )
        await session.commit()
        return CreateResult(experiment_id=experiment.id).model_dump(mode="json")

    return handle
