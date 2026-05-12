import logging

from aiosmtplib import SMTPResponseException
from fastapi_mail import FastMail, MessageSchema

from core.mail import create_mail_instance
from settings import settings

logger = logging.getLogger(__name__)


async def send_email_task(message: MessageSchema) -> None:
    """发送邮件（与 hr-backend/tasks/__init__.py 中 send_email_task 同思路）。"""
    mail: FastMail = create_mail_instance()
    try:
        await mail.send_message(message)
    except SMTPResponseException as e:
        if e.code == -1 and b"\\x00\\x00\\x00" in str(e).encode():
            logger.info("忽略 QQ 邮箱 SMTP 关闭阶段的非标准响应（邮件可能已成功发送）")
        else:
            logger.error("邮件发送失败: %s", e)
            raise
    except Exception:
        logger.exception("邮件发送失败")
        raise


async def send_register_code_email_task(email: str, invite_code: str) -> None:
    """发送注册验证码邮件（命名与 hr 的 send_invite_email_task 对齐，参数 invite_code）。"""
    minutes = max(1, settings.REGISTER_CODE_TTL_SECONDS // 60)
    message = MessageSchema(
        subject="【PolicyPlain】注册验证码",
        recipients=[email],
        body=f"您好，您的邮箱是：{email}，验证码是：{invite_code}，{minutes} 分钟内有效。",
        subtype="plain",
    )
    await send_email_task(message)
