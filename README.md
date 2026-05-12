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
pip install -r requirements.txt
copy .env.example .env
# 在 .env 中配置本地 PG（DB_* 或 DATABASE_URL），并先 CREATE DATABASE
# 可选：填写 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
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

1. 打开前端 → **注册** → **登录**
2. 在「解读」页粘贴一段政策样例 → **生成白话解读**
3. 打开 **历史** → 查看单条详情（含原文与结构化 JSON）

## 环境变量（后端）

见 `policy-backend/.env.example`。

## 文档索引

- `docs/项目需求分析.md`
- `docs/项目概要设计.md`（若与已实现接口有出入，以 `policy-backend` 与 `/docs` OpenAPI 为准）
- `docs/技术实施步骤.md`

