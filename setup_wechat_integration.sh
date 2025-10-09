#!/bin/bash
# setup_wechat_integration.sh
# 微信集成一键部署脚本 - 自动完成所有配置

echo "🚀 开始微信集成自动化部署..."

# 1. 安装依赖（如果需要）
echo "[1/4] 检查依赖..."
pip3 install fastapi uvicorn requests --quiet 2>/dev/null || echo "依赖已安装"

# 2. 配置环境变量
echo "[2/4] 配置环境变量..."
export WECHAT_TOKEN="${WECHAT_TOKEN:-xuanji_ai_token_2025}"

# 3. 启动微信服务器
echo "[3/4] 启动微信集成服务器..."
nohup python3 wechat_server.py > wechat_server.log 2>&1 &
WECHAT_PID=$!

# 等待服务启动
sleep 2

# 4. 验证服务
echo "[4/4] 验证服务状态..."
if curl -s http://127.0.0.1:8088/health | grep -q "healthy"; then
    echo "✅ 微信集成服务启动成功！"
    echo ""
    echo "📱 微信验证接口: http://127.0.0.1:8088/wechat"
    echo "📊 报告接口: http://127.0.0.1:8088/report"
    echo "🏥 健康检查: http://127.0.0.1:8088/health"
    echo ""
    echo "服务PID: $WECHAT_PID"
    echo "日志文件: wechat_server.log"
else
    echo "❌ 服务启动失败，请检查日志: wechat_server.log"
    exit 1
fi

echo ""
echo "🎉 微信集成部署完成！"
