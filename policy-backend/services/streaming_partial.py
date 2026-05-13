"""流式过程中尝试把不完整 JSON 修成可校验对象，供 SSE partial 事件使用。"""

from typing import Any

import json_repair
from pydantic import ValidationError

from services.explain_llm import normalize_to_schema


def try_normalize_streaming_explain(acc: str) -> dict[str, Any] | None:
    s = acc.strip()
    if len(s) < 12 or not s.startswith("{"):
        return None
    try:
        obj = json_repair.loads(s)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    try:
        return normalize_to_schema(obj).model_dump()
    except ValidationError:
        return None
