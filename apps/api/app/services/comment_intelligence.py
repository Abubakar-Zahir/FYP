"""The comments.sync job: classify new comments, then rebuild themes and ideas (SRS FR-7.2 to 7.5)."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.models.reel import Comment, CommentTheme
from app.models.user import User
from app.schemas.comments import SyncResult
from app.services import llm
from app.workers.runner import JobContext, JobFailure, JobHandler, TransientJobError
from ml.comments.ideas import MAX_OUTPUT_TOKENS, PROMPT_VERSION, CallLlm, ThemeInput, name_themes
from ml.comments.labels import CommentLabel
from ml.comments.models import CommentClassifier, load_sklearn_classifier
from ml.comments.themes import find_themes

logger = logging.getLogger(__name__)

THEME_WINDOW_DAYS = 90
CLASSIFY_BATCH = 200
NO_LLM = "no-llm"

HttpFactory = Callable[[], httpx.AsyncClient]
ClassifierLoader = Callable[[Settings], CommentClassifier]


def load_classifier(settings: Settings) -> CommentClassifier:
    """A .joblib file is the CPU model. A folder is the XLM-R ONNX export (needs the nlp group)."""
    if not settings.comment_model_path:
        raise JobFailure("comment_model_not_configured")
    path = Path(settings.comment_model_path)
    if path.is_file():
        return load_sklearn_classifier(path)
    if path.is_dir():
        from ml.comments.onnx_model import XlmrOnnxClassifier

        return XlmrOnnxClassifier(path)
    raise JobFailure("comment_model_missing")


async def _classify_new(session: AsyncSession, user_id: UUID, classifier: CommentClassifier) -> int:
    pending = list(
        (
            await session.execute(select(Comment).where(Comment.user_id == user_id, Comment.label.is_(None)))
        ).scalars()
    )
    for start in range(0, len(pending), CLASSIFY_BATCH):
        batch = pending[start : start + CLASSIFY_BATCH]
        for comment, label in zip(batch, classifier.predict([item.text for item in batch]), strict=True):
            comment.label = label.value
            comment.label_model_version = classifier.name
    await session.commit()
    return len(pending)


def _llm_caller(context: JobContext, http: httpx.AsyncClient) -> CallLlm | None:
    try:
        client = llm.build_llm_client(context.settings, http, llm.DatabaseLedger(context.session))
    except llm.LlmNotConfigured:
        return None
    user_id = context.job.user_id

    async def call(system: str, user: str) -> str:
        return await client.complete(
            llm.LlmPrompt(system=system, user=user, max_output_tokens=MAX_OUTPUT_TOKENS),
            purpose="comments.ideas",
            prompt_version=PROMPT_VERSION,
            user_id=user_id,
        )

    return call


async def _rebuild_themes(context: JobContext, http: httpx.AsyncClient, classifier_name: str) -> int:
    session, user_id = context.session, context.job.user_id
    since = datetime.now(UTC) - timedelta(days=THEME_WINDOW_DAYS)
    recent = list(
        (
            await session.execute(
                select(Comment).where(
                    Comment.user_id == user_id, Comment.label.is_not(None), Comment.posted_at >= since
                )
            )
        ).scalars()
    )
    found = find_themes([item.text for item in recent], [CommentLabel(str(item.label)) for item in recent])
    user = await session.get(User, user_id)
    inputs = [
        ThemeInput(
            terms=theme.terms,
            dominant_label=theme.dominant_label,
            examples=[recent[index].text for index in theme.examples],
        )
        for theme in found
    ]
    call = _llm_caller(context, http)
    try:
        ideas = await name_themes(user.niche if user else "", inputs, call)
    except llm.LlmUnavailable as error:
        raise TransientJobError("llm_unavailable") from error
    except (llm.LlmBudgetExceeded, llm.LlmRequestRejected, llm.LlmBadResponse):
        logger.warning("Theme ideas fell back to plain text")
        ideas = await name_themes("", inputs, None)
    await session.execute(delete(CommentTheme).where(CommentTheme.user_id == user_id))
    version = f"{classifier_name}+nmf/{PROMPT_VERSION if call else NO_LLM}"
    for theme, idea in zip(found, ideas, strict=True):
        session.add(
            CommentTheme(
                user_id=user_id,
                theme=idea.name,
                size=theme.size,
                dominant_label=theme.dominant_label.value,
                example_comment_ids=[str(recent[index].id) for index in theme.examples],
                idea=idea.idea,
                model_version=version,
            )
        )
    await session.commit()
    return len(found)


def make_sync_handler(http_factory: HttpFactory, loader: ClassifierLoader = load_classifier) -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        classifier = loader(context.settings)
        labelled = await _classify_new(context.session, context.job.user_id, classifier)
        await context.progress(0.5)
        async with http_factory() as http:
            theme_count = await _rebuild_themes(context, http, classifier.name)
        return SyncResult(labelled=labelled, themes=theme_count).model_dump()

    return handle
