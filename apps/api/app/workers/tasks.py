"""Task names and the queue each one runs on (docs/backend.md, Jobs 3).

Kept free of Celery imports so the API can name a task without loading worker code.
"""

from enum import StrEnum


class Queue(StrEnum):
    VIDEO = "video"
    AI = "ai"
    DEFAULT = "default"


class TaskName(StrEnum):
    INSTAGRAM_IMPORT = "instagram.import"
    INSTAGRAM_REFRESH_TOKENS = "instagram.refresh_tokens"
    DNA_ANALYSE = "dna.analyse"
    SCRIPTS_GENERATE = "scripts.generate"
    COMMENTS_SYNC = "comments.sync"
    HOOKS_SCORE = "hooks.score"
    VIDEOS_EDIT = "videos.edit"
    EXPERIMENTS_CREATE = "experiments.create"
    EXPERIMENTS_PUBLISH = "experiments.publish"
    EXPERIMENTS_COLLECT_INSIGHTS = "experiments.collect_insights"
    REPORTS_WEEKLY = "reports.weekly"
    REPORTS_WEEKLY_ALL = "reports.weekly_all"


TASK_QUEUES: dict[TaskName, Queue] = {
    TaskName.INSTAGRAM_IMPORT: Queue.DEFAULT,
    TaskName.INSTAGRAM_REFRESH_TOKENS: Queue.DEFAULT,
    TaskName.DNA_ANALYSE: Queue.VIDEO,
    TaskName.SCRIPTS_GENERATE: Queue.AI,
    TaskName.COMMENTS_SYNC: Queue.AI,
    TaskName.HOOKS_SCORE: Queue.AI,
    TaskName.VIDEOS_EDIT: Queue.VIDEO,
    TaskName.EXPERIMENTS_CREATE: Queue.AI,
    # Publishing renders each variant's hook overlay with FFmpeg first.
    TaskName.EXPERIMENTS_PUBLISH: Queue.VIDEO,
    TaskName.EXPERIMENTS_COLLECT_INSIGHTS: Queue.DEFAULT,
    TaskName.REPORTS_WEEKLY: Queue.DEFAULT,
    TaskName.REPORTS_WEEKLY_ALL: Queue.DEFAULT,
}
