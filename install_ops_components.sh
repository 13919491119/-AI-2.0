#!/bin/bash
set -euo pipefail
# 安装/更新 运维组件脚本
# 功能: 安装依赖 -> 创建 systemd -> (可选) Nginx/Certbot -> Logrotate

if [[ $EUID -ne 0 ]]; then
  echo "[ERR] 请使用 root 或 sudo 运行 (需要写入 /etc/systemd/)" >&2
  exit 1
fi

PROJECT_DIR=${PROJECT_DIR:-/workspaces/-AI-2.0}
SERVICE_FILE=wechat_server.service
API_SERVICE_FILE=celestial_api.service
PY_REQ=${PROJECT_DIR}/requirements.txt

echo "[1/5] 安装 Python 依赖"
python3 -m pip install --upgrade pip
pip install -r "$PY_REQ"

echo "[2/6] 部署 systemd 单元 (WeChat + API)"
install -m 644 "$PROJECT_DIR/$SERVICE_FILE" /etc/systemd/system/$SERVICE_FILE
if [ -f "$PROJECT_DIR/$API_SERVICE_FILE" ]; then
  install -m 644 "$PROJECT_DIR/$API_SERVICE_FILE" /etc/systemd/system/$API_SERVICE_FILE
fi
systemctl daemon-reload
systemctl enable $SERVICE_FILE
if [ -f /etc/systemd/system/$API_SERVICE_FILE ]; then
  systemctl enable $API_SERVICE_FILE
fi

for svc in $SERVICE_FILE $API_SERVICE_FILE; do
  if [[ -f /etc/systemd/system/$svc ]]; then
    if ! systemctl is-active --quiet $svc; then
      systemctl start $svc || true
    fi
    systemctl status --no-pager $svc || true
  fi
done

echo "[3/6] 生成 logrotate 规则"
cat >/etc/logrotate.d/celestial_wechat <<'EOF'
/workspaces/-AI-2.0/wechat_server.out.log /workspaces/-AI-2.0/wechat_server.err.log /workspaces/-AI-2.0/wechat_server.log {
  daily
  rotate 14
  compress
  missingok
  notifempty
  copytruncate
}
EOF

echo "[4/6] (可选) 安装 Nginx (若未安装)"
if ! command -v nginx >/dev/null 2>&1; then
  apt-get update && apt-get install -y nginx
fi

if [[ ! -f /etc/nginx/sites-available/wechat_reverse.conf ]]; then
cat >/etc/nginx/sites-available/wechat_reverse.conf <<'EOF'
server {
  listen 80;
  server_name _;
  # WeChat 接口
  location /wechat {
    proxy_pass http://127.0.0.1:9090/wechat;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
  location /wechat_health { proxy_pass http://127.0.0.1:9090/health; }
  location /wechat_metrics { proxy_pass http://127.0.0.1:9090/metrics; }

  # Celestial API (FastAPI)
  location /api/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
  location /api_metrics { proxy_pass http://127.0.0.1:8000/metrics; }
  location /api_health { proxy_pass http://127.0.0.1:8000/health; }
}
EOF
ln -s /etc/nginx/sites-available/wechat_reverse.conf /etc/nginx/sites-enabled/wechat_reverse.conf 2>/dev/null || true
nginx -t && systemctl restart nginx
fi

echo "[5/6] 生成 requirements-lock.txt (冻结依赖)"
python3 -m pip freeze > ${PROJECT_DIR}/requirements-lock.txt

echo "[6/6] 汇总: systemd(wechat+api) + nginx + logrotate + metrics 已配置"
echo "[DONE] 运维组件安装完成"
