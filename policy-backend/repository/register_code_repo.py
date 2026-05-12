from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.register_email_code import RegisterEmailCodeModel


class RegisterCodeRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> RegisterEmailCodeModel | None:
        r = await self.session.execute(
            select(RegisterEmailCodeModel).where(RegisterEmailCodeModel.email == email)
        )
        return r.scalar_one_or_none()

    async def replace(self, row: RegisterEmailCodeModel) -> None:
        await self.session.execute(
            delete(RegisterEmailCodeModel).where(RegisterEmailCodeModel.email == row.email)
        )
        self.session.add(row)
        await self.session.flush()

    async def delete_by_email(self, email: str) -> None:
        await self.session.execute(
            delete(RegisterEmailCodeModel).where(RegisterEmailCodeModel.email == email)
        )
        await self.session.flush()
