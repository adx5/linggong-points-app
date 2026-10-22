#!/usr/bin/env bash
# 扣子部署构建阶段：安装 Python 依赖
set -e
cd "$(dirname "$0")/.."
python3 -m pip install --no-cache-dir --upgrade pip
python3 -m pip install --no-cache-dir -r requirements.txt
echo "✅ dependencies installed"