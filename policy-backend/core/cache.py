"""Redis 缓存封装（行为对齐 hr-backend HRCache；直接使用 redis.asyncio，避免 fastapi-cache 包名冲突）。"""

from redis.asyncio import Redis

from schemas.cache_schema import RegisterInfoSchema
from settings import settings

_redis: Redis | None = None


def set_redis_client(client: Redis | None) -> None:
    """由 main.py lifespan 在启动/关闭时注入或清空 Redis 客户端。"""
    global _redis
    _redis = client


def get_redis_for_cache() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis 未初始化：请确认 lifespan 已调用 set_redis_client")
    return _redis


class PolicyCache:
    """注册验证码等缓存（键前缀与原先 FastAPICache 语义区分，避免与其它服务冲突）。"""

    register_key_prefix = "policy-plain:register:"

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def set(self, key: str, value: str, ex: int) -> None:
        await self._redis.set(key, value, ex=ex)

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def set_register_info(self, info: RegisterInfoSchema) -> None:
        key = f"{self.register_key_prefix}{info.email}"
        await self.set(key, info.model_dump_json(), ex=settings.REGISTER_CODE_TTL_SECONDS)

    async def get_register_info(self, email: str) -> RegisterInfoSchema | None:
        key = f"{self.register_key_prefix}{email}"
        raw = await self.get(key)
        if raw is not None:
            return RegisterInfoSchema.model_validate_json(raw)
        return None

    async def delete_register_info(self, email: str) -> None:
        await self.delete(f"{self.register_key_prefix}{email}")
