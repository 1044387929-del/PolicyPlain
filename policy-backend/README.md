# PolicyPlain API

## 数据库（PostgreSQL）

默认使用 **本地 PostgreSQL**，异步驱动 **asyncpg**。

- 先建库：`CREATE DATABASE policy_plain;`
- 在 **`settings/setting.env`** 里改 `DB_USER` 或 **`DB_USERNAME`**、`DB_PASSWORD`、`DB_NAME`（或填完整 `DATABASE_URL`，须为 `postgresql+asyncpg://...`）。
- 可选：在项目根目录放 **`.env`**，同名变量会**覆盖** `setting.env`，适合本机密钥不入库。

**表结构由 Alembic 迁移维护**（对齐 `hr-backend` 习惯）；应用启动**不会**自动建表，需先执行迁移。

### 初始化数据库（迁移）

```bash
cd policy-backend
pip install -r requirements.txt
# 编辑 settings/setting.env（或根目录 .env）后任选其一：
python -m alembic upgrade head
# Windows：.\scripts\init_db.ps1
# Bash：  bash scripts/init_db.sh
```

## 运行

```bash
cd policy-backend
pip install -r requirements.txt
# 已执行 alembic upgrade head 后：
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**`policy-backend/.env.example`** 可作字段说明；含 **邮件验证码注册** 所需 `MAIL_*` 与可选 `REGISTER_CODE_*`。

## 注册（邮箱验证码）

1. 在 `setting.env`（或根目录 `.env`）配置 **`MAIL_USERNAME` / `MAIL_PASSWORD`**（QQ 邮箱为 **SMTP 授权码**），默认 **`MAIL_SMTP_HOST=smtp.qq.com`**、`MAIL_SMTP_PORT=465`。
2. 前端：输入邮箱 → **获取验证码** → 查收邮件中的 6 位数字 → 设置密码与确认密码 → **注册**。
3. 接口：`POST /api/v1/auth/register/send-code` 发信；`POST /api/v1/auth/register` 校验验证码并建用户。未配置邮件时发码接口返回 **503**。
4. 重发间隔 **`REGISTER_CODE_RESEND_SECONDS`**（默认 60）；验证码有效期 **`REGISTER_CODE_TTL_SECONDS`**（默认 600）。

## 说明

- 未设置 `OPENAI_API_KEY` 时，`/policy/explain` 返回 **演示用 mock JSON**，便于无密钥验收。
