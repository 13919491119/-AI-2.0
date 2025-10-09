#!/bin/bash
# 本地模式微信集成配置脚本 - 不依赖Ngrok
# 适用于有公网IP或自行配置反向代理的情况

echo "==============================================="
echo "Celestial Nexus AI 微信公众号集成 (本地模式)"
echo "==============================================="

# 停止现有的服务
echo "停止现有服务..."
pkill -f "python wechat_server.py"
sleep 2

# 配置环境变量
export USE_NGROK=false
export WECHAT_PORT=9090

# 启动微信服务
echo "启动微信服务..."
python wechat_server.py > wechat_server.log 2>&1 &

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 获取本机IP地址
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "==============================================="
echo "微信公众平台配置信息 (本地模式)"
echo "==============================================="
echo ""
echo "服务已在本地端口9090上启动"
echo ""
echo "本地测试URL: http://localhost:9090/wechat"
echo "本机IP测试URL: http://${LOCAL_IP}:9090/wechat"
echo ""
echo "重要说明:"
echo "1. 微信公众平台要求服务器有公网可访问的URL"
echo "2. 本地模式需要您自行配置反向代理或端口转发"
echo "3. 确保端口9090已在防火墙中开放"
echo ""
echo "可选配置方案:"
echo "1. 使用内网穿透工具(Frp/Ngrok等)映射到公网"
echo "2. 使用云服务器反向代理到本机"
echo "3. 配置公网IP和域名直接指向本服务器"
echo ""
echo "本地模式验证方法:"
echo "curl \"http://localhost:9090/wechat?signature=test&timestamp=123&nonce=test&echostr=test\""
echo ""
echo "Token: celestial_nexus_ai_token"
echo "==============================================="
echo ""
echo "日志文件: wechat_server.log"
echo "使用 'tail -f wechat_server.log' 查看实时日志"