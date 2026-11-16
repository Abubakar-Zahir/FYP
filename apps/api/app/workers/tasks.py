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


TASK_QUEUES: dict[TaskName, Queue] = {
    TaskName.INSTAGRAM_IMPORT: Queue.DEFAULT,
    TaskName.INSTAGRAM_REFRESH_TOKENS: Queue.DEFAULT,
    TaskName.DNA_ANALYSE: Queue.VIDEO,
    TaskName.SCRIPTS_GENERATE: Queue.AI,
    TaskName.COMMENTS_SYNC: Queue.AI,
}
