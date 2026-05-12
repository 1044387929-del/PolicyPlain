from typing import Literal

from pydantic import BaseModel, Field


class ResponseSchema(BaseModel):
    """标准 API 响应模型（与 hr-backend/schemas/__init__.py 一致）。"""

    result: Literal["success", "fail"] = Field(default="success", description="响应消息")
