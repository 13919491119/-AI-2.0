#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PID_FILE=.xuanji_ai.pid
LOG=ai_system.log

start() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "[xuanji_ai] already running with PID $(cat "$PID_FILE")"
    exit 0
  fi
  echo "[xuanji_ai] starting..."
  nohup bash -lc 'source .venv/bin/activate && python -u xuanji_ai_main.py' >> "$LOG" 2>&1 &
  echo $! > "$PID_FILE"
  echo "[xuanji_ai] started PID $(cat "$PID_FILE") (logs: $LOG)"
}

stop() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    kill $(cat "$PID_FILE") || true
    rm -f "$PID_FILE"
    echo "[xuanji_ai] stopped"
  else
    echo "[xuanji_ai] not running"
  fi
}

status() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "[xuanji_ai] running with PID $(cat "$PID_FILE")"
  else
    echo "[xuanji_ai] not running"
    exit 1
  fi
}

case "$1" in
  start) start ;;
  stop) stop ;;
  restart) stop || true; start ;;
  status) status ;;
  *) echo "Usage: $0 {start|stop|restart|status}" ; exit 1 ;;
esac
