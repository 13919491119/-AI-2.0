#!/bin/bash
# 启动 Celestial Nexus AI 与微信集成服务

# 启动 AI 系统
echo "启动 Celestial Nexus AI 系统..."
nohup python autonomous_run.py > ai_system.log 2>&1 &
sleep 5

# 启动 API 服务
echo "启动 API 服务..."
nohup uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000 > api_server.log 2>&1 &
sleep 5

# 启动微信对接服务
echo "启动微信对接服务..."
export WECHAT_PORT=9090  # 使用9090端口避免冲突
export USE_NGROK=false   # 默认不使用Ngrok，避免认证问题

# 如果用户提供了Ngrok令牌，则启用Ngrok
if [ -n "$NGROK_AUTH_TOKEN" ]; then
  export USE_NGROK=true
  echo "检测到Ngrok令牌，将使用Ngrok创建公网地址"
  
  # 启动微信服务
  nohup python wechat_server.py > wechat_server.log 2>&1 &
  
  # 等待服务启动和Ngrok隧道建立
  sleep 5
  
  # 提取Ngrok URL
  NGROK_URL=$(grep -o 'https://[^"]*' wechat_server.log | tail -1)
  
  if [ -n "$NGROK_URL" ]; then
    echo "Ngrok隧道已建立: ${NGROK_URL}"
    echo "请在微信公众平台配置URL: ${NGROK_URL}/wechat"
    echo "Token: celestial_nexus_ai_token"
  else
    echo "警告: 无法获取Ngrok URL，请检查wechat_server.log"
  fi
else
  echo "未设置Ngrok令牌，将使用本地地址 (http://localhost:9090)"
  echo "要使用Ngrok获取公网地址，请设置令牌: export NGROK_AUTH_TOKEN=your_token"
  
  # 启动微信服务(不使用Ngrok)
  nohup python wechat_server.py > wechat_server.log 2>&1 &
fi

echo "所有服务已启动!"
echo "查看日志: tail -f wechat_server.log"
