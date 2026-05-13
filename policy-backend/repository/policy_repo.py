from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import PolicyExplanationModel, PolicyFollowupModel


class PolicyRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, row: PolicyExplanationModel) -> PolicyExplanationModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_id_for_user(self, record_id: str, user_id: str) -> PolicyExplanationModel | None:
        r = await self.session.execute(
            select(PolicyExplanationModel).where(
                PolicyExplanationModel.id == record_id,
                PolicyExplanationModel.user_id == user_id,
            )
        )
        return r.scalar_one_or_none()

    async def list_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[PolicyExplanationModel]:
        r = await self.session.execute(
            select(PolicyExplanationModel)
            .where(PolicyExplanationModel.user_id == user_id)
            .order_by(PolicyExplanationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(r.scalars().all())

    async def count_for_user(self, user_id: str) -> int:
        r = await self.session.execute(
            select(func.count()).select_from(PolicyExplanationModel).where(
                PolicyExplanationModel.user_id == user_id
            )
        )
        return int(r.scalar_one())

    async def count_followups(self, explanation_id: str) -> int:
        r = await self.session.execute(
            select(func.count()).select_from(PolicyFollowupModel).where(
                PolicyFollowupModel.explanation_id == explanation_id
            )
        )
        return int(r.scalar_one())

    async def list_followups_for_explanation(self, explanation_id: str) -> list[PolicyFollowupModel]:
        r = await self.session.execute(
            select(PolicyFollowupModel)
            .where(PolicyFollowupModel.explanation_id == explanation_id)
            .order_by(PolicyFollowupModel.turn_index.asc())
        )
        return list(r.scalars().all())

    async def create_followup(self, row: PolicyFollowupModel) -> PolicyFollowupModel:
        self.session.add(row)
        await self.session.flush()
        return row
