# PolicyPlain API

## 数据库（PostgreSQL）

默认使用 **本地 PostgreSQL**，异步驱动 **asyncpg**。

- 先建库：`CREATE DATABASE policy_plain;`
- 在 **`settings/setting.env`** 里改 `DB_USER` / `DB_PASSWORD` / `DB_NAME`（或填完整 `DATABASE_URL`，须为 `postgresql+asyncpg://...`）。
- 可选：在项目根目录放 **`.env`**，同名变量会**覆盖** `setting.env`，适合本机密钥不入库。

启动时会执行 `create_all` 建表（笔试可用；生产建议 Alembic）。

## 运行

```bash
cd policy-backend
pip install -r requirements.txt
# 编辑 settings/setting.env 后：
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

根目录 **`.env.example`** 可作字段说明备份，与 `setting.env` 字段一致。

## 说明

- 未设置 `OPENAI_API_KEY` 时，`/policy/explain` 返回 **演示用 mock JSON**，便于无密钥验收。
