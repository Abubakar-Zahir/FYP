"""Scores hooks with the trained model at HOOK_SCORER_PATH (SRS FR-4.1, FR-4.3).

Runs only inside workers (CLAUDE.md rule 7). Without a model, hooks stay unscored rather
than getting a made-up number.
"""

from collections.abc import Sequence
from functools import cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.settings import Settings
from app.workers.runner import JobContext, JobFailure, JobHandler
from ml.dna.schema import HookType
from ml.scoring.model import HookScorer

MAX_HOOKS = 10


class HookScoreRequest(BaseModel):
    hooks: list[str] = Field(min_length=1, max_length=MAX_HOOKS)
    hook_type: HookType | None = None


@cache
def _load(path: str) -> HookScorer:
    """Loaded once per worker process."""
    return HookScorer.load(Path(path))


def load_scorer(settings: Settings) -> HookScorer | None:
    if not settings.hook_scorer_path:
        return None
    if not Path(settings.hook_scorer_path).is_dir():
        raise JobFailure("hook_scorer_missing")
    return _load(settings.hook_scorer_path)


def scored_hooks(
    scorer: HookScorer | None, texts: Sequence[str], hook_type: HookType | None
) -> list[dict[str, Any]]:
    """The ScoredHook shape the API returns, as JSON-ready dicts."""
    if scorer is None:
        return [{"text": text, "score": None, "top_factors": []} for text in texts]
    scores = scorer.score(texts, [hook_type] * len(texts))
    return [
        {
            "text": text,
            "score": float(score.score),
            "top_factors": [{"label": factor.label, "impact": factor.impact} for factor in score.top_factors],
        }
        for text, score in zip(texts, scores, strict=True)
    ]


def make_score_handler() -> JobHandler:
    async def handle(context: JobContext) -> dict[str, Any]:
        request = HookScoreRequest.model_validate(context.job.payload or {})
        scorer = load_scorer(context.settings)
        if scorer is None:
            raise JobFailure("hook_scorer_not_configured")
        return {
            "hooks": scored_hooks(scorer, request.hooks, request.hook_type),
            "model_version": scorer.version,
        }

    return handle
