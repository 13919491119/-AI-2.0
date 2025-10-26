#!/bin/bash
# Nginx反向代理配置生成器 - 用于Celestial Nexus AI微信集成
# 此脚本生成Nginx反向代理配置文件，用于微信公众号访问

echo "==============================================="
echo "  Celestial Nexus AI - Nginx反向代理配置生成器  "
echo "==============================================="

# 提示用户输入配置信息
echo "请提供以下信息用于配置Nginx反向代理:"
read -p "1. 您的域名 (如: example.com): " DOMAIN
read -p "2. 本地服务器IP地址 (如: 192.168.1.100): " LOCAL_IP
read -p "3. 本地服务端口 (默认: 9090): " LOCAL_PORT
LOCAL_PORT=${LOCAL_PORT:-9090}

read -p "4. 是否配置SSL (HTTPS)? (y/n): " USE_SSL

# 创建配置目录
mkdir -p nginx_config
cd nginx_config

# 创建基本配置
echo "生成Nginx配置文件..."

if [[ "$USE_SSL" == "y" || "$USE_SSL" == "Y" ]]; then
    # 创建HTTPS配置
    cat > celestial-nexus.conf <<EOL
server {
    listen 80;
    server_name ${DOMAIN};
    
    # 将HTTP请求重定向到HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name ${DOMAIN};
    
    # SSL配置
    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    
    # 微信接口路径
    location /wechat {
        proxy_pass http://${LOCAL_IP}:${LOCAL_PORT}/wechat;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 增加超时时间，避免微信验证超时
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
}
EOL

    # 创建Let's Encrypt配置说明
    cat > setup_ssl.sh <<EOL
#!/bin/bash
# 安装Let's Encrypt Certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# 获取并配置SSL证书
sudo certbot --nginx -d ${DOMAIN}

# 测试自动续期
sudo certbot renew --dry-run

echo "SSL证书已配置完成！"
EOL
    chmod +x setup_ssl.sh

    echo ""
    echo "HTTPS配置文件已生成。"
    echo "请将celestial-nexus.conf文件复制到/etc/nginx/sites-available/"
    echo "然后运行:"
    echo "sudo ln -s /etc/nginx/sites-available/celestial-nexus.conf /etc/nginx/sites-enabled/"
    echo "sudo nginx -t"
    echo "sudo systemctl restart nginx"
    echo ""
    echo "要配置SSL证书，请运行:"
    echo "./setup_ssl.sh"
    
else
    # 创建HTTP配置
    cat > celestial-nexus.conf <<EOL
server {
    listen 80;
    server_name ${DOMAIN};
    
    # 微信接口路径
    location /wechat {
        proxy_pass http://${LOCAL_IP}:${LOCAL_PORT}/wechat;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 增加超时时间，避免微信验证超时
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
}
EOL

    echo ""
    echo "HTTP配置文件已生成。"
    echo "请将celestial-nexus.conf文件复制到/etc/nginx/sites-available/"
    echo "然后运行:"
    echo "sudo ln -s /etc/nginx/sites-available/celestial-nexus.conf /etc/nginx/sites-enabled/"
    echo "sudo nginx -t"
    echo "sudo systemctl restart nginx"
    echo ""
    echo "注意: 微信官方建议使用HTTPS，建议您考虑配置SSL"
fi

# 创建安装说明
cat > install_nginx.sh <<EOL
#!/bin/bash
# 安装Nginx
sudo apt-get update
sudo apt-get install -y nginx

# 配置防火墙
sudo ufw allow 'Nginx Full'

# 检查Nginx状态
sudo systemctl status nginx
EOL
chmod +x install_nginx.sh

# 提示微信配置信息
echo ""
echo "==============================================="
echo "微信公众平台配置信息"
echo "==============================================="
echo ""
echo "请在微信公众平台配置以下信息:"
if [[ "$USE_SSL" == "y" || "$USE_SSL" == "Y" ]]; then
    echo "URL: https://${DOMAIN}/wechat"
else
    echo "URL: http://${DOMAIN}/wechat"
fi
echo "Token: celestial_nexus_ai_token"
echo ""
echo "请确保您的本地微信集成服务已启动:"
echo "./local_wechat_integration.sh"
echo ""
echo "==============================================="
echo "配置文件生成完成!"
echo "==============================================="