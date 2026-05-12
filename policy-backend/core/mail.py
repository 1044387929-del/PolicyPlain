"""SMTP 发送（QQ 邮箱等）；同步实现，由路由里 asyncio.to_thread 调用。"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from settings import settings

logger = logging.getLogger(__name__)


def _send_plain_sync(to_email: str, subject: str, body: str) -> None:
    from_addr = (settings.MAIL_FROM or settings.MAIL_USERNAME).strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP_SSL(
        settings.MAIL_SMTP_HOST,
        settings.MAIL_SMTP_PORT,
        timeout=settings.MAIL_SMTP_TIMEOUT,
    ) as smtp:
        smtp.login(settings.MAIL_USERNAME.strip(), settings.MAIL_PASSWORD.strip())
        smtp.send_message(msg)


async def send_register_verification_email(to_email: str, code: str) -> None:
    minutes = max(1, settings.REGISTER_CODE_TTL_SECONDS // 60)
    body = (
        f"您的 PolicyPlain 注册验证码为：{code}\n\n"
        f"验证码 {minutes} 分钟内有效，请勿泄露给他人。\n"
        "如非本人操作，请忽略本邮件。"
    )
    await asyncio.to_thread(
        _send_plain_sync,
        to_email,
        "PolicyPlain 注册验证码",
        body,
    )
