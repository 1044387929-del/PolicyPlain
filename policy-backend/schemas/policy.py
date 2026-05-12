from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserPublic(BaseModel):
    id: str
    email: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("两次输入的密码不一致")
        return self


class SendRegisterCodeRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0
    user: UserPublic


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
