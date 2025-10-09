#!/bin/bash
# 一键启动玄机AI主服务与美化前端报告服务

# 启动FastAPI主服务（API微服务，8000端口）
echo "[1/5] 启动FastAPI主服务..."
nohup uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000 --reload > api_server.log 2>&1 &

# 启动美化前端报告服务（8080端口）
echo "[2/5] 启动美化前端报告服务..."
nohup python3 celestial_nexus/report_frontend.py > report_frontend.log 2>&1 &

# 启动微信集成服务（8088端口）
echo "[3/5] 启动微信集成服务..."
nohup python3 wechat_server.py > wechat_server.log 2>&1 &

# 启动静态报告服务器（8089端口）
echo "[4/5] 启动静态报告服务器..."
nohup python3 static_report_server.py > static_report_server.log 2>&1 &

# 等待服务启动
sleep 2

# 系统自检
echo "[5/5] 执行系统自检..."
python3 system_check.py

echo ""
echo "✅ 全部服务已启动！"
echo ""
echo "📡 API接口:        http://127.0.0.1:8000/status"
echo "📊 运营报告页面:    http://127.0.0.1:8080/report"
echo "📱 微信集成接口:    http://127.0.0.1:8088/report"
echo "🌐 静态报告中心:    http://127.0.0.1:8089"
