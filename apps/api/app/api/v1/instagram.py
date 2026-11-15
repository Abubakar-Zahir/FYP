from fastapi import APIRouter, Response, status

from app.core.crypto import TokenCipherDependency
from app.core.errors import ApiError
from app.core.http import HttpClientDependency
from app.core.security import CurrentUserDependency
from app.db.session import SessionDependency
from app.schemas.instagram import (
    InstagramAccountOut,
    InstagramAuthorizeUrl,
    InstagramCallback,
    InstagramConnected,
)
from app.schemas.jobs import JobAccepted
from app.services import instagram, instagram_accounts, jobs
from app.services.instagram_accounts import InstagramConfigDependency
from app.workers.queue import JobQueueDependency
from app.workers.tasks import TaskName

router = APIRouter(tags=["instagram"])


@router.get("/instagram/connect")
async def start_connect(
    identity: CurrentUserDependency, cipher: TokenCipherDependency, config: InstagramConfigDependency
) -> InstagramAuthorizeUrl:
    """The web app sends the browser to this URL. Instagram redirects back with a code."""
    state = cipher.oauth_state(identity.id)
    return InstagramAuthorizeUrl(
        authorize_url=instagram.build_authorize_url(config.app_id, config.redirect_uri, state)
    )


@router.post("/instagram/callback", status_code=status.HTTP_202_ACCEPTED)
async def finish_connect(
    callback: InstagramCallback,
    identity: CurrentUserDependency,
    session: SessionDependency,
    http: HttpClientDependency,
    cipher: TokenCipherDependency,
    config: InstagramConfigDependency,
    queue: JobQueueDependency,
) -> InstagramConnected:
    # The state names who started the flow, so a code can't be attached to someone else.
    if cipher.user_from_oauth_state(callback.state) != identity.id:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "invalid_oauth_state",
            "This Instagram link was started by another account. Try connecting again.",
        )
    account = await instagram_accounts.connect(session, http, cipher, config, identity.id, callback.code)
    job = await jobs.start_job(session, queue, identity.id, TaskName.INSTAGRAM_IMPORT)
    return InstagramConnected(instagram=InstagramAccountOut.from_account(account), job_id=job.id)


@router.post("/instagram/import", status_code=status.HTTP_202_ACCEPTED)
async def start_import(
    identity: CurrentUserDependency, session: SessionDependency, queue: JobQueueDependency
) -> JobAccepted:
    if await instagram_accounts.get_account(session, identity.id) is None:
        raise instagram_accounts.not_connected()
    job = await jobs.start_job(session, queue, identity.id, TaskName.INSTAGRAM_IMPORT)
    return JobAccepted(job_id=job.id)


@router.delete("/instagram/account", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(identity: CurrentUserDependency, session: SessionDependency) -> Response:
    await instagram_accounts.disconnect(session, identity.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
