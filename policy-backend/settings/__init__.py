from datetime import timedelta
from typing import Any
from urllib.parse import quote_plus
import os

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_SETTINGS_DIR)


def _env_file_tuple() -> tuple[str, ...]:
    """先加载 settings/setting.env，再加载项目根目录 .env（后者覆盖前者）。"""
    paths = [
        os.path.join(_SETTINGS_DIR, "setting.env"),
        os.path.join(_ROOT_DIR, ".env"),
    ]
    return tuple(p for p in paths if os.path.isfile(p))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file_tuple() or None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="before")
    @classmethod
    def _strip_env_string_quotes(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for k, v in list(data.items()):
            if isinstance(v, str):
                data[k] = v.strip().strip('"').strip("'")
        return data

    # 若设置非空，则优先作为 SQLAlchemy 异步连接串（须含驱动，如 postgresql+asyncpg://...）
    DATABASE_URL: str = Field(default="", validation_alias="DATABASE_URL")

    DB_HOST: str = Field(default="127.0.0.1", validation_alias="DB_HOST")
    DB_PORT: int = Field(default=5432, validation_alias="DB_PORT")
    DB_USER: str = Field(
        default="postgres",
        validation_alias=AliasChoices("DB_USER", "DB_USERNAME"),
    )
    DB_PASSWORD: str = Field(default="postgres", validation_alias="DB_PASSWORD")
    DB_NAME: str = Field(default="policy_plain", validation_alias="DB_NAME")

    JWT_SECRET_KEY: str = Field(
        default="dev-only-change-me-please-use-long-random-string",
        validation_alias="JWT_SECRET_KEY",
    )
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = Field(
        default=timedelta(hours=8),
        validation_alias="JWT_ACCESS_TOKEN_EXPIRES",
    )
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = Field(
        default=timedelta(days=7),
        validation_alias="JWT_REFRESH_TOKEN_EXPIRES",
    )

    CORS_ORIGINS: str = Field(default="*", validation_alias="CORS_ORIGINS")

    # Redis（与 hr-backend 一致；供 PolicyCache）
    REDIS_HOST: str = Field(default="127.0.0.1", validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, validation_alias="REDIS_PORT")

    POLICY_TEXT_MAX_CHARS: int = Field(default=12000, validation_alias="POLICY_TEXT_MAX_CHARS")
    LLM_TIMEOUT_SECONDS: float = Field(default=120.0, validation_alias="LLM_TIMEOUT_SECONDS")

    URL_FETCH_TIMEOUT_SECONDS: float = Field(default=30.0, validation_alias="URL_FETCH_TIMEOUT_SECONDS")
    URL_FETCH_MAX_BYTES: int = Field(default=2_000_000, ge=10_000, le=10_000_000, validation_alias="URL_FETCH_MAX_BYTES")
    URL_FETCH_MAX_REDIRECTS: int = Field(default=5, ge=0, le=15, validation_alias="URL_FETCH_MAX_REDIRECTS")
    URL_EXTRACT_MAX_CHARS: int = Field(default=18_000, ge=2000, le=100_000, validation_alias="URL_EXTRACT_MAX_CHARS")

    # 百炼与 OpenAI 兼容接口分字段读取：优先 DASHSCOPE_API_KEY，避免系统/空 OPENAI_API_KEY 覆盖百炼密钥
    DASHSCOPE_API_KEY: str = Field(default="", validation_alias="DASHSCOPE_API_KEY")
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    OPENAI_BASE_URL: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    OPENAI_MODEL: str = Field(default="qwen3-max", validation_alias="OPENAI_MODEL")

    # 邮件（字段命名对齐 hr-backend/settings：MAIL_SERVER / MAIL_PORT / MAIL_STARTTLS / MAIL_SSL_TLS）
    MAIL_SERVER: str = Field(
        default="smtp.qq.com",
        validation_alias=AliasChoices("MAIL_SERVER", "MAIL_SMTP_HOST"),
    )
    MAIL_PORT: int = Field(
        default=465,
        validation_alias=AliasChoices("MAIL_PORT", "MAIL_SMTP_PORT"),
    )
    MAIL_STARTTLS: bool = Field(default=False, validation_alias="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = Field(default=True, validation_alias="MAIL_SSL_TLS")
    MAIL_FROM_NAME: str = Field(default="PolicyPlain", validation_alias="MAIL_FROM_NAME")
    MAIL_SMTP_TIMEOUT: float = Field(default=30.0, validation_alias=AliasChoices("MAIL_SMTP_TIMEOUT", "MAIL_TIMEOUT"))
    MAIL_USERNAME: str = Field(default="", validation_alias="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(default="", validation_alias="MAIL_PASSWORD")
    MAIL_FROM: str = Field(default="", validation_alias="MAIL_FROM")

    REGISTER_CODE_TTL_SECONDS: int = Field(default=600, ge=60, le=3600, validation_alias="REGISTER_CODE_TTL_SECONDS")
    REGISTER_CODE_RESEND_SECONDS: int = Field(
        default=60, ge=15, le=600, validation_alias="REGISTER_CODE_RESEND_SECONDS"
    )

    @property
    def llm_api_key(self) -> str:
        """调用兼容 OpenAI 接口时使用的密钥：显式百炼密钥优先，其次 OPENAI_API_KEY。"""
        d = self.DASHSCOPE_API_KEY.strip()
        if d:
            return d
        return self.OPENAI_API_KEY.strip()

    @property
    def mail_configured(self) -> bool:
        return bool(self.MAIL_USERNAME.strip() and self.MAIL_PASSWORD.strip())

    @property
    def resolved_database_url(self) -> str:
        if self.DATABASE_URL.strip():
            return self.DATABASE_URL.strip()
        u = quote_plus(self.DB_USER)
        p = quote_plus(self.DB_PASSWORD)
        return f"postgresql+asyncpg://{u}:{p}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if raw == "*":
            return ["*"]
        return [p.strip() for p in raw.split(",") if p.strip()]


settings = Settings()
