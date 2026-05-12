from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    text: str
    topic: str | None = Field(default="general")


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
