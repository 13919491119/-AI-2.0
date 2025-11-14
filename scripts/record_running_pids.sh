#!/bin/bash
# 记录当前运行的服务 PID 到 logs/，不会启动或停止任何进程
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT_DIR/logs"

echo "Recording running PIDs to $ROOT_DIR/logs/"

# Find uvicorn server running celestial_nexus.api
API_PID=$(pgrep -f "uvicorn .*celestial_nexus.api" || true)
if [ -n "$API_PID" ]; then
  echo "$API_PID" > "$ROOT_DIR/logs/api.pid"
  echo "api.pid -> $API_PID"
else
  echo "No uvicorn celestial_nexus.api process found"
fi

# Find report frontend process
FRONT_PID=$(pgrep -f "report_frontend.py" || true)
if [ -n "$FRONT_PID" ]; then
  echo "$FRONT_PID" > "$ROOT_DIR/logs/report_frontend.pid"
  echo "report_frontend.pid -> $FRONT_PID"
else
  echo "No report_frontend.py process found"
fi

echo "Done."
