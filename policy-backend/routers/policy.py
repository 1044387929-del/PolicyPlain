import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session_instance
from models.user import PolicyExplanationModel, UserModel
from repository.policy_repo import PolicyRepo
from schemas.policy import (
    ExplainRequest,
    ExplainResponse,
    ExplanationDetailResponse,
    ExplanationListItem,
    ExplanationListResponse,
    ExplainResultFields,
)
from services.explain_llm import generate_structured_explain, normalize_to_schema
from settings import settings

router = APIRouter(prefix="/policy", tags=["policy"])

ALLOWED_TOPICS = frozenset({"general", "medical_insurance", "pension"})


@router.post("/explain", response_model=ExplainResponse)
async def explain(
    body: ExplainRequest,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    text = body.text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="文本不能为空")
    if len(text) > settings.POLICY_TEXT_MAX_CHARS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="文本过长")

    topic = body.topic or "general"
    if topic not in ALLOWED_TOPICS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="无效的主题标签")

    raw = await generate_structured_explain(text, topic)
    normalized = normalize_to_schema(raw)

    async with session.begin():
        repo = PolicyRepo(session)
        row = PolicyExplanationModel(
            id=str(uuid.uuid4()),
            user_id=current.id,
            topic=topic,
            input_text=text,
            input_digest=text[:300],
            result_json=normalized.model_dump(),
            model=normalized.model,
        )
        await repo.create(row)

    payload = normalized.model_dump()
    return ExplainResponse(record_id=row.id, **payload)


@router.get("/explanations", response_model=ExplanationListResponse)
async def list_explanations(
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    async with session.begin():
        repo = PolicyRepo(session)
        rows = await repo.list_for_user(current.id, limit=limit, offset=offset)
        total = await repo.count_for_user(current.id)

    items: list[ExplanationListItem] = []
    for r in rows:
        summary = None
        if isinstance(r.result_json, dict):
            summary = r.result_json.get("summary_one_line")
        items.append(
            ExplanationListItem(
                record_id=r.id,
                topic=r.topic,
                created_at=r.created_at,
                summary_one_line=str(summary) if summary else None,
            )
        )
    return ExplanationListResponse(items=items, total=total)


@router.get("/explanations/{record_id}", response_model=ExplanationDetailResponse)
async def get_explanation(
    record_id: str,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    async with session.begin():
        repo = PolicyRepo(session)
        row = await repo.get_by_id_for_user(record_id, current.id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="记录不存在")

    result = ExplainResultFields.model_validate(row.result_json)
    return ExplanationDetailResponse(
        record_id=row.id,
        topic=row.topic,
        created_at=row.created_at,
        input_text=row.input_text,
        result=result,
    )
