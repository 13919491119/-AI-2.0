#!/bin/bash
# 一键启动玄机AI主服务与美化前端报告服务

# 启动FastAPI主服务（API微服务，8000端口）
echo "[1/2] 启动FastAPI主服务..."
nohup uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000 --reload > api_server.log 2>&1 &

# 启动美化前端报告服务（8080端口）
echo "[2/2] 启动美化前端报告服务..."
nohup python3 celestial_nexus/report_frontend.py > report_frontend.log 2>&1 &

echo "全部服务已启动！"
echo "API接口:     http://127.0.0.1:8000/status"
echo "运营报告页面: http://127.0.0.1:8080/report"
