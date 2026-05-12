import logging
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.mail import send_register_verification_email
from core.register_code import register_code_hmac_hex, verify_register_code
from models import auth_handler, get_session
from models.register_email_code import RegisterEmailCodeModel
from models.user import UserModel
from repository.register_code_repo import RegisterCodeRepo
from repository.user_repo import UserRepo
from schemas.policy import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    SendRegisterCodeRequest,
    UserPublic,
)
from settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/send-code")
async def send_register_code(
    body: SendRegisterCodeRequest,
    session: AsyncSession = Depends(get_session),
):
    if not settings.mail_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="邮件服务未配置：请在环境变量中填写 MAIL_USERNAME 与 MAIL_PASSWORD",
        )
    email = str(body.email).lower()
    code = f"{secrets.randbelow(1_000_000):06d}"
    code_hash = register_code_hmac_hex(email, code)
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=settings.REGISTER_CODE_TTL_SECONDS)

    async with session.begin():
        user_repo = UserRepo(session)
        if await user_repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该邮箱已被注册",
            )
        code_repo = RegisterCodeRepo(session)
        row = await code_repo.get_by_email(email)
        if row is not None:
            elapsed = (now - row.created_at).total_seconds()
            if elapsed < settings.REGISTER_CODE_RESEND_SECONDS:
                wait = int(settings.REGISTER_CODE_RESEND_SECONDS - elapsed)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"发送过于频繁，请 {wait} 秒后再试",
                )
        await code_repo.replace(
            RegisterEmailCodeModel(
                id=str(uuid.uuid4()),
                email=email,
                code_hash=code_hash,
                expires_at=expires_at,
                created_at=now,
            )
        )

    try:
        await send_register_verification_email(email, code)
    except Exception:
        logger.exception("发送注册验证码邮件失败: %s", email)
        async with session.begin():
            await RegisterCodeRepo(session).delete_by_email(email)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="邮件发送失败，请检查 SMTP 配置或稍后再试",
        ) from None

    return {
        "result": "ok",
        "expires_in": settings.REGISTER_CODE_TTL_SECONDS,
        "resend_after": settings.REGISTER_CODE_RESEND_SECONDS,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    email = str(body.email).lower()
    async with session.begin():
        user_repo = UserRepo(session)
        code_repo = RegisterCodeRepo(session)
        if await user_repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该邮箱已被注册",
            )
        row = await code_repo.get_by_email(email)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先获取邮箱验证码",
            )
        if row.expires_at < datetime.utcnow():
            await code_repo.delete_by_email(email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码已过期，请重新获取",
            )
        if not verify_register_code(email, body.code, row.code_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误",
            )
        await code_repo.delete_by_email(email)
        user = UserModel(
            id=str(uuid.uuid4()),
            email=email,
            password=body.password,
        )
        await user_repo.create(user)
    return {"result": "ok"}


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        repo = UserRepo(session)
        user = await repo.get_by_email(str(body.email).lower())
        if not user or not user.check_password(body.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )
        tokens = auth_handler.encode_login_token(user.id)
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserPublic(id=user.id, email=user.email),
    )


@router.post("/logout")
async def logout():
    return {"result": "ok"}
