from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user
from models import get_session
from models.user import UserModel
from schemas.policy import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def me(current: UserModel = Depends(get_current_user)):
    return UserPublic(id=current.id, email=current.email)
