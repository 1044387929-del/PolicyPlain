import json
import uuid
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from openai import APIError, AuthenticationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session_instance
from models.user import PolicyExplanationModel, UserModel
from repository.policy_repo import PolicyRepo
from schemas.policy import (
    ExplainFromUrlRequest,
    ExplainRequest,
    ExplainResponse,
    ExplanationDetailResponse,
    ExplanationListItem,
    ExplanationListResponse,
    ExplainResultFields,
)
from services.explain_llm import (
    extract_synopsis_from_web_plain,
    llm_token_stream,
    normalize_to_schema,
    sse_event,
)
from services.url_fetch import assert_public_http_url, fetch_html, html_to_plain_text
from settings import settings

router = APIRouter(prefix="/policy", tags=["policy"])

ALLOWED_TOPICS = frozenset({"general", "medical_insurance", "pension"})


async def _stream_explain_and_save(
    text_for_llm: str,
    topic: str,
    session: AsyncSession,
    current: UserModel,
    persist_input_text: str,
) -> AsyncIterator[str]:
    if len(text_for_llm) > settings.POLICY_TEXT_MAX_CHARS:
        yield sse_event({"event": "error", "detail": "用于解读的文本过长"})
        return

    acc = ""
    try:
        async for piece in llm_token_stream(text_for_llm, topic):
            acc += piece
            yield sse_event({"event": "delta", "text": piece})
    except AuthenticationError:
        yield sse_event(
            {
                "event": "error",
                "detail": (
                    "大模型 API 密钥无效（百炼返回 401）。请检查 DASHSCOPE_API_KEY / OPENAI_API_KEY，"
                    "并在百炼控制台确认密钥有效。"
                ),
            }
        )
        return
    except APIError as e:
        yield sse_event({"event": "error", "detail": str(e) or "大模型接口调用失败"})
        return

    try:
        raw = json.loads(acc)
    except json.JSONDecodeError:
        yield sse_event({"event": "error", "detail": "模型输出不是合法 JSON，无法保存记录"})
        return

    try:
        normalized = normalize_to_schema(raw)
    except ValidationError as e:
        yield sse_event({"event": "error", "detail": f"结果字段校验失败：{e!s}"})
        return

    store_text = persist_input_text.strip()
    if len(store_text) > 80000:
        store_text = store_text[:80000]

    row_id = str(uuid.uuid4())
    async with session.begin():
        repo = PolicyRepo(session)
        row = PolicyExplanationModel(
            id=row_id,
            user_id=current.id,
            topic=topic,
            input_text=store_text,
            input_digest=store_text[:300],
            result_json=normalized.model_dump(),
            model=normalized.model,
        )
        await repo.create(row)

    out = ExplainResponse(record_id=row.id, **normalized.model_dump())
    yield sse_event({"event": "done", **out.model_dump()})


def _sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


@router.post("/explain")
async def explain(
    body: ExplainRequest,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    """流式解读：SSE，`event` 为 `delta` | `done` | `error`。"""
    text = body.text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="文本不能为空")
    if len(text) > settings.POLICY_TEXT_MAX_CHARS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="文本过长")

    topic = body.topic or "general"
    if topic not in ALLOWED_TOPICS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="无效的主题标签")

    return StreamingResponse(
        _stream_explain_and_save(text, topic, session, current, text),
        media_type="text/event-stream; charset=utf-8",
        headers=_sse_headers(),
    )


@router.post("/explain-from-url")
async def explain_from_url(
    body: ExplainFromUrlRequest,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    """从网址抓取网页 → 提炼政策要点 → 流式白话解读。SSE 含 `status` 阶段提示。"""
    safe_url = assert_public_http_url(body.url)
    topic = body.topic or "general"
    if topic not in ALLOWED_TOPICS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="无效的主题标签")

    async def from_url_stream() -> AsyncIterator[str]:
        yield sse_event({"event": "status", "stage": "fetch", "message": "正在抓取网页…"})
        try:
            html_bytes, final_url = await fetch_html(safe_url)
        except httpx.HTTPStatusError as e:
            yield sse_event(
                {"event": "error", "detail": f"网页返回错误：HTTP {e.response.status_code}"},
            )
            return
        except httpx.HTTPError as e:
            yield sse_event({"event": "error", "detail": f"抓取网页失败：{e!s}"})
            return

        yield sse_event({"event": "status", "stage": "parse", "message": "正在提取正文…"})
        plain = await html_to_plain_text(html_bytes, final_url)
        if len(plain) < 80:
            yield sse_event(
                {
                    "event": "error",
                    "detail": "未能从页面提取到足够的正文，请换链接或改用「粘贴正文」方式。",
                },
            )
            return

        plain = plain[: settings.URL_EXTRACT_MAX_CHARS]

        yield sse_event({"event": "status", "stage": "synopsis", "message": "正在提炼政策要点…"})
        try:
            synopsis = await extract_synopsis_from_web_plain(plain, final_url)
        except json.JSONDecodeError:
            yield sse_event({"event": "error", "detail": "提炼要点时模型返回格式异常，请重试或换链接。"})
            return
        except AuthenticationError:
            yield sse_event(
                {
                    "event": "error",
                    "detail": (
                        "大模型 API 密钥无效。请检查 DASHSCOPE_API_KEY / OPENAI_API_KEY，"
                        "提炼要点与白话解读均需有效密钥。"
                    ),
                },
            )
            return
        except APIError as e:
            yield sse_event({"event": "error", "detail": str(e) or "提炼要点时大模型接口失败"})
            return

        synopsis = synopsis.strip()
        if len(synopsis) < 40:
            yield sse_event(
                {
                    "event": "error",
                    "detail": "提炼结果过短，该页面可能不是政策/办事类内容，请换链接或粘贴正文。",
                },
            )
            return

        synopsis_for_llm = synopsis[: settings.POLICY_TEXT_MAX_CHARS]
        excerpt = plain[:6000]
        persist = (
            f"【来源网址】{final_url}\n\n【提炼后的政策要点】\n{synopsis_for_llm}\n\n【网页正文摘录】\n{excerpt}"
        )

        yield sse_event({"event": "status", "stage": "explain", "message": "正在生成白话解读…"})
        async for chunk in _stream_explain_and_save(
            synopsis_for_llm,
            topic,
            session,
            current,
            persist,
        ):
            yield chunk

    return StreamingResponse(
        from_url_stream(),
        media_type="text/event-stream; charset=utf-8",
        headers=_sse_headers(),
    )


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
