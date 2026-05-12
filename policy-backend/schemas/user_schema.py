from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from schemas.response_schema import ResponseSchema


class UserLoginSchema(BaseModel):
    email: EmailStr = Field(..., description="邮箱账号")
    password: str = Field(..., description="密码", min_length=1, max_length=128)


class UserSchema(BaseModel):
    id: str = Field(..., description="用户ID")
    email: EmailStr = Field(..., description="邮箱")

    model_config = ConfigDict(from_attributes=True)


class UserLoginRespSchema(BaseModel):
    access_token: str = Field(..., description="access_token")
    refresh_token: str = Field(..., description="refresh_token")
    user: UserSchema = Field(..., description="用户信息")


class UserRegisterSendCodeSchema(BaseModel):
    """发送注册验证码（对齐 hr 的 UserInviteSchema 仅保留邮箱语义）。"""

    email: EmailStr = Field(..., description="邮箱，用于接收注册验证码")


class UserRegisterSendCodeRespSchema(ResponseSchema):
    expires_in: int = Field(..., description="验证码有效期（秒）")
    resend_after: int = Field(..., description="可再次发送间隔（秒）")


class UserRegisterSchema(BaseModel):
    """注册（对齐 hr-backend UserRegisterSchema：含 invite_code 验证码字段）。"""

    email: EmailStr = Field(..., description="邮箱")
    invite_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="邮箱验证码（6位）",
    )
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    password_confirm: str = Field(..., min_length=8, max_length=128, description="确认密码")

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegisterSchema":
        if self.password != self.password_confirm:
            raise ValueError("两次输入的密码不一致")
        return self
