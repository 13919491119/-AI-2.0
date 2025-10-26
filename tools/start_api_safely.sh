#!/usr/bin/env bash
set -euo pipefail

# start_api_safely.sh
# Purpose: Start the FastAPI uvicorn server on a port that is not in use.
# It reads PORT from the environment (default 8000). If that port is occupied,
# it will probe subsequent ports (8001, 8002, ...) until it finds a free one,
# then launches uvicorn binding to that port. This avoids killing existing
# processes that may already be listening on the default port.

PORT_ARG=${1:-}
DEFAULT_PORT=${PORT_ARG:-${PORT:-8000}}

port_in_use() {
  local p=$1
  if ss -ltnp 2>/dev/null | grep -q ":${p} "; then
    return 0
  fi
  if lsof -i :${p} >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

chosen_port=$DEFAULT_PORT
MAX_TRIES=100
tries=0
while port_in_use "$chosen_port"; do
  tries=$((tries+1))
  if [ $tries -ge $MAX_TRIES ]; then
    echo "无法在范围内找到空闲端口 (tried $tries ports)." >&2
    exit 1
  fi
  echo "端口 ${chosen_port} 已被占用，尝试下一个端口..."
  chosen_port=$((chosen_port+1))
done

export PORT=$chosen_port
echo "启动 uvicorn，使用 PORT=$PORT (若需覆盖请在命令行设置 PORT 环境变量)"

exec uvicorn api.server:app --host 127.0.0.1 --port "$PORT"
