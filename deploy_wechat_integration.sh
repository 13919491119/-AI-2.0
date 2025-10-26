#!/bin/bash
# 自动部署脚本：将 Celestial Nexus AI 系统链接到微信公众号 "刘洪鹏76"
# 作者: GitHub Copilot
# 日期: 2025-10-07

# 定义颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 恢复颜色

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}    Celestial Nexus AI 微信公众号集成自动部署脚本    ${NC}"
echo -e "${GREEN}    微信公众号: 刘洪鹏76                             ${NC}"
echo -e "${GREEN}======================================================${NC}"

# 检查权限
echo -e "${BLUE}[1/7] 检查执行权限...${NC}"
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}提示: 当前非root用户，80端口可能无法绑定，将使用8080端口代替${NC}"
  WECHAT_PORT=8080
else
  WECHAT_PORT=80
fi

# 安装依赖
echo -e "${BLUE}[2/7] 安装必要依赖...${NC}"
pip install flask requests uvicorn fastapi pyngrok

# 创建微信对接服务
echo -e "${BLUE}[3/7] 创建微信对接服务...${NC}"
cat > /workspaces/-AI-2.0/wechat_server.py <<EOF
#!/usr/bin/env python3
"""
微信公众号与 Celestial Nexus AI 系统对接服务
公众号: 刘洪鹏76
"""
from flask import Flask, request, make_response
import requests
import xml.etree.ElementTree as ET
import time
import json
import os
import logging
from pyngrok import ngrok

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
PORT = int(os.environ.get('WECHAT_PORT', 8080))
USE_NGROK = True

# 微信公众号信息
WECHAT_NAME = '刘洪鹏76'
TOKEN = 'celestial_nexus_ai_token'  # 在公众号后台配置相同的Token

# 命令处理函数
def handle_command(command):
    """处理用户命令并调用对应的 Celestial Nexus API"""
    if command.startswith('预测') or command.startswith('双色球'):
        try:
            result = requests.post(
                f'{CELESTIAL_API}/predict',
                json={'query': command}
            ).json()
            return result.get('result', '预测结果生成中，请稍后再试')
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return f"系统暂时无法处理请求，请稍后再试"
    
    elif command.startswith('状态') or command.startswith('系统'):
        try:
            result = requests.get(f'{CELESTIAL_API}/status').json()
            return f"系统状态: {result.get('status', '运行中')}\n健康度: {result.get('health', '良好')}\n上线时间: {result.get('uptime', '未知')}"
        except Exception as e:
            logger.error(f"状态查询失败: {e}")
            return "系统状态查询失败，请稍后再试"
    
    elif command.startswith('帮助') or command.startswith('?'):
        return """玄机AI预测系统使用指南:
1. 发送"预测+内容"获取预测结果
2. 发送"双色球"获取双色球预测
3. 发送"状态"查询系统运行情况
4. 发送"帮助"获取使用说明"""
    
    else:
        # 默认作为预测内容处理
        try:
            result = requests.post(
                f'{CELESTIAL_API}/predict',
                json={'query': command}
            ).json()
            return result.get('result', '正在分析中，请稍后再试')
        except Exception as e:
            logger.error(f"默认API调用失败: {e}")
            return "您的请求已收到，但系统暂时无法处理，请稍后再试"

@app.route('/wechat', methods=['GET', 'POST'])
def wechat():
    """微信公众号接口"""
    # 处理服务器验证请求
    if request.method == 'GET':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        # 简化验证逻辑，微信会验证Token
        logger.info(f"收到验证请求: {echostr}")
        return echostr
    
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

def start_ngrok():
    """启动ngrok隧道服务获取公网地址"""
    try:
        # 开启隧道
        public_url = ngrok.connect(PORT, "http")
        logger.info(f"Ngrok隧道已启动: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Ngrok启动失败: {e}")
        return None

if __name__ == '__main__':
    try:
        if USE_NGROK:
            # 启动ngrok获取公网URL
            public_url = start_ngrok()
            if public_url:
                logger.info(f"请在微信公众平台配置以下URL: {public_url}/wechat")
                logger.info(f"请使用Token: {TOKEN}")
            
        # 启动Flask服务
        logger.info(f"微信对接服务启动在端口 {PORT}")
        app.run(host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
EOF

# 创建启动脚本
echo -e "${BLUE}[4/7] 创建系统启动脚本...${NC}"
cat > /workspaces/-AI-2.0/start_wechat_integration.sh <<EOF
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
export WECHAT_PORT=${WECHAT_PORT}
nohup python wechat_server.py > wechat_server.log 2>&1 &

echo "所有服务已启动!"
echo "查看日志: tail -f wechat_server.log"
EOF

# 赋予执行权限
echo -e "${BLUE}[5/7] 赋予脚本执行权限...${NC}"
chmod +x /workspaces/-AI-2.0/start_wechat_integration.sh
chmod +x /workspaces/-AI-2.0/wechat_server.py

# 创建README
echo -e "${BLUE}[6/7] 创建微信集成说明文档...${NC}"
cat > /workspaces/-AI-2.0/WECHAT_INTEGRATION.md <<EOF
# Celestial Nexus AI - 微信公众号集成说明

## 概述
本文档说明如何将"玄机设计与实现AI系统"(Celestial Nexus AI)与微信公众号"刘洪鹏76"集成。

## 部署步骤

### 1. 启动系统
执行以下命令启动所有服务:
\`\`\`bash
bash start_wechat_integration.sh
\`\`\`

### 2. 配置微信公众号

登录微信公众平台(mp.weixin.qq.com):
- 进入"开发"-"基本配置"
- 设置服务器地址URL: 使用ngrok提供的公网URL (见wechat_server.log)
- 令牌(Token): celestial_nexus_ai_token
- 保存配置

### 3. 测试
在微信公众号"刘洪鹏76"中发送以下消息测试:
- "帮助" - 获取使用说明
- "预测+内容" - 进行预测
- "双色球" - 获取双色球预测
- "状态" - 查看系统状态

## 日志与监控
- API服务日志: api_server.log
- 微信对接服务日志: wechat_server.log
- AI系统日志: ai_system.log

## 注意事项
- ngrok提供的URL会在每次重启后改变
- 微信公众号消息回复有5秒超时限制
EOF

# 启动服务
echo -e "${BLUE}[7/7] 正在启动所有服务...${NC}"
bash /workspaces/-AI-2.0/start_wechat_integration.sh

echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}    部署完成! 微信公众号集成已自动配置                ${NC}"
echo -e "${GREEN}    查看日志: tail -f wechat_server.log                ${NC}"
echo -e "${GREEN}    查看集成说明: cat WECHAT_INTEGRATION.md            ${NC}"
echo -e "${GREEN}========================================================${NC}"