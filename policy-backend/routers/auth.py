import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models import auth_handler, get_session
from models.user import UserModel
from repository.user_repo import UserRepo
from schemas.policy import LoginRequest, LoginResponse, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        repo = UserRepo(session)
        if await repo.get_by_username(body.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在",
            )
        user = UserModel(
            id=str(uuid.uuid4()),
            username=body.username,
            password=body.password,
        )
        await repo.create(user)
    return {"result": "ok"}


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        repo = UserRepo(session)
        user = await repo.get_by_username(body.username)
        if not user or not user.check_password(body.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )
        tokens = auth_handler.encode_login_token(user.id)
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserPublic(id=user.id, username=user.username),
    )


@router.post("/logout")
async def logout():
    return {"result": "ok"}
