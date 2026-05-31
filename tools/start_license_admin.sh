#!/bin/bash
cd "$(dirname "$0")/.."
PYTHON="python-server/venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "未找到 venv，请先安装 python-server 依赖"
  exit 1
fi
exec "$PYTHON" tools/license_admin_app.py
