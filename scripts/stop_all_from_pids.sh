#!/bin/bash
# 优雅停止基于 logs/*.pid 中记录的进程
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

kill_if_exists() {
  local pidfile="$1"
  local name="$2"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile" 2>/dev/null || true)
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
      echo "Stopping $name (pid $pid)"
      kill "$pid" || true
      # wait up to 5s
      for i in {1..5}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
          break
        fi
        sleep 1
      done
      if ps -p "$pid" > /dev/null 2>&1; then
        echo "$name did not stop, killing..."
        kill -9 "$pid" || true
      fi
    else
      echo "No running $name found for pidfile $pidfile"
    fi
    rm -f "$pidfile" || true
  else
    echo "Pidfile $pidfile not found; skipping $name"
  fi
}

kill_if_exists "$ROOT_DIR/logs/api.pid" "api (uvicorn)"
kill_if_exists "$ROOT_DIR/logs/report_frontend.pid" "report_frontend"

echo "Done stopping known services."
