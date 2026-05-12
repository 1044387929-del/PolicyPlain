from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, health, policy, users
from settings import settings

app = FastAPI(title="PolicyPlain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(policy.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "PolicyPlain API", "docs": "/docs"}
