from datetime import timedelta
from urllib.parse import quote_plus
import os

from pydantic import Field
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

    # 若设置非空，则优先作为 SQLAlchemy 异步连接串（须含驱动，如 postgresql+asyncpg://...）
    DATABASE_URL: str = Field(default="", validation_alias="DATABASE_URL")

    DB_HOST: str = Field(default="127.0.0.1", validation_alias="DB_HOST")
    DB_PORT: int = Field(default=5432, validation_alias="DB_PORT")
    DB_USER: str = Field(default="postgres", validation_alias="DB_USER")
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

    POLICY_TEXT_MAX_CHARS: int = Field(default=12000, validation_alias="POLICY_TEXT_MAX_CHARS")
    LLM_TIMEOUT_SECONDS: float = Field(default=120.0, validation_alias="LLM_TIMEOUT_SECONDS")

    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    OPENAI_BASE_URL: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

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
