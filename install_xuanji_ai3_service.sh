#!/bin/bash
# 启动 玄机AI3.0 systemd 服务
SERVICE_FILE="/workspaces/-AI-2.0/xuanji_ai3.service"
TARGET="/etc/systemd/system/xuanji_ai3.service"

if [ $EUID -ne 0 ]; then
  echo "请用sudo运行此脚本：sudo bash install_xuanji_ai3_service.sh"
  exit 1
fi

cp "$SERVICE_FILE" "$TARGET"
systemctl daemon-reload
systemctl enable xuanji_ai3.service
systemctl start xuanji_ai3.service
systemctl status xuanji_ai3.service --no-pager
