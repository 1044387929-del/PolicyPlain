from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from core.cache import set_redis_client
from routers import health, policy, user_router
from settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_client = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True,
    )
    set_redis_client(redis_client)
    try:
        yield
    finally:
        await redis_client.aclose()
        set_redis_client(None)


app = FastAPI(title="PolicyPlain API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(user_router.router, prefix="/api/v1")
app.include_router(policy.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "PolicyPlain API", "docs": "/docs"}
