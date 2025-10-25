#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "[services] 停止 xuanji_ai_main.py ..."
pkill -f 'python -u xuanji_ai_main.py' || true

echo "[services] 停止 API 服务 (gunicorn_api) ..."
pkill -f 'gunicorn_api.conf.py' || true

echo "[services] 停止 WeChat 服务 (gunicorn_wechat) ..."
pkill -f 'gunicorn_wechat.conf.py' || true

echo "[services] 已发送停止信号。"
