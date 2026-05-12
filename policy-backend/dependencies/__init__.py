from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import PolicyCache, get_redis_for_cache
from models import auth_handler, get_session
from models.user import UserModel
from repository.user_repo import UserRepo


async def get_session_instance():
    async for session in get_session():
        yield session


def get_cache_instance() -> PolicyCache:
    """与 hr-backend dependencies.get_cache_instance 命名一致。"""
    return PolicyCache(get_redis_for_cache())


async def get_user_id_str(user_id: str = Depends(auth_handler.auth_access_dependency)) -> str:
    return user_id


async def get_current_user(
    user_id: str = Depends(get_user_id_str),
    session: AsyncSession = Depends(get_session_instance),
) -> UserModel:
    # 单独提交只读事务，避免后续路由里 session.begin() 报「事务已开始」
    async with session.begin():
        repo = UserRepo(session)
        user = await repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
