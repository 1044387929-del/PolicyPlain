import json
import logging
import os
import tempfile
import uuid
from collections.abc import AsyncIterator

import httpx
import json_repair
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from openai import APIError, AuthenticationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_session_instance
from core.ocr import PaddleOcr
from models.user import PolicyExplanationModel, PolicyFollowupModel, UserModel
from repository.policy_repo import PolicyRepo
from schemas.policy import (
    ExplainFromUrlRequest,
    ExplainRequest,
    ExplainResponse,
    ExplanationDetailResponse,
    ExplanationListItem,
    ExplanationListResponse,
    ExplainResultFields,
    FollowUpItem,
    FollowUpRequest,
    PolicyOcrImageResponse,
)
from services.explain_llm import (
    extract_synopsis_from_web_plain,
    llm_followup_token_stream,
    llm_token_stream,
    normalize_to_schema,
    sse_event,
)
from services.streaming_partial import try_normalize_streaming_explain
from services.url_fetch import assert_public_http_url, fetch_html, html_to_plain_text
from settings import settings

router = APIRouter(prefix="/policy", tags=["policy"])

logger = logging.getLogger(__name__)

ALLOWED_TOPICS = frozenset({"general", "medical_insurance", "pension"})
OCR_ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
OCR_MAX_BYTES = 8 * 1024 * 1024
MAX_FOLLOWUP_ROUNDS = 3


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
    last_partial_sig: str | None = None
    tick = 0
    try:
        async for piece in llm_token_stream(text_for_llm, topic):
            acc += piece
            tick += 1
            if tick % 2 == 0 or len(piece) > 100:
                partial = try_normalize_streaming_explain(acc)
                if partial:
                    sig = json.dumps(partial, ensure_ascii=False, sort_keys=True)
                    if sig != last_partial_sig:
                        last_partial_sig = sig
                        yield sse_event({"event": "partial", "data": partial})
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
        try:
            raw = json_repair.loads(acc)
        except Exception:
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


async def _stream_mixed_explain(
    pasted: str,
    url_part: str | None,
    topic: str,
    session: AsyncSession,
    current: UserModel,
) -> AsyncIterator[str]:
    """粘贴正文、可选网址合并后走同一套 LLM 流式解读。"""
    pasted_st = pasted.strip()
    url_st = (url_part or "").strip()
    if not pasted_st and not url_st:
        yield sse_event({"event": "error", "detail": "请填写政策正文，或填写政策网页链接，至少填写一项"})
        return

    text_for_llm = ""
    persist = ""

    if url_st:
        try:
            safe_url = assert_public_http_url(url_st)
        except HTTPException as e:
            d = e.detail if isinstance(e.detail, str) else "网址无效"
            yield sse_event({"event": "error", "detail": d})
            return

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
                    "detail": "未能从页面提取到足够的正文，请换链接或补充粘贴正文。",
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
                    "detail": "提炼结果过短，该页面可能不是政策/办事类内容，请换链接或补充粘贴正文。",
                },
            )
            return

        synopsis_for_llm = synopsis[: settings.POLICY_TEXT_MAX_CHARS]
        excerpt = plain[:6000]
        base_persist = (
            f"【来源网址】{final_url}\n\n【提炼后的政策要点】\n{synopsis_for_llm}\n\n【网页正文摘录】\n{excerpt}"
        )

        if pasted_st:
            glue = "\n\n---\n【以下为与网页相关的补充材料（用户粘贴）】\n"
            text_for_llm = (synopsis_for_llm + glue + pasted_st)[: settings.POLICY_TEXT_MAX_CHARS]
            persist = (base_persist + f"\n\n【用户补充粘贴的正文】\n{pasted_st}")[:80000]
        else:
            text_for_llm = synopsis_for_llm
            persist = base_persist[:80000]
    else:
        if len(pasted_st) > settings.POLICY_TEXT_MAX_CHARS:
            yield sse_event({"event": "error", "detail": "文本过长"})
            return
        text_for_llm = pasted_st
        persist = pasted_st

    yield sse_event({"event": "status", "stage": "explain", "message": "正在生成白话解读…"})
    async for chunk in _stream_explain_and_save(text_for_llm, topic, session, current, persist):
        yield chunk


def _sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


async def _stream_follow_up_answer(
    record_id: str,
    question: str,
    session: AsyncSession,
    current: UserModel,
) -> AsyncIterator[str]:
    async with session.begin():
        repo = PolicyRepo(session)
        row = await repo.get_by_id_for_user(record_id, current.id)
        if not row:
            yield sse_event({"event": "error", "detail": "记录不存在"})
            return
        n = await repo.count_followups(record_id)
        if n >= MAX_FOLLOWUP_ROUNDS:
            yield sse_event({"event": "error", "detail": "本条解读的追问已达上限（最多 3 轮）"})
            return
        input_text = row.input_text or ""
        topic = row.topic
        result_snapshot = json.dumps(row.result_json, ensure_ascii=False)
        prior_rows = await repo.list_followups_for_explanation(record_id)
        prior_pairs = [(p.question, p.answer) for p in prior_rows]

    acc = ""
    try:
        async for piece in llm_followup_token_stream(input_text, result_snapshot, topic, prior_pairs, question):
            acc += piece
            if piece:
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

    answer = acc.strip()
    if not answer:
        yield sse_event({"event": "error", "detail": "模型未返回有效内容，请重试"})
        return

    fid = str(uuid.uuid4())
    try:
        async with session.begin():
            repo = PolicyRepo(session)
            n2 = await repo.count_followups(record_id)
            if n2 >= MAX_FOLLOWUP_ROUNDS:
                yield sse_event({"event": "error", "detail": "追问已达上限，请刷新后查看已保存的问答"})
                return
            turn = n2 + 1
            await repo.create_followup(
                PolicyFollowupModel(
                    id=fid,
                    explanation_id=record_id,
                    turn_index=turn,
                    question=question.strip(),
                    answer=answer,
                )
            )
    except Exception:
        logger.exception("保存追问失败")
        yield sse_event({"event": "error", "detail": "保存追问失败，请重试"})
        return

    yield sse_event({"event": "done", "answer": answer, "turn": turn, "followup_id": fid})


@router.post("/explain")
async def explain(
    body: ExplainRequest,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    """流式解读：SSE。支持仅粘贴、仅网址、或正文+网址混合（截图 OCR 由前端填入正文）。"""
    topic = body.topic or "general"
    if topic not in ALLOWED_TOPICS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="无效的主题标签")

    return StreamingResponse(
        _stream_mixed_explain(body.text, body.url, topic, session, current),
        media_type="text/event-stream; charset=utf-8",
        headers=_sse_headers(),
    )


@router.post("/explain-from-url")
async def explain_from_url(
    body: ExplainFromUrlRequest,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    """兼容旧客户端：仅从网址解读，等价于 POST /explain 且 text 为空。"""
    topic = body.topic or "general"
    if topic not in ALLOWED_TOPICS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="无效的主题标签")

    return StreamingResponse(
        _stream_mixed_explain("", body.url, topic, session, current),
        media_type="text/event-stream; charset=utf-8",
        headers=_sse_headers(),
    )


@router.post("/ocr-image", response_model=PolicyOcrImageResponse)
async def ocr_policy_screenshot(
    file: UploadFile = File(...),
    current: UserModel = Depends(get_current_user),
):
    """上传政策类截图，调用与 hr-backend 相同的 PaddleOCR 云端配置识别文字，填入前端正文框。"""
    _ = current
    if not settings.paddle_ocr_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置 Paddle OCR：请设置环境变量 PADDLE_OCR_ACCESS_TOKEN（与 hr-backend 一致，见 .env.example）",
        )
    ct = (file.content_type or "").split(";")[0].strip().lower()
    if ct not in OCR_ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="仅支持 JPG、PNG、WebP 图片")

    if ct == "image/jpeg":
        suffix = ".jpg"
    elif ct == "image/png":
        suffix = ".png"
    else:
        suffix = ".webp"

    raw = await file.read(OCR_MAX_BYTES + 1)
    if len(raw) > OCR_MAX_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="图片过大（单张上限 8MB）")

    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    text = ""
    try:
        with open(path, "wb") as fp:
            fp.write(raw)
        paddle = PaddleOcr()
        text = await paddle.extract_text_from_file(path)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e
    except Exception as e:
        logger.exception("PaddleOCR 识别异常")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=f"识别失败：{e!s}") from e
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    return PolicyOcrImageResponse(text=text)


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
        follow_rows: list[PolicyFollowupModel] = []
        if row:
            follow_rows = await repo.list_followups_for_explanation(record_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="记录不存在")

    result = ExplainResultFields.model_validate(row.result_json)
    followups = [
        FollowUpItem(
            id=f.id,
            turn_index=f.turn_index,
            question=f.question,
            answer=f.answer,
            created_at=f.created_at,
        )
        for f in follow_rows
    ]
    return ExplanationDetailResponse(
        record_id=row.id,
        topic=row.topic,
        created_at=row.created_at,
        input_text=row.input_text,
        result=result,
        followups=followups,
    )


@router.post("/explanations/{record_id}/follow-up")
async def follow_up_explanation(
    record_id: str,
    body: FollowUpRequest,
    session: AsyncSession = Depends(get_session_instance),
    current: UserModel = Depends(get_current_user),
):
    """对已有解读追问，SSE 流式返回纯文本；同一记录最多 3 轮。"""
    q = body.question.strip()
    if not q:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="问题不能为空")

    return StreamingResponse(
        _stream_follow_up_answer(record_id, q, session, current),
        media_type="text/event-stream; charset=utf-8",
        headers=_sse_headers(),
    )
