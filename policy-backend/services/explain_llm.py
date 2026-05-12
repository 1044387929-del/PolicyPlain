import json
import uuid
from typing import Any

import httpx
from openai import AsyncOpenAI

from schemas.policy import ExplainResultFields
from settings import settings


SYSTEM_PROMPT = """你是面向老年人阅读的「社保 / 医保 / 养老保险」政策辅助解读助手（非官方）。
规则：
1. 只根据用户给出的政策原文回答，不得编造未在原文出现的电话号码、日期、金额、地区政策版本。
2. 输出必须是单个 JSON 对象，且只包含以下键（不要多余键）：
summary_one_line, applicability, materials, channels, important_dates,
common_misunderstandings, uncovered_points, verification_hints, warnings
3. applicability/channels/important_dates/common_misunderstandings/uncovered_points/verification_hints 均为字符串数组；没有则 []。
4. materials 为对象：{"items": string[], "source_note": string}；原文未列材料时 items 可为 []，source_note 说明。
5. 若原文未写清某类信息，在对应数组中用短句说明「原文未提及」，不要编造。
6. 用语短句、通俗。"""


def _mock_result(text: str, topic: str) -> dict[str, Any]:
    snippet = (text[:120] + "…") if len(text) > 120 else text
    return {
        "summary_one_line": f"（演示模式）已收到约 {len(text)} 字、主题 {topic} 的政策片段，请配置 DASHSCOPE_API_KEY 或 OPENAI_API_KEY 后获得真实解读。",
        "applicability": ["演示数据：原文需自行判断是否与您个人情况相关。"],
        "materials": {
            "items": [],
            "source_note": "演示模式未解析原文材料清单。",
        },
        "channels": ["原文未提及（演示）"],
        "important_dates": ["原文未提及明确截止时间（演示）"],
        "common_misunderstandings": ["不要把演示结果当作真实办事依据。"],
        "uncovered_points": ["演示模式未覆盖您可能关心的全部问题。"],
        "verification_hints": ["请咨询当地社保/医保经办窗口或拨打官方公开热线（以政府网站为准）。"],
        "warnings": [f"原文片段预览：{snippet}"],
        "model": "mock",
    }


async def generate_structured_explain(text: str, topic: str) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY.strip():
        return _mock_result(text, topic)

    base = (settings.OPENAI_BASE_URL or "").strip() or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=base,
        timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS),
    )
    user_msg = f"主题标签：{topic}\n\n政策原文：\n{text}"
    completion = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content or "{}"
    data = json.loads(raw)
    data["model"] = completion.model
    return data


def normalize_to_schema(data: dict[str, Any]) -> ExplainResultFields:
    def arr(key: str) -> list[str]:
        v = data.get(key)
        if isinstance(v, list):
            return [str(x) for x in v]
        return []

    materials = data.get("materials")
    if not isinstance(materials, dict):
        materials = {"items": [], "source_note": "原文未列材料清单或模型未返回结构化 materials。"}

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
