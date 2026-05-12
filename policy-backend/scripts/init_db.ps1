# 在 policy-backend 目录执行 Alembic 迁移到 head（需已安装依赖并配置 PG）。
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$backendRoot = Split-Path -Parent $PSScriptRoot
Push-Location $backendRoot
try {
    python -m alembic upgrade head
}
finally {
    Pop-Location
}
