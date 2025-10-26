#!/bin/bash
set -euo pipefail
# 使用 certbot 为 Nginx 获取并自动续期证书
# 需: 已解析域名指向本机公网IP
# 用法: ./setup_https_certbot.sh domain.com admin@example.com

domain=${1:-}
email=${2:-}
if [[ -z "$domain" || -z "$email" ]]; then
  echo "用法: $0 <domain> <email>" >&2
  exit 1
fi

if ! command -v nginx >/dev/null 2>&1; then
  echo "[ERR] 需要先安装 Nginx" >&2
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  apt-get update && apt-get install -y certbot python3-certbot-nginx
fi

# 基础 HTTP server 块 (若不存在)
CONF=/etc/nginx/sites-available/wechat_reverse.conf
if ! grep -q "server_name" "$CONF"; then
  sed -i "s/server_name _;/server_name ${domain};/" "$CONF"
else
  sed -i "s/server_name .*/server_name ${domain};/" "$CONF"
fi

nginx -t && systemctl reload nginx

echo "[INFO] 申请证书: $domain"
certbot --nginx -d "$domain" --email "$email" --agree-tos --no-eff-email

echo "[INFO] 完成。证书路径: /etc/letsencrypt/live/${domain}/fullchain.pem"
