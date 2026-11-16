from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.job import Job
from app.models.script import Script
from app.schemas.scripts import GenerateScriptRequest, ScoredHook, ScriptOut
from app.services import dna, jobs, users
from app.workers.queue import JobQueue
from app.workers.tasks import TaskName
from ml.scripts.schema import Angle, ScriptBeat, ScriptLanguage


def script_not_found() -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, "script_not_found", "No such script.")


def profile_missing() -> ApiError:
    return ApiError(
        status.HTTP_409_CONFLICT,
        "profile_missing",
        "Finish onboarding first, so scripts can match your niche and tone.",
    )


async def start_generation(
    session: AsyncSession, queue: JobQueue, user_id: UUID, request: GenerateScriptRequest
) -> Job:
    """Checks the template and profile before queueing, so the job can't fail for those reasons."""
    await dna.get_for_user(session, request.template_id, user_id)
    if await users.get_user(session, user_id) is None:
        raise profile_missing()
    script = Script(
        user_id=user_id, template_id=request.template_id, topic=request.topic, language=request.language.value
    )
    session.add(script)
    await session.commit()
    return await jobs.start_job(session, queue, user_id, TaskName.SCRIPTS_GENERATE, subject_id=script.id)


async def get_ready_script(session: AsyncSession, script_id: UUID, user_id: UUID) -> ScriptOut:
    script = await session.get(Script, script_id)
    if script is None or script.user_id != user_id:
        raise script_not_found()
    if script.hooks is None or script.angles is None or script.body is None or script.model_version is None:
        raise ApiError(
            status.HTTP_409_CONFLICT, "script_not_ready", "The script is still being written. Check the job."
        )
    return ScriptOut(
        id=script.id,
        template_id=script.template_id,
        topic=script.topic,
        language=ScriptLanguage(script.language),
        hooks=[ScoredHook.model_validate(hook) for hook in script.hooks],
        angles=[Angle.model_validate(angle) for angle in script.angles],
        body=[ScriptBeat.model_validate(beat) for beat in script.body],
        model_version=script.model_version,
    )
