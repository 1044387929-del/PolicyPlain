# core/mail.py（与 hr-backend/core/mail.py 同结构：FastMail + ConnectionConfig）
from fastapi_mail import ConnectionConfig, FastMail
from pydantic import SecretStr

from settings import settings


def create_mail_instance() -> FastMail:
    """创建 FastMail 实例（每次调用返回新实例，线程/协程安全）。"""
    mail_from = (settings.MAIL_FROM or settings.MAIL_USERNAME).strip()
    mail_config = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME.strip(),
        MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD.strip() or ""),
        MAIL_FROM=mail_from,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    return FastMail(mail_config)
