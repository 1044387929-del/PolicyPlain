# PolicyPlain

老年友好型 **社保 / 医保 / 养老** 政策「白话解读」小应用：Vue3 + FastAPI + **PostgreSQL（asyncpg）** + JWT；未配置大模型 API Key 时后端返回 **mock 结构化结果**，便于本地演示。

## 功能概览

| 模块 | 说明 |
| --- | --- |
| **账户** | 邮箱验证码注册、登录、JWT（Access / Refresh）、退出；验证码存 **Redis**，用户与解读记录存 **PostgreSQL**。 |
| **白话解读** | 将政策材料转为结构化白话卡片（一句话摘要、适用条件、材料、渠道、时间节点、易误解点等）；支持 **SSE 流式**渐进展示。 |
| **材料来源** | **粘贴正文**、**公网政策页 URL**、**截图 OCR 识别** 可单独或组合使用；有 URL 时服务端先抓页、再 **LLM 提炼要点**，再与粘贴正文合并后解读。 |
| **解读主题** | 前端单选：`general`（社保综合）、`medical_insurance`（医保）、`pension`（养老保险），作为用户消息中的主题标签传给模型。 |
| **追问** | 对某条已保存的解读记录，在结果页发起多轮追问（后端限制每条约 **3 轮**）；流式纯文本回答。 |
| **历史** | 解读结果落库后可在历史列表查看详情（含当时输入摘录与结构化结果）。 |
| **适老化** | 大字号排版、结果页适老组件；全局 **「看字大小」**（标准 / 大字 / 特大）写入 `localStorage`。 |

## 前后端细节（与界面行为对齐）

### 解读输入

- **至少一种**：正文非空 **或** 政策页链接非空（或先 OCR 再写入正文）。  
- **仅粘贴**：全文直接作为「政策原文」进入解读；超长由后端 **`POLICY_TEXT_MAX_CHARS`**（默认 12000）限制。  
- **含 URL**：仅公网 `http/https`；抓取 HTML → 转纯文本 → 若正文过短会报错；否则 **LLM 生成 synopsis**，再与可选的用户粘贴合并；合并文本同样受字数上限约束。SSE 中会先出现 **`status`** 阶段（如 `fetch` / `parse` / `synopsis` / `explain`）便于前端展示进度。  
- **截图 OCR**：`POST /api/v1/policy/ocr-image`，需登录与 **`PADDLE_OCR_ACCESS_TOKEN`**；前端支持上传 **JPG / PNG / WebP**（≤ **8MB**），并在下方虚线区域内 **先点击区域再 Ctrl+V（Mac ⌘+V）** 粘贴剪贴板图片，与上传等价；识别文本 **追加** 到正文框。

### 解读输出与 SSE

- 成功路径：`partial`（流式过程中可校验的结构化片段）→ `done`（含 **`record_id`** 与完整字段）。  
- 失败：`error` + `detail` 人类可读说明。  
- 结构化字段与 Pydantic 模型一致，包括 `summary_one_line`、`applicability`、`materials`（含 `items` 与 `source_note`）、`channels`、`important_dates`、`common_misunderstandings`、`uncovered_points`、`verification_hints`、`warnings` 等（详见 `docs/项目概要设计.md` 与 OpenAPI）。

### 前端交互

- **宽屏**：解读区为右侧可 **展开/收起** 的竖条 + 面板；**窄屏**：生成后以 **抽屉** 展示结果与追问。  
- **外网演示**：可用 ngrok 暴露前端；`vite.config.ts` 已放宽部分 ngrok 域名；若 API 不同源需配置 **`VITE_API_BASE_URL`** 与后端 **CORS**（见 `policy-backend/settings` 中 `CORS_ORIGINS`）。

### 安全与合规（产品侧）

- 页面含 **免责声明**：阅读辅助、以当地经办为准；政策原文可能落库，需注意隐私与账号隔离（详见需求文档 F4/F5）。

## 仓库结构

| 目录 | 说明 |
| --- | --- |
| `docs/` | 需求、概要、实施步骤等文档 |
| `policy-backend/` | 后端（FastAPI、分层、JWT、SQLAlchemy 异步、Alembic） |
| `policy-frontend/` | 前端（Vite、Vue3、Pinia、Axios、Element Plus、Tailwind） |
| `hr-backend/`、`hr-frontend-src/` | 课程参考工程（本仓库 `.gitignore` 中可按需忽略） |

## 技术栈（摘要）

- **前端**：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus、Tailwind CSS。  
- **后端**：Python 3、FastAPI、SQLAlchemy 2（async）、Alembic、httpx、OpenAI 兼容客户端（百炼 / DashScope）、Redis（asyncio）、SMTP 发信。  
- **数据**：PostgreSQL；Redis 仅用于注册验证码缓存。

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
# 可选：填写 DASHSCOPE_API_KEY / OPENAI_API_KEY、OPENAI_BASE_URL、OPENAI_MODEL
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

## 演示路径（建议顺序）

1. 打开前端 → **邮箱收验证码** → **注册** → **登录**（需本地 **Redis**；邮件发码见 `policy-backend/README.md`）。  
2. 在「白话解读」页：选择 **解读主题** → 粘贴正文、填写 **政策网页链接**、和/或 **上传 / 在截图区粘贴** 截图识别 → **生成白话解读**。  
3. 生成过程中后端以 **SSE** 推送 `status`（若有网址）与 **`partial`**，前端 **渐进展示**；结束后 **`done`** 并写入 **历史**。  
4. 在结果区域使用 **追问**（每记录最多约 3 轮，以服务端为准）。  
5. 右下角 **「看字大小」**：全局放大字号，设置保存在浏览器 **`localStorage`**。  
6. 打开 **历史记录** → 查看单条详情（含保存的原文摘录/要点与结构化结果）。

## 环境变量（后端）

见 `policy-backend/.env.example` 与 `policy-backend/README.md`（含 **Redis**、**邮件验证码**、**LLM / 百炼**、**OCR**、抓取与字数上限等可调项）。

## 文档索引

- `docs/项目需求分析.md`
- `docs/项目概要设计.md`（与代码不一致时，以 `policy-backend` OpenAPI `/docs` 与源码为准）
- `docs/项目实施流程与顺序.md`
- `docs/技术实施步骤.md`
- `policy-backend/README.md`（数据库、Redis、邮件注册、LLM、SSE、OCR、策略与限制）
