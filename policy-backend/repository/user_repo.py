from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserModel


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: dict) -> UserModel:
        user = UserModel(**user_data)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_email(self, email: str) -> UserModel | None:
        return await self.session.scalar(select(UserModel).where(UserModel.email == email))

    async def get_by_id(self, user_id: str) -> UserModel | None:
        return await self.session.scalar(select(UserModel).where(UserModel.id == user_id))

    async def create(self, user: UserModel) -> UserModel:
        self.session.add(user)
        await self.session.flush()
        return user
