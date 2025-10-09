#!/bin/bash
# FRP配置助手脚本 - 用于Celestial Nexus AI微信集成
# 此脚本帮助配置FRP内网穿透，使微信可以访问本地服务

echo "==============================================="
echo "  Celestial Nexus AI - FRP内网穿透配置助手  "
echo "==============================================="

# 检查是否已安装FRP
if ! command -v wget &> /dev/null; then
    echo "错误: 未安装wget，请先安装: sudo apt install wget"
    exit 1
fi

# 设置变量
FRP_VERSION="0.45.0"
ARCH="amd64"
LOCAL_PORT=9090
SERVER_PORT=7000

# 获取操作系统类型
OS="linux"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="darwin"
elif [[ "$OSTYPE" == "msys" ]]; then
    OS="windows"
fi

echo "检测到操作系统: $OS"
echo ""

# 提示用户输入配置信息
echo "请提供以下信息用于配置FRP:"
read -p "1. 公网服务器IP地址: " SERVER_IP
read -p "2. FRP通信认证令牌 (自定义安全字符串): " FRP_TOKEN
read -p "3. 您的域名或服务器IP (用于微信访问): " DOMAIN
read -p "4. 是否为服务器端配置? (y/n): " IS_SERVER

# 创建目录
mkdir -p frp
cd frp

# 下载FRP
echo ""
echo "下载FRP $FRP_VERSION..."
wget -q --show-progress "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_${OS}_${ARCH}.tar.gz"

# 解压
echo "解压FRP..."
tar -zxf "frp_${FRP_VERSION}_${OS}_${ARCH}.tar.gz"
cd "frp_${FRP_VERSION}_${OS}_${ARCH}"

# 根据角色配置
if [[ "$IS_SERVER" == "y" || "$IS_SERVER" == "Y" ]]; then
    # 服务器端配置
    echo ""
    echo "配置FRP服务端(frps)..."
    
    cat > frps.ini <<EOL
[common]
bind_port = ${SERVER_PORT}
token = ${FRP_TOKEN}
EOL

    echo ""
    echo "FRP服务端配置完成。您可以使用以下命令启动服务:"
    echo "./frps -c frps.ini"
    
    echo ""
    echo "提示: 请确保您的防火墙开放了${SERVER_PORT}端口"
    
    # 创建启动脚本
    cat > start_frps.sh <<EOL
#!/bin/bash
./frps -c frps.ini
EOL
    chmod +x start_frps.sh
    
    echo "创建了启动脚本: start_frps.sh"
    
else
    # 客户端配置
    echo ""
    echo "配置FRP客户端(frpc)..."
    
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

    echo ""
    echo "FRP客户端配置完成。您可以使用以下命令启动客户端:"
    echo "./frpc -c frpc.ini"
    
    # 创建启动脚本
    cat > start_frpc.sh <<EOL
#!/bin/bash
./frpc -c frpc.ini
EOL
    chmod +x start_frpc.sh
    
    echo "创建了启动脚本: start_frpc.sh"
    
    # 提示微信配置信息
    echo ""
    echo "==============================================="
    echo "微信公众平台配置信息"
    echo "==============================================="
    echo ""
    echo "请在微信公众平台配置以下信息:"
    echo "URL: http://${DOMAIN}:${SERVER_PORT}/wechat"
    echo "Token: celestial_nexus_ai_token"
    echo ""
    echo "提示: 请先确保FRP服务端已启动，且本地微信集成服务已启动"
    echo "启动本地微信集成服务: ./local_wechat_integration.sh"
fi

cd ../../

echo ""
echo "==============================================="
echo "配置完成!"
echo "==============================================="