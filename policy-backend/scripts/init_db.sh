#!/usr/bin/env bash
# 在 policy-backend 目录执行 Alembic 迁移到 head（需已安装依赖并配置 PG）。
set -euo pipefail
cd "$(dirname "$0")/.."
python -m alembic upgrade head
