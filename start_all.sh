#!/bin/bash
# 一键启动玄机AI主服务与美化前端报告服务（更安全的版本：写入 logs/ 并避免重复启动）
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

echo "[1/2] 启动 FastAPI 主服务 (如果尚未运行)..."
if pgrep -f "uvicorn .*celestial_nexus.api" >/dev/null 2>&1; then
	echo "uvicorn celestial_nexus.api 似乎已在运行，跳过启动。"
else
	nohup uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000 --reload > "$ROOT_DIR/logs/api_server.log" 2>&1 &
	echo $! > "$ROOT_DIR/logs/api_manual.pid"
	echo "已启动 FastAPI，pid=$(cat $ROOT_DIR/logs/api_manual.pid) ，日志：$ROOT_DIR/logs/api_server.log"
fi

echo "[2/2] 启动美化前端报告服务 (如果尚未运行)..."
if pgrep -f "report_frontend.py" >/dev/null 2>&1; then
	echo "report_frontend.py 似乎已在运行，跳过启动。"
else
	nohup python3 celestial_nexus/report_frontend.py > "$ROOT_DIR/logs/report_frontend.log" 2>&1 &
	echo $! > "$ROOT_DIR/logs/report_frontend_manual.pid"
	echo "已启动 report_frontend，pid=$(cat $ROOT_DIR/logs/report_frontend_manual.pid) ，日志：$ROOT_DIR/logs/report_frontend.log"
fi

echo "全部请求的服务已尝试启动（如适用）。"
echo "API接口:     http://127.0.0.1:8000/status"
echo "运营报告页面: http://127.0.0.1:8080/report"
echo "手动启动的 pid 文件位于 logs/，若由 supervisord/systemd 管理则无需手动脚本。"
