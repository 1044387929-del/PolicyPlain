from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserModel


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> UserModel | None:
        r = await self.session.execute(select(UserModel).where(UserModel.email == email))
        return r.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> UserModel | None:
        r = await self.session.execute(select(UserModel).where(UserModel.id == user_id))
        return r.scalar_one_or_none()

    async def create(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.flush()
        return user
