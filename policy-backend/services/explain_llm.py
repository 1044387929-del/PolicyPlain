import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import HTTPException, status
from openai import APIError, AsyncOpenAI, AuthenticationError

from schemas.policy import ExplainResultFields
from settings import settings


SYSTEM_PROMPT = """你是给「大爷大妈」和家属看的政策白话讲解员（非官方），像在社区窗口面对面聊天那样说话。

【语气与用词】
- 一律用日常口语、短句；不要用公文腔，不要用「据此」「前述」「综上所述」这类词。
- 碰到「参保地、统筹、待遇资格」等词，后面用括号或紧跟一句大白话解释清楚。
- 每条内容都要是**完整的一句话或一小段话**，像跟老人慢慢说清楚，不要只写几个干巴巴的关键词。
- summary_one_line：控制在 40 字以内，像您亲口告诉老人「这事儿到底啥意思」的一句话。

【内容要求】
1. 只根据用户给出的政策原文回答，不得编造原文没有的电话、日期、金额、具体地区版本。
2. 输出必须是单个 JSON 对象，且只包含以下键（不要多余键）：
summary_one_line, applicability, materials, channels, important_dates,
common_misunderstandings, uncovered_points, verification_hints, warnings
3. applicability / channels / important_dates / common_misunderstandings / uncovered_points / verification_hints：字符串数组；每一项都是**读得顺口的整句**；没有信息时写一句「原文里没写清楚，您要到窗口问一声」之类，不要编造。
4. materials 为对象：{"items": string[], "source_note": string}。items 里每条用口语写要带啥；source_note 用两三句大白话交代材料从哪来、没写清怎么说。
5. warnings：用温和口吻提醒「以当地经办为准」等，同样用口语短句数组。

【禁止】
- 不要用编号列表式的极简短语凑数；不要堆专业术语不解释。"""


SYNOPSIS_SYSTEM = """你是政策和办事网页的摘录员。用户发来的是从网页抓到的纯文本（可能含导航、页脚等噪音）。
任务：整理成一篇连贯的中文「政策要点」摘要，供后续给老年人做白话解读使用。
规则：
1. 只依据输入文本，不编造文中没有的电话、金额、日期、机构名、地区版本。
2. 输出必须是单个 JSON 对象，且只包含一个键 synopsis（字符串）。
3. synopsis 用完整句子写清：适用对象、待遇或条件、材料、办理渠道与时间等（文中有则写，无则明确说文中未写清），避免公文腔。
4. synopsis 建议 500～3500 字；若网页与社保/医保/养老等政策无关，在 synopsis 中如实说明并摘录可见的事实性信息。"""


async def extract_synopsis_from_web_plain(plain: str, page_url: str) -> str:
    trimmed = plain.strip()
    if not trimmed:
        return ""
    cap = settings.URL_EXTRACT_MAX_CHARS
    body = trimmed[:cap]
    if not settings.llm_api_key:
        return (
            body[:4000]
            + "\n\n（演示：未配置大模型密钥，以上为网页正文截断，未做 AI 提炼。配置后可自动生成要点摘要。）"
        )

    base = (settings.OPENAI_BASE_URL or "").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=base,
        timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS),
    )
    user_msg = f"页面链接（仅供参考）：{page_url}\n\n以下为抓取的正文：\n{body}"
    completion = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYNOPSIS_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)
    return str(data.get("synopsis") or "").strip()


def _mock_result(text: str, topic: str) -> dict[str, Any]:
    snippet = (text[:120] + "…") if len(text) > 120 else text
    return {
        "summary_one_line": f"（演示）您贴了大约 {len(text)} 字，主题是「{topic}」。接上真实密钥后，会像聊天一样给您逐句说明。",
        "applicability": [
            "演示里没法判断跟您家有没有关系，您对照自己情况想想，拿不准就问社区或经办窗口。"
        ],
        "materials": {
            "items": [],
            "source_note": "演示模式没读您的原件，所以说不清具体要带啥；接上密钥后会按原文用大白话列出来。",
        },
        "channels": ["原文里办事去哪儿，演示里没写，您以纸质通知或政府网站为准。"],
        "important_dates": ["截止时间演示里看不出来，您留意通知上有没有写「截至某月某日」。"],
        "common_misunderstandings": ["别把演示当正式答复，真办事以前台工作人员说的为准。"],
        "uncovered_points": ["您心里还惦记别的事，可以换几句原文再解读一遍，或直接问窗口。"],
        "verification_hints": [
            "心里不踏实，就带上身份证去一趟社保或医保窗口，把通知给工作人员看一眼，最稳妥。"
        ],
        "warnings": [f"您贴的内容开头是这样的（演示）：{snippet}"],
        "model": "mock",
    }


def sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def llm_token_stream(text: str, topic: str) -> AsyncIterator[str]:
    """按 token/片段产出模型原始文本（整段为单个 JSON 对象）。无密钥时为演示分片。"""
    if not settings.llm_api_key:
        payload = json.dumps(_mock_result(text, topic), ensure_ascii=False)
        step = max(24, len(payload) // 24)
        for i in range(0, len(payload), step):
            yield payload[i : i + step]
            await asyncio.sleep(0)
        return

    base = (settings.OPENAI_BASE_URL or "").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=base,
        timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS),
    )
    user_msg = (
        f"主题标签：{topic}\n\n"
        "读者主要是老年朋友或其家人。请按系统提示的口吻写，让人一眼看得懂、读得顺。\n\n"
        f"政策原文：\n{text}"
    )
    stream = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


async def generate_structured_explain(text: str, topic: str) -> dict[str, Any]:
    """非流式：聚合 llm_token_stream 后解析（供脚本或单测复用）。"""
    acc = ""
    try:
        async for piece in llm_token_stream(text, topic):
            acc += piece
        data = json.loads(acc)
        data.setdefault("model", settings.OPENAI_MODEL)
        return data
    except AuthenticationError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=(
                "大模型 API 密钥无效（百炼返回 401）。请核对："
                "1）在阿里云百炼/模型服务控制台创建的是「API-KEY」且未过期；"
                "2）环境变量优先使用 DASHSCOPE_API_KEY，并删除或改正本机/根目录 .env 里错误的 OPENAI_API_KEY；"
                "3）密钥前后不要有空格或多余引号。"
            ),
        ) from None
    except APIError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(e) or "大模型接口错误") from None


def normalize_to_schema(data: dict[str, Any]) -> ExplainResultFields:
    def arr(key: str) -> list[str]:
        v = data.get(key)
        if isinstance(v, list):
            return [str(x) for x in v]
        return []

    materials = data.get("materials")
    if not isinstance(materials, dict):
        materials = {"items": [], "source_note": "原文里材料写得散，您带好身份证，到窗口让工作人员帮您对一下最稳。"}

    return ExplainResultFields(
        summary_one_line=str(data.get("summary_one_line") or ""),
        applicability=arr("applicability"),
        materials=materials,
        channels=arr("channels"),
        important_dates=arr("important_dates"),
        common_misunderstandings=arr("common_misunderstandings"),
        uncovered_points=arr("uncovered_points"),
        verification_hints=arr("verification_hints"),
        model=data.get("model"),
        warnings=arr("warnings"),
    )


FOLLOWUP_SYSTEM = """你是面向老年人与家属的政策白话讲解员（非官方）。
用户已经阅读过针对一段政策材料的「结构化白话解读」，现在要在此基础上追问。

规则：
1. 只根据【政策原文或来源摘录】与【已给出的解读内容】以及此前的追问与回答作答；不要编造其中都没有的电话、金额、日期和地区版本。
2. 用日常口语、短句，直接回应用户的具体问题；不要用公文腔。
3. 若材料里确实没有相关信息，清楚说明「原文和现有材料里没写到」，并温和提醒以当地经办部门解释为准。
4. 直接输出自然段落的纯文本，不要使用 JSON、不要用 Markdown 标题符号堆砌。"""


async def llm_followup_token_stream(
    input_text: str,
    result_json_text: str,
    topic: str,
    prior_qa: list[tuple[str, str]],
    question: str,
) -> AsyncIterator[str]:
    """追问：流式产出纯文本片段（非 JSON）。"""
    if not settings.llm_api_key:
        mock = (
            f"（演示）您在「{topic}」主题下提问：{question[:120]}"
            + ("…" if len(question) > 120 else "")
            + " 接入真实大模型密钥后，这里会结合您保存的原文和解读具体分析。"
        )
        step = max(20, len(mock) // 8)
        for i in range(0, len(mock), step):
            yield mock[i : i + step]
            await asyncio.sleep(0)
        return

    base = (settings.OPENAI_BASE_URL or "").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=base,
        timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS),
    )
    prior_block = ""
    for i, (pq, pa) in enumerate(prior_qa, start=1):
        prior_block += f"\n【第{i}轮追问】{pq}\n【回答】{pa}\n"

    body_in = (input_text or "").strip()
    body_in = body_in[:50000]
    body_res = (result_json_text or "").strip()[:80000]

    user_msg = (
        f"主题标签：{topic}\n\n"
        "【政策原文或来源摘录】\n"
        f"{body_in}\n\n"
        "【结构化白话解读（JSON）】\n"
        f"{body_res}\n"
        f"{prior_block}\n"
        "【用户本轮追问】\n"
        f"{question.strip()}\n\n"
        "请直接给出口语化回答，不要用 JSON 包裹，不要重复打印整段原文。"
    )
    stream = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": FOLLOWUP_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        stream=True,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
