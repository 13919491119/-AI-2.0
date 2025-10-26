#!/bin/bash
# 微信公众平台服务配置帮助脚本

echo "==============================================="
echo "Celestial Nexus AI 微信公众号集成配置助手"
echo "==============================================="

# 停止现有的服务
echo "停止现有服务..."
pkill -f "python wechat_server.py"
sleep 2

# 启动微信服务
echo "启动微信服务..."
# 检查是否已经设置了环境变量
if [ -z "$NGROK_AUTH_TOKEN" ]; then
    read -p "请输入您的Ngrok认证令牌 (从 https://dashboard.ngrok.com/get-started/your-authtoken 获取): " NGROK_TOKEN
    export NGROK_AUTH_TOKEN="$NGROK_TOKEN"
fi

echo "使用Ngrok令牌: ${NGROK_AUTH_TOKEN:0:5}*****"
python wechat_server.py > wechat_server.log 2>&1 &

# 等待服务启动和Ngrok隧道建立
echo "等待服务启动..."
sleep 10

# 提取Ngrok URL
NGROK_URL=$(grep -o 'https://[^"]*\.ngrok-free\.dev' wechat_server.log | tail -1)

# 检查是否存在Ngrok错误
NGROK_ERROR=$(grep -o 'ERR_NGROK_[0-9]*' wechat_server.log | head -1)

if [ -n "$NGROK_ERROR" ]; then
    echo "错误: Ngrok启动失败，错误代码: $NGROK_ERROR"
    echo "请查看错误详情: https://ngrok.com/docs/errors/$NGROK_ERROR"
    echo ""
    echo "将使用本地URL作为替代..."
    NGROK_URL="http://localhost:9090"
elif [ -z "$NGROK_URL" ]; then
    echo "警告: 无法获取Ngrok URL，将使用本地URL"
    NGROK_URL="http://localhost:9090"
fi

# 显示配置信息
echo ""
echo "==============================================="
echo "微信公众平台配置信息"
echo "==============================================="
echo ""
echo "请在微信公众平台管理后台完成以下配置:"
echo ""
echo "1. 登录微信公众平台管理后台: https://mp.weixin.qq.com/"
echo "2. 进入'设置与开发' > '基本配置' > '服务器配置'"
echo "3. 在'服务器地址(URL)'中填入: ${NGROK_URL}/wechat"
echo "4. 在'令牌(Token)'中填入: celestial_nexus_ai_token"
echo "5. 在'消息加解密方式'中选择: '明文模式'"
echo "6. 点击'提交'按钮"
echo ""
echo "注意: 每次重启服务后，Ngrok的URL会变化，需要重新配置"
echo "==============================================="

# 验证服务是否正常运行
echo ""
echo "验证服务状态..."
echo ""

# 生成一个测试验证请求
TIMESTAMP="$(date +%s)"
NONCE="random$(date +%N)"
ECHOSTR="test$(date +%s)"

# 计算签名
TOKEN="celestial_nexus_ai_token"
STR_TO_SIGN="${TOKEN}${TIMESTAMP}${NONCE}"
SIGNATURE=$(echo -n "$STR_TO_SIGN" | sha1sum | awk '{print $1}')

# 发送测试请求
echo "发送测试验证请求..."
TEST_URL="${NGROK_URL}/wechat?signature=${SIGNATURE}&timestamp=${TIMESTAMP}&nonce=${NONCE}&echostr=${ECHOSTR}"
echo "测试URL: $TEST_URL"

# 使用 -m 选项限制响应大小，避免获取大量HTML
RESPONSE=$(curl -s -m 5 "$TEST_URL" | head -c 100)
if [ "$RESPONSE" == "$ECHOSTR" ]; then
    echo "测试成功! 服务器验证逻辑正常"
    echo ""
    echo "验证通过，请使用以下配置:"
    echo "URL: ${NGROK_URL}/wechat"
    echo "Token: celestial_nexus_ai_token"
else
    echo "测试失败! 服务器响应(截断): ${RESPONSE:0:50}..."
    echo ""
    echo "请检查日志获取更多信息: tail -f wechat_server.log"
fi

echo ""
echo "服务已启动，日志文件: wechat_server.log"
echo "使用 'tail -f wechat_server.log' 查看实时日志"
echo "==============================================="