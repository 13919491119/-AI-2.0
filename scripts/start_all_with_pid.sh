#!/bin/bash
# 启动服务并把子进程 PID 写入 logs/ （谨慎使用：不要在已有相同服务运行时重复执行）
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT_DIR/logs"

echo "Starting services and writing PIDs to $ROOT_DIR/logs/"

cd "$ROOT_DIR"

# start API
if pgrep -f "uvicorn .*celestial_nexus.api" >/dev/null 2>&1; then
  echo "uvicorn celestial_nexus.api already running; skipping start"
else
  nohup uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000 --reload > "$ROOT_DIR/logs/api_server.log" 2>&1 &
  echo $! > "$ROOT_DIR/logs/api.pid"
  echo "Started api pid $(cat $ROOT_DIR/logs/api.pid)"
fi

# start frontend
if pgrep -f "report_frontend.py" >/dev/null 2>&1; then
  echo "report_frontend.py already running; skipping start"
else
  nohup python3 celestial_nexus/report_frontend.py > "$ROOT_DIR/logs/report_frontend.log" 2>&1 &
  echo $! > "$ROOT_DIR/logs/report_frontend.pid"
  echo "Started frontend pid $(cat $ROOT_DIR/logs/report_frontend.pid)"
fi

echo "All requested starts attempted. Check $ROOT_DIR/logs/ for logs and pid files."
