# PolicyPlain

老年友好型 **社保 / 医保 / 养老** 政策「白话解读」小应用：Vue3 + FastAPI + **PostgreSQL（asyncpg）** + JWT；未配置大模型 API Key 时后端返回 **mock 结构化结果**，便于本地演示。

## 仓库结构


| 目录                               | 说明                                                                   |
| -------------------------------- | -------------------------------------------------------------------- |
| `docs/`                          | 需求、概要、实施步骤等文档                                                        |
| `policy-backend/`                | 后端（对齐 `hr-backend` 风格：FastAPI、分层、JWT、SQLAlchemy 异步）                  |
| `policy-frontend/`               | 前端（对齐 `hr-frontend-src`：Vite、Vue3、Pinia、Axios、Element Plus、Tailwind） |
| `hr-backend/`、`hr-frontend-src/` | 课程参考工程（本仓库 `.gitignore` 中可按需忽略）                                      |


## 快速启动

### 1. 后端

```powershell
cd policy-backend
python -m venv .venv
.\.venv\Scripts\activate
uv sync
# 或：pip install -r requirements.txt
copy .env.example .env
# 在 .env 中配置本地 PG（DB_* 或 DATABASE_URL），并先 CREATE DATABASE
# 启动本地 Redis（默认 127.0.0.1:6379，与 hr-backend 一致）
# 执行迁移：uv run python -m alembic upgrade head（或 policy-backend/scripts 下 init 脚本）
# 可选：填写 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 健康检查：[http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. 前端

```powershell
cd policy-frontend
npm install
npm run dev
```

默认请求后端：`policy-frontend/.env.development` 中 `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`。

## 演示路径

1. 打开前端 → **邮箱收验证码** → **注册** → **登录**（需本地 **Redis**；邮件发码见 `policy-backend/README.md`）
2. 在「白话解读」页：**粘贴正文**或切换到 **输入网址**（公网政策页）→ **生成白话解读**
3. 生成过程中后端以 **SSE** 推送 `partial`（可解析的结构化片段），前端**渐进展示**；结束后写入 **历史**
4. 右下角 **「看字大小」**：可**全局放大字号**（标准 / 大字 / 特大），支持**收起**为浮钮；设置保存在浏览器 `localStorage`
5. 打开 **历史记录** → 查看单条详情（含保存的原文摘录/要点与结构化结果）

**外网演示（可选）**：`ngrok http 8080` 穿透前端时，已在 `policy-frontend/vite.config.ts` 中配置 `server.allowedHosts` 以允许 `*.ngrok-free.dev` 等域名；若 API 仍指向本机，需在 `.env` 中为穿透环境单独配置 `VITE_API_BASE_URL` 并处理后端的 **CORS**。

## 环境变量（后端）

见 `policy-backend/.env.example` 与 `policy-backend/README.md`（含 **Redis**、**邮件验证码**、**LLM / 百炼** 说明）。

## 文档索引

- `docs/项目需求分析.md`
- `docs/项目概要设计.md`（与代码不一致时，以 `policy-backend` OpenAPI `/docs` 与源码为准）
- `docs/项目实施流程与顺序.md`
- `docs/技术实施步骤.md`
- `policy-backend/README.md`（数据库、Redis、邮件注册、LLM 与 SSE 说明）

