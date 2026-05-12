import jwt
from datetime import datetime
from enum import Enum
from threading import Lock

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from settings import settings


class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class TokenTypeEnum(Enum):
    ACCESS_TOKEN = 1
    REFRESH_TOKEN = 2


class AuthHandler(metaclass=SingletonMeta):
    security = HTTPBearer()
    secret = settings.JWT_SECRET_KEY

    def _encode_token(self, iss: str, type: TokenTypeEnum) -> str:
        payload = dict(iss=iss, sub=str(type.value))
        to_encode = payload.copy()
        if type == TokenTypeEnum.ACCESS_TOKEN:
            exp = datetime.now() + settings.JWT_ACCESS_TOKEN_EXPIRES
        else:
            exp = datetime.now() + settings.JWT_REFRESH_TOKEN_EXPIRES
        to_encode["exp"] = int(exp.timestamp())
        return jwt.encode(to_encode, self.secret, algorithm="HS256")

    def encode_login_token(self, iss: str) -> dict[str, str]:
        return {
            "access_token": self._encode_token(iss, TokenTypeEnum.ACCESS_TOKEN),
            "refresh_token": self._encode_token(iss, TokenTypeEnum.REFRESH_TOKEN),
        }

    def decode_access_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            if payload["sub"] != str(TokenTypeEnum.ACCESS_TOKEN.value):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Token 类型错误"
                )
            return str(payload["iss"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Access Token 已过期"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Access Token 无效"
            )

    def auth_access_dependency(
        self, auth: HTTPAuthorizationCredentials = Security(security)
    ) -> str:
        return self.decode_access_token(auth.credentials)
