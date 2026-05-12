import time

from pydantic import BaseModel, EmailStr, Field


class RegisterInfoSchema(BaseModel):
    """注册验证码缓存（对齐 hr-backend InviteInfoSchema：邮箱 + invite_code + 元数据）。"""

    email: EmailStr
    invite_code: str
    sent_epoch: float = Field(default_factory=time.time)
