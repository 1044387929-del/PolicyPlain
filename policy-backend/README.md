# PolicyPlain API

## 数据库（PostgreSQL）

默认使用 **本地 PostgreSQL**，异步驱动 **asyncpg**。

- 先建库：`CREATE DATABASE policy_plain;`
- 在 **`settings/setting.env`** 里改 `DB_USER` 或 **`DB_USERNAME`**、`DB_PASSWORD`、`DB_NAME`（或填完整 `DATABASE_URL`，须为 `postgresql+asyncpg://...`）。
- 可选：在项目根目录放 **`.env`**，同名变量会**覆盖** `setting.env`，适合本机密钥不入库。

**表结构由 Alembic 迁移维护**（对齐 `hr-backend` 习惯）；应用启动**不会**自动建表，需先执行迁移。

## Redis（与 hr-backend 一致）

- 本地需启动 **Redis**（默认 `127.0.0.1:6379`，可用环境变量 **`REDIS_HOST` / `REDIS_PORT`** 修改）。
- 应用启动时在 `lifespan` 中创建 **`redis.asyncio`** 客户端并注入 **`PolicyCache`**（见 `core/cache.py`）；注册验证码以 JSON 写入 Redis，键前缀 `policy-plain:register:`。

### 初始化数据库（迁移）

```bash
cd policy-backend
# 推荐（与 hr-backend 一致用 uv 管理依赖）：
uv sync
# 或：pip install -r requirements.txt
# 编辑 settings/setting.env（或根目录 .env）后任选其一：
uv run python -m alembic upgrade head
# Windows：.\scripts\init_db.ps1
# Bash：  bash scripts/init_db.sh
```

## 运行

```bash
cd policy-backend
uv sync
# 已执行 alembic upgrade head 后：
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
# 或激活 .venv 后：uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**`policy-backend/.env.example`** 可作字段说明；含 **邮件验证码注册** 所需 `MAIL_*` 与可选 `REGISTER_CODE_*`。

## 注册（邮箱验证码）

1. 在 `setting.env`（或根目录 `.env`）配置 **`MAIL_USERNAME` / `MAIL_PASSWORD`**（QQ 邮箱为 **SMTP 授权码**），默认 **`MAIL_SMTP_HOST=smtp.qq.com`**、`MAIL_SMTP_PORT=465`。
2. 前端：输入邮箱 → **获取验证码** → 查收邮件中的 6 位数字 → 设置密码与确认密码 → **注册**。
3. 接口（对齐 hr-backend 路由风格）：`POST /api/v1/user/register/send-code` 发信；`POST /api/v1/user/register` 提交 `invite_code` 与密码完成注册。未配置邮件时发码接口返回 **503**。
4. 重发间隔 **`REGISTER_CODE_RESEND_SECONDS`**（默认 60）；验证码有效期 **`REGISTER_CODE_TTL_SECONDS`**（默认 600）。

## 政策解读 LLM（通义千问 / 百炼）

与 **`hr-backend/agents/llms.py`** 相同思路：通过 **OpenAI 兼容接口** 调用 DashScope 上的 Qwen。

- 在 **`settings/setting.env`** 或根目录 **`.env`** 中配置 **`DASHSCOPE_API_KEY`**（与 hr-backend 的 `DASHSCOPE_API_KEY` 一致）或 **`OPENAI_API_KEY`** 任一即可；**优先读 `DASHSCOPE_API_KEY`**，避免本机环境里空的 `OPENAI_API_KEY` 把百炼密钥「盖住」。
- 默认 **`OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`**、**`OPENAI_MODEL=qwen3-max`**；若改用官方 OpenAI，请把 `OPENAI_BASE_URL` 设为 `https://api.openai.com/v1` 并设置对应模型名。
- 未配置任一密钥时，`/policy/explain` 仍走流式通道，内容为 **演示用 mock JSON** 分片，便于无密钥验收。
- **`POST /api/v1/policy/explain`** 响应为 **`text/event-stream`（SSE）**：每行 `data: {...}`，`event` 为 `delta`（模型输出增量）、`done`（含 `record_id` 与完整结构化结果）、`error`（`detail`）。服务端在收齐合法 JSON 并校验通过后写入数据库再发送 `done`。
- 若百炼返回 **401 / invalid_api_key**：在控制台重新创建 API-KEY，确认未过期、复制完整；不要在 `KEY = value` 的等号两侧加空格（部分编辑器会误配）。
