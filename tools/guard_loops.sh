#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

LOG_DIR="/workspaces/-AI-2.0/logs/guard"
mkdir -p "$LOG_DIR"

# 加载 .env 以继承推荐的服务器参数（如 SSQ_* 与 DEEPSEEK_API_KEY）
if [ -f ./.env ]; then
  set -a
  . ./.env
  set +a
fi

# start_or_keep "name" "cmd" "pidfile"
start_or_keep() {
  local name="$1"; shift
  local cmd="$1"; shift
  local pidfile="$1"; shift

  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] running PID $(cat "$pidfile")"
    return 0
  fi

  echo "[$name] starting..."
  # shellcheck disable=SC2086
  nohup bash -lc "$cmd" >> "$LOG_DIR/${name}.log" 2>&1 &
  echo $! > "$pidfile"
  echo "[$name] started PID $(cat "$pidfile")"
}

# 优先使用项目本地虚拟环境的 Python，如不存在则回退到系统 Python
if [ -x "/workspaces/-AI-2.0/.venv/bin/python3" ]; then
  PYTHON_BIN="/workspaces/-AI-2.0/.venv/bin/python3"
else
  PYTHON_BIN="/bin/python3"
fi

start_or_keep "autonomous" "$PYTHON_BIN -u autonomous_run.py" "/workspaces/-AI-2.0/autonomous_run.pid"
start_or_keep "predict"    "$PYTHON_BIN -u ssq_fusion_predict_cycle.py" "/workspaces/-AI-2.0/ssq_fusion_predict_cycle.pid"
start_or_keep "optimize"   "$PYTHON_BIN -u auto_optimize_cycle.py" "/workspaces/-AI-2.0/auto_optimize_cycle.pid"

# 历史人物任务守护
start_or_keep "person"     "$PYTHON_BIN -u person_predict_cycle.py" "/workspaces/-AI-2.0/person_predict_cycle.pid"

# 八字起名任务守护（轻量队列消费，见 bazi_naming_cycle.py）
start_or_keep "bazi_naming" "$PYTHON_BIN -u bazi_naming_cycle.py" "/workspaces/-AI-2.0/bazi_naming_cycle.pid"

echo "guard done. logs in $LOG_DIR"
