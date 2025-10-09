#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# 可配置端口
: "${API_PORT:=8000}"
: "${WECHAT_PORT:=9090}"

echo "[services] 启动后台自动推演..."
nohup bash -lc 'source .venv/bin/activate && python -u xuanji_ai_main.py' >> ai_system.log 2>&1 &
AI_PID=$!
echo "[services] xuanji_ai_main.py PID=$AI_PID (logs: ai_system.log)"

echo "[services] 启动API服务 (gunicorn+uvicorn workers)..."
nohup bash -lc './start_api_gunicorn.sh' >> api_server.log 2>&1 &
API_PID=$!
echo "[services] API bootstrap PID=$API_PID (logs: api_server.log)"

if [ -f WECHAT_LINK_PENDING.md ] && [ "${FORCE_WECHAT_LINK:-0}" != "1" ]; then
  echo "[services] 检测到 WECHAT_LINK_PENDING.md，暂不启动公众号服务（可设置 FORCE_WECHAT_LINK=1 覆盖）"
else
  echo "[services] 启动微信公众号接入服务..."
  nohup bash -lc './start_wechat_gunicorn.sh' >> wechat_server.log 2>&1 &
  WECHAT_PID=$!
  echo "[services] WeChat bootstrap PID=$WECHAT_PID (logs: wechat_server.log)"
fi

echo "[services] 全部服务已触发启动。可用命令查看：ps -ef | grep -E "'xuanji_ai_main.py|gunicorn|uvicorn'""
