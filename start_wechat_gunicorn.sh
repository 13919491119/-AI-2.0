#!/bin/bash
set -e
export WECHAT_TOKEN=${WECHAT_TOKEN:-celestial_nexus_ai_token}
export STRICT_WECHAT_VERIFY=${STRICT_WECHAT_VERIFY:-1}
export USE_NGROK=${USE_NGROK:-false}
PORT=${WECHAT_PORT:-9090}

echo "[WeChat] 使用Gunicorn启动 端口=$PORT 严格验证=$STRICT_WECHAT_VERIFY Ngrok=$USE_NGROK"
if [ "$USE_NGROK" = "true" ]; then
  echo "[WeChat] Gunicorn模式暂不内嵌Ngrok，请先单独运行 python wechat_server.py 生成URL 或使用外部反向代理"
fi

# 加载可选加密环境 (.env.wechat) 不退出（若不存在）
if [ -f .env.wechat ]; then
  echo "[WeChat] 加载 .env.wechat 环境变量"
  # shellcheck disable=SC2046
  export $(grep -E '^(WECHAT_ENCODING_AES_KEY|WECHAT_APPID)=' .env.wechat | xargs)
  if [ -n "${WECHAT_ENCODING_AES_KEY:-}" ]; then
    echo "[WeChat] 已检测到加密模式配置 (AES Key 长度=${#WECHAT_ENCODING_AES_KEY})"
  fi
fi

GUNICORN_BIN="gunicorn"
if [ -x "/workspaces/-AI-2.0/.venv/bin/gunicorn" ]; then
  GUNICORN_BIN="/workspaces/-AI-2.0/.venv/bin/gunicorn"
elif command -v python >/dev/null 2>&1 && python -c "import gunicorn" 2>/dev/null; then
  GUNICORN_BIN="python -m gunicorn"
fi

echo "[WeChat] 使用执行器: $GUNICORN_BIN"
exec $GUNICORN_BIN -c gunicorn_wechat.conf.py wechat_server:app
