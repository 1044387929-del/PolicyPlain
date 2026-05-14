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
- **`POST /api/v1/policy/explain`** 响应为 **`text/event-stream`（SSE）**：每行 `data: {...}`，`event` 为 `partial`（流式过程中可校验的结构化片段，字段在 `data` 内）、`done`（含 `record_id` 与完整结果）、`error`（`detail`）。服务端在收齐合法 JSON 并校验通过后写入数据库再发送 `done`。
- 若百炼返回 **401 / invalid_api_key**：在控制台重新创建 API-KEY，确认未过期、复制完整；不要在 `KEY = value` 的等号两侧加空格（部分编辑器会误配）。

## 政策截图 OCR（PaddleOCR 云端，对齐 hr-backend）

与 **`hr-backend/core/ocr.py`** 相同：使用飞桨 **AI Studio** 的 **`PADDLE_OCR_ACCESS_TOKEN`** 访问 `paddleocr.aistudio-app.com` 的 OCR Jobs API（默认模型 **`PaddleOCR-VL-1.5`**）。

- 配置 **`PADDLE_OCR_ACCESS_TOKEN`**（见 `.env.example`）；可选 **`PADDLE_OCR_JOB_URL`**、**`PADDLE_OCR_MODEL_NAME`**。
- **`POST /api/v1/policy/ocr-image`**：`multipart/form-data` 字段 **`file`**（JPG / PNG / WebP，≤ 8MB），需 **Bearer** 登录；成功返回 **`{ "text": "..." }`**。
- 未配置 Token 时返回 **503**；识别失败返回 **502**。

## 政策解读 API 与流程细节

### `POST /api/v1/policy/explain`

- **鉴权**：需 **Bearer** JWT。  
- **请求体**：`text`（可选）、`url`（可选）、`topic`（`general` | `medical_insurance` | `pension`，缺省为 `general`）；**`text` 与 `url` 至少填一项**（与 Pydantic 校验一致）。  
- **响应**：`Content-Type: text/event-stream`（SSE），每行 `data: <JSON>`。  
- **`event` 取值**：  
  - **`status`**：可选；含 `stage`（如 `fetch` / `parse` / `synopsis` / `explain`）与 `message`，主要在「带 URL」流程中出现。  
  - **`partial`**：流式阶段已累积输出经 `json-repair` 等尝试解析后的**可展示片段**（无 `record_id`）。  
  - **`done`**：成功结束，含 **`record_id`** 与完整结构化结果（已写入 `policy_explanations`）。  
  - **`error`**：`detail` 为人类可读错误。  
- **兼容接口**：`POST /api/v1/policy/explain-from-url` 等价于仅传 `url`、不传 `text` 的 explain。

### 带 URL 时的服务端顺序（摘要）

1. 校验公网 URL → **抓取 HTML**（大小与重定向次数见 **`URL_FETCH_MAX_BYTES`**、**`URL_FETCH_MAX_REDIRECTS`**）。  
2. **HTML → 纯文本**，截断至 **`URL_EXTRACT_MAX_CHARS`**（默认 18000）。  
3. 调用大模型 **`SYNOPSIS_SYSTEM`** 提示词，得到 JSON 中的 **`synopsis`** 字符串；过短则判为无效内容。  
4. 将 synopsis 与用户粘贴（若有）合并为送入主解读模型的 **`text_for_llm`**，总长不超过 **`POLICY_TEXT_MAX_CHARS`**（默认 12000）。  
5. 主解读使用 **`SYSTEM_PROMPT`**，流式 **`response_format: json_object`**，落库前严格校验。

### 追问 `POST /api/v1/policy/explanations/{record_id}/follow-up`（流式）

- **请求体**：JSON 含 **`question`**（非空字符串）。  
- **响应**：SSE；成功结束事件含 **`answer`**、**`turn`**、**`followup_id`**。  
- 针对已有 **`record_id`** 的解读；使用保存的原文摘录与结构化结果 JSON，以及该记录下已有追问轮次，调用 **`FOLLOWUP_SYSTEM`** 提示词；输出为 **纯文本** 流（非 JSON）。  
- **每条约 3 轮追问**（代码常量 **`MAX_FOLLOWUP_ROUNDS`**，以 `policy.py` 为准）。

### 历史与详情

- **`GET /api/v1/policy/explanations`**：分页列表（`limit` / `offset`），仅当前用户。  
- **`GET /api/v1/policy/explanations/{record_id}`**：单条详情（原文摘录、结构化结果、已有追问列表）。

### 提示词位置（便于调优）

- 主解读、网页 synopsis、追问的系统提示均在 **`services/explain_llm.py`**（`SYSTEM_PROMPT`、`SYNOPSIS_SYSTEM`、`FOLLOWUP_SYSTEM`）。

### 其它可调环境变量（解读链路）

- **`POLICY_TEXT_MAX_CHARS`**：送入主解读模型的最大字符数。  
- **`URL_EXTRACT_MAX_CHARS`**：参与 synopsis 的网页纯文本上限。  
- **`LLM_TIMEOUT_SECONDS`**：大模型请求超时。  

完整列表见 **`settings/__init__.py`** 与 **`.env.example`**。
