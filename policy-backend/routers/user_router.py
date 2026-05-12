import secrets
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import PolicyCache
from dependencies import get_cache_instance, get_current_user, get_session_instance
from models import auth_handler
from models.user import UserModel
from repository.user_repo import UserRepo
from schemas.cache_schema import RegisterInfoSchema
from schemas.response_schema import ResponseSchema
from schemas.user_schema import (
    UserLoginRespSchema,
    UserLoginSchema,
    UserRegisterSchema,
    UserRegisterSendCodeRespSchema,
    UserRegisterSendCodeSchema,
    UserSchema,
)
from settings import settings
from tasks import send_register_code_email_task

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/login", summary="登录", response_model=UserLoginRespSchema)
async def login(
    login_data: UserLoginSchema,
    session: AsyncSession = Depends(get_session_instance),
):
    async with session.begin():
        user_repo = UserRepo(session)
        user = await user_repo.get_by_email(str(login_data.email).lower())
        if not user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="该用户不存在！")
        if not user.check_password(login_data.password):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="邮箱或密码错误！")
        tokens = auth_handler.encode_login_token(user.id)
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "user": user,
    }


@router.post(
    "/register/send-code",
    summary="发送注册邮箱验证码",
    response_model=UserRegisterSendCodeRespSchema,
)
async def send_register_code(
    body: UserRegisterSendCodeSchema,
    background_tasks: BackgroundTasks,
    cache: PolicyCache = Depends(get_cache_instance),
    session: AsyncSession = Depends(get_session_instance),
):
    if not settings.mail_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="邮件服务未配置：请在环境变量中填写 MAIL_USERNAME 与 MAIL_PASSWORD",
        )
    email = str(body.email).lower()
    invite_code = f"{secrets.randbelow(1_000_000):06d}"

    async with session.begin():
        user_repo = UserRepo(session)
        if await user_repo.get_by_email(email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="该邮箱已被注册！")

    existing = await cache.get_register_info(email)
    if existing is not None:
        elapsed = time.time() - existing.sent_epoch
        if elapsed < settings.REGISTER_CODE_RESEND_SECONDS:
            wait = int(settings.REGISTER_CODE_RESEND_SECONDS - elapsed)
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"发送过于频繁，请 {wait} 秒后再试",
            )

    await cache.set_register_info(
        RegisterInfoSchema(email=email, invite_code=invite_code, sent_epoch=time.time())
    )
    background_tasks.add_task(
        send_register_code_email_task,
        email=email,
        invite_code=invite_code,
    )
    return UserRegisterSendCodeRespSchema(
        result="success",
        expires_in=settings.REGISTER_CODE_TTL_SECONDS,
        resend_after=settings.REGISTER_CODE_RESEND_SECONDS,
    )


@router.post("/register", summary="注册", response_model=ResponseSchema)
async def register(
    register_data: UserRegisterSchema,
    cache: PolicyCache = Depends(get_cache_instance),
    session: AsyncSession = Depends(get_session_instance),
):
    email = str(register_data.email).lower()
    invite_info = await cache.get_register_info(email)
    if not invite_info:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="该邮箱账号不存在！")
    if invite_info.invite_code != register_data.invite_code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="邀请码错误！")

    async with session.begin():
        user_repo = UserRepo(session)
        if await user_repo.get_by_email(email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="该邮箱已被注册！")
        await user_repo.create_user(
            {
                "id": str(uuid.uuid4()),
                "email": email,
                "password": register_data.password,
            }
        )
    return ResponseSchema()


@router.get("/me", summary="获取当前用户", response_model=UserSchema)
async def me(current: UserModel = Depends(get_current_user)):
    return current


@router.post("/logout", summary="退出登录", response_model=ResponseSchema)
async def logout():
    return ResponseSchema()
