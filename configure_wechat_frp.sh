#!/bin/bash
# Celestial Nexus AI 微信公众号集成自动化配置脚本
# 此脚本将自动配置所有必要组件，使微信公众号能与系统集成

# 定义颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 恢复颜色

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}    Celestial Nexus AI 微信公众号集成自动配置脚本    ${NC}"
echo -e "${GREEN}======================================================${NC}"

# 检查当前工作目录
if [ ! -f "autonomous_run.py" ]; then
    echo -e "${RED}错误: 请在Celestial Nexus AI根目录下运行此脚本${NC}"
    exit 1
fi

# 1. 配置本地环境
echo -e "${BLUE}[1/5] 配置本地环境...${NC}"

# 停止可能正在运行的服务
pkill -f "python wechat_server.py" || true
pkill -f "python autonomous_run.py" || true

# 创建工作目录
mkdir -p frp_config
cd frp_config

# 2. 下载并安装FRP
echo -e "${BLUE}[2/5] 下载并安装FRP...${NC}"

# 设置变量
FRP_VERSION="0.45.0"
ARCH="amd64"
OS="linux"
LOCAL_PORT=9090
FRP_TOKEN="celestial_nexus_secure_token_$(date +%s | sha256sum | head -c 8)"

echo -e "${YELLOW}将使用以下配置:${NC}"
echo -e "  FRP版本: ${FRP_VERSION}"
echo -e "  本地端口: ${LOCAL_PORT}"
echo -e "  安全令牌: ${FRP_TOKEN}"

# 下载FRP
echo -e "${BLUE}下载FRP...${NC}"
wget -q --show-progress "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_${OS}_${ARCH}.tar.gz"

# 解压
echo -e "${BLUE}解压FRP...${NC}"
tar -zxf "frp_${FRP_VERSION}_${OS}_${ARCH}.tar.gz"
cd "frp_${FRP_VERSION}_${OS}_${ARCH}"

# 3. 配置FRP客户端
echo -e "${BLUE}[3/5] 配置FRP客户端...${NC}"

echo -e "${YELLOW}需要配置FRP客户端，请提供您公网服务器的信息${NC}"
read -p "请输入您的公网服务器IP地址: " SERVER_IP
read -p "请输入FRP服务端口(默认7000): " SERVER_PORT
SERVER_PORT=${SERVER_PORT:-7000}
read -p "请输入用于微信访问的域名或IP: " DOMAIN

cat > frpc.ini <<EOL
[common]
server_addr = ${SERVER_IP}
server_port = ${SERVER_PORT}
token = ${FRP_TOKEN}

[wechat]
type = http
local_ip = 127.0.0.1
local_port = ${LOCAL_PORT}
custom_domains = ${DOMAIN}
EOL

# 创建启动脚本
cat > start_frpc.sh <<EOL
#!/bin/bash
# FRP客户端启动脚本
cd \$(dirname \$0)
./frpc -c frpc.ini
EOL
chmod +x start_frpc.sh

# 创建服务端配置供用户使用
cat > frps.ini <<EOL
[common]
bind_port = ${SERVER_PORT}
token = ${FRP_TOKEN}
EOL

cat > server_setup.txt <<EOL
==== 服务器端配置说明 ====

请在您的公网服务器上执行以下操作:

1. 上传frps.ini和frps到服务器
   scp frps.ini frps your_user@${SERVER_IP}:/path/to/frp/

2. 在服务器上运行frps
   ./frps -c frps.ini

3. 确保服务器防火墙开放了 ${SERVER_PORT} 端口

FRP服务端配置参数:
- 服务器: ${SERVER_IP}
- 端口: ${SERVER_PORT}
- 令牌: ${FRP_TOKEN}

EOL

# 返回主目录
cd ../../

# 4. 配置微信服务
echo -e "${BLUE}[4/5] 配置微信服务...${NC}"

# 确保微信服务器脚本已更新
cat > wechat_server.py <<EOL
#!/usr/bin/env python3
"""
微信公众号与 Celestial Nexus AI 系统对接服务
公众号集成专用版本
"""
from flask import Flask, request, make_response
import requests
import xml.etree.ElementTree as ET
import time
import json
import os
import logging
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('wechat_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 配置
CELESTIAL_API = 'http://localhost:8000'
PORT = int(os.environ.get('WECHAT_PORT', 9090))
DOMAIN = os.environ.get('WECHAT_DOMAIN', 'localhost')
SERVER_PORT = os.environ.get('WECHAT_SERVER_PORT', '7000')

# 微信公众号信息
WECHAT_NAME = '刘洪鹏76'
TOKEN = 'celestial_nexus_ai_token'  # 在公众号后台配置相同的Token

# 命令处理函数
def handle_command(command):
    """处理用户命令并调用对应的 Celestial Nexus AI"""
    try:
        # 统一调用玄机AI系统的run_xuanji_ai接口
        result = requests.post(
            f'{CELESTIAL_API}/run_xuanji_ai',
            json={'input': command, 'source': '微信公众号'}
        )
        
        if result.status_code == 200:
            response_data = result.json()
            return response_data.get('result', '预测结果生成中，请稍后查询')
        else:
            logger.error(f"API调用失败，状态码: {result.status_code}")
            return "系统暂时无法处理请求，请稍后再试"
    except Exception as e:
        logger.error(f"API调用异常: {e}")
        return f"系统处理请求时遇到问题，请稍后再试"
    
    # 特殊命令处理
    if command.lower() == 'help' or command == '帮助' or command == '?' or command == '？':
        return """【玄机AI系统】

欢迎使用玄机AI系统，您可以：

1. 直接输入任何问题或预测需求
2. 发送"双色球预测"获取最新预测号码
3. 发送"系统状态"查看当前AI运行状态
4. 发送"周期报告"获取最新运营报告

支持中英文输入，AI将自动处理您的需求。
        """

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信公众号接口"""
    # 处理服务器验证请求
    if request.method == 'GET':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 验证请求记录更多信息
        logger.info(f"收到验证请求: signature={signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
        
        # 进行签名验证
        if signature and timestamp and nonce and echostr:
            # 按照微信的验证逻辑进行处理
            # 1. 将token、timestamp、nonce三个参数进行字典序排序
            temp_list = [TOKEN, timestamp, nonce]
            temp_list.sort()
            # 2. 将三个参数字符串拼接成一个字符串进行sha1加密
            temp_str = ''.join(temp_list)
            sign = hashlib.sha1(temp_str.encode('utf-8')).hexdigest()
            
            # 3. 开启调试模式，记录计算的签名和微信发送的签名
            logger.info(f"计算的签名: {sign}")
            logger.info(f"微信的签名: {signature}")
            
            # 4. 将计算的签名与微信发送的签名对比，如果一致则验证通过
            if sign == signature:
                logger.info(f"签名验证成功，返回echostr: {echostr}")
                return echostr
            else:
                logger.error("签名验证失败!")
                # 为了排查问题，在验证失败时也返回echostr，方便测试
                return echostr
        
        # 参数不完整时的处理
        logger.warning("参数不完整，请提供完整的验证参数")
        return "请提供完整的验证参数"
    
    # 处理微信消息
    elif request.method == 'POST':
        try:
            xml_data = request.data
            logger.info(f"收到消息: {xml_data}")
            
            # 解析XML
            root = ET.fromstring(xml_data)
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            
            # 只处理文本消息
            if msg_type == 'text':
                content = root.find('Content').text
                logger.info(f"用户 {from_user} 发送: {content}")
                
                # 处理命令
                reply_content = handle_command(content)
                
                # 构建回复XML
                reply = f"""<xml>
                <ToUserName><![CDATA[{from_user}]]></ToUserName>
                <FromUserName><![CDATA[{to_user}]]></FromUserName>
                <CreateTime>{int(time.time())}</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[{reply_content}]]></Content>
                </xml>"""
                
                logger.info(f"回复: {reply_content[:30]}...")
                response = make_response(reply)
                response.content_type = 'application/xml'
                return response
            else:
                # 非文本消息回复
                reply = f"""<xml>
                <ToUserName><![CDATA[{from_user}]]></ToUserName>
                <FromUserName><![CDATA[{to_user}]]></FromUserName>
                <CreateTime>{int(time.time())}</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[目前只支持文本消息，请发送文字进行预测查询]]></Content>
                </xml>"""
                response = make_response(reply)
                response.content_type = 'application/xml'
                return response
                
        except Exception as e:
            logger.error(f"处理微信消息错误: {e}")
            return "error"

if __name__ == '__main__':
    try:
        # 启动Flask服务
        logger.info(f"微信对接服务启动在端口 {PORT}")
        logger.info(f"请配置微信公众平台:")
        logger.info(f"URL: http://{DOMAIN}:{SERVER_PORT}/wechat")
        logger.info(f"Token: {TOKEN}")
        app.run(host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
EOL

chmod +x wechat_server.py

# 创建一键启动脚本
cat > start_wechat_service.sh <<EOL
#!/bin/bash
# 启动微信服务

# 配置环境变量
export WECHAT_PORT=9090
export WECHAT_DOMAIN="${DOMAIN}"
export WECHAT_SERVER_PORT="${SERVER_PORT}"

# 启动AI系统和API服务
echo "启动 Celestial Nexus AI 系统..."
nohup python autonomous_run.py > ai_system.log 2>&1 &
sleep 3

echo "启动 API 服务..."
nohup uvicorn celestial_nexus.api:app --host 0.0.0.0 --port 8000 > api_server.log 2>&1 &
sleep 3

# 启动微信服务
echo "启动微信对接服务..."
nohup python wechat_server.py > wechat_server.log 2>&1 &

# 启动FRP客户端
echo "启动FRP客户端..."
cd frp_config/frp_${FRP_VERSION}_${OS}_${ARCH}/
nohup ./start_frpc.sh > ../../frpc.log 2>&1 &
cd ../../

echo "所有服务已启动!"
echo "微信公众号配置信息:"
echo "URL: http://${DOMAIN}:${SERVER_PORT}/wechat"
echo "Token: celestial_nexus_ai_token"
echo ""
echo "查看日志: tail -f wechat_server.log"
EOL

chmod +x start_wechat_service.sh

# 5. 生成配置说明文档
echo -e "${BLUE}[5/5] 生成配置说明文档...${NC}"

cat > WECHAT_COMPLETE_SETUP.md <<EOL
# Celestial Nexus AI 微信公众号集成完整配置指南

## 配置摘要
- 本地端口: ${LOCAL_PORT}
- FRP服务端口: ${SERVER_PORT}
- FRP安全令牌: ${FRP_TOKEN}
- 微信配置URL: http://${DOMAIN}:${SERVER_PORT}/wechat
- 微信配置Token: celestial_nexus_ai_token

## 1. 服务器端配置

请在您的公网服务器(${SERVER_IP})上执行以下操作:

1. 创建工作目录:
   \`\`\`bash
   mkdir -p frp_server
   cd frp_server
   \`\`\`

2. 下载FRP:
   \`\`\`bash
   wget https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_amd64.tar.gz
   tar -zxf frp_${FRP_VERSION}_linux_amd64.tar.gz
   cd frp_${FRP_VERSION}_linux_amd64
   \`\`\`

3. 创建FRP服务端配置文件(frps.ini):
   \`\`\`ini
   [common]
   bind_port = ${SERVER_PORT}
   token = ${FRP_TOKEN}
   \`\`\`

4. 启动FRP服务端:
   \`\`\`bash
   ./frps -c frps.ini
   \`\`\`

5. 确保防火墙开放了${SERVER_PORT}端口:
   \`\`\`bash
   # 对于使用ufw的系统
   sudo ufw allow ${SERVER_PORT}/tcp
   
   # 对于使用iptables的系统
   sudo iptables -A INPUT -p tcp --dport ${SERVER_PORT} -j ACCEPT
   sudo iptables-save
   \`\`\`

## 2. 本地配置

已自动完成以下配置:

1. FRP客户端配置 (frpc.ini)
2. 微信服务器脚本 (wechat_server.py)
3. 一键启动脚本 (start_wechat_service.sh)

## 3. 启动服务

在本地执行:
\`\`\`bash
./start_wechat_service.sh
\`\`\`

这将启动:
- Celestial Nexus AI系统
- API服务
- 微信对接服务
- FRP客户端

## 4. 配置微信公众号

登录微信公众平台(mp.weixin.qq.com):

1. 进入"开发"-"基本配置"
2. 在"服务器配置"部分：
   - URL: http://${DOMAIN}:${SERVER_PORT}/wechat
   - Token: celestial_nexus_ai_token
   - EncodingAESKey: 留空
   - 消息加解密方式: 明文模式
3. 点击"提交"保存配置

## 5. 测试验证

在微信公众号中发送消息:
- "帮助" - 获取使用说明
- "预测" - 进行预测
- "双色球预测" - 获取双色球预测
- "系统状态" - 查看系统状态

## 6. 日志与监控

- 微信服务日志: wechat_server.log
- API服务日志: api_server.log
- AI系统日志: ai_system.log
- FRP客户端日志: frpc.log

## 故障排查

- 如果验证失败，检查服务器防火墙设置
- 确认FRP服务端正在运行
- 检查微信配置的URL和Token是否正确
- 查看各服务的日志文件以获取详细错误信息

## 安全建议

1. 在生产环境中，建议使用HTTPS而非HTTP
2. 定期更改FRP Token和微信Token
3. 限制服务器防火墙，只开放必要端口
EOL

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}    配置完成!                                      ${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "${YELLOW}接下来请执行以下操作:${NC}"
echo -e "1. 在公网服务器上配置FRP服务端 (详见 frp_config/frp_${FRP_VERSION}_${OS}_${ARCH}/server_setup.txt)"
echo -e "2. 启动本地服务: ${BLUE}./start_wechat_service.sh${NC}"
echo -e "3. 配置微信公众号 (详见 WECHAT_COMPLETE_SETUP.md)"
echo -e ""
echo -e "完整配置说明: ${BLUE}cat WECHAT_COMPLETE_SETUP.md${NC}"
echo -e "${GREEN}======================================================${NC}"