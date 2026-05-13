from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator


class ExplainRequest(BaseModel):
    """粘贴正文、网页链接可单独或同时使用；截图 OCR 由前端填入 text。"""

    text: str = Field(default="", description="粘贴的政策正文（可与 url 同时使用）")
    url: str | None = Field(default=None, description="可选的政府公开政策页链接")
    topic: str | None = Field(default="general")

    @model_validator(mode="after")
    def at_least_text_or_url(self) -> Self:
        if not self.text.strip() and not (self.url or "").strip():
            raise ValueError("请填写政策正文，或填写政策网页链接，至少填写一项")
        return self


class ExplainFromUrlRequest(BaseModel):
    url: str
    topic: str | None = Field(default="general")


class PolicyOcrImageResponse(BaseModel):
    """上传政策类截图，经 PaddleOCR 识别后的纯文本（供用户粘贴区继续编辑）。"""

    text: str = Field(default="", description="识别出的正文，多段以空行拼接")


class ExplainResultFields(BaseModel):
    summary_one_line: str = ""
    applicability: list[str] = Field(default_factory=list)
    materials: dict[str, Any] = Field(default_factory=dict)
    channels: list[str] = Field(default_factory=list)
    important_dates: list[str] = Field(default_factory=list)
    common_misunderstandings: list[str] = Field(default_factory=list)
    uncovered_points: list[str] = Field(default_factory=list)
    verification_hints: list[str] = Field(default_factory=list)
    model: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ExplainResponse(ExplainResultFields):
    record_id: str


class ExplanationListItem(BaseModel):
    record_id: str
    topic: str
    created_at: datetime
    summary_one_line: str | None = None


class ExplanationListResponse(BaseModel):
    items: list[ExplanationListItem]
    total: int


class ExplanationDetailResponse(BaseModel):
    record_id: str
    topic: str
    created_at: datetime
    input_text: str | None
    result: ExplainResultFields
