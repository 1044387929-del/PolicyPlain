from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models import auth_handler, get_session
from models.user import UserModel
from repository.user_repo import UserRepo


async def get_user_id_str(user_id: str = Depends(auth_handler.auth_access_dependency)) -> str:
    return user_id


async def get_current_user(
    user_id: str = Depends(get_user_id_str),
    session: AsyncSession = Depends(get_session),
) -> UserModel:
    repo = UserRepo(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
