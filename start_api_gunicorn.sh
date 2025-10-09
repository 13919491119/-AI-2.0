#!/bin/bash
set -euo pipefail
export PORT=${API_PORT:-8000}
GUNICORN_BIN="gunicorn"
if [ -x "/workspaces/-AI-2.0/.venv/bin/gunicorn" ]; then
  GUNICORN_BIN="/workspaces/-AI-2.0/.venv/bin/gunicorn"
elif command -v python >/dev/null 2>&1 && python -c "import gunicorn" 2>/dev/null; then
  GUNICORN_BIN="python -m gunicorn"
fi
echo "[API] 使用Gunicorn(UvicornWorker) 端口=$PORT"
exec $GUNICORN_BIN -c gunicorn_api.conf.py celestial_nexus.api:app
