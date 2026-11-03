from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user

router = APIRouter(tags=["me"])


@router.get("/me")
async def read_me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    return user
