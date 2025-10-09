#!/bin/bash
set -euo pipefail
KEY=${1:-}
APPID=${2:-}
if [ -z "$KEY" ] || [ -z "$APPID" ]; then
  echo "用法: $0 <43位AESKey> <AppID>"
  exit 1
fi
if [ ${#KEY} -ne 43 ]; then
  echo "[ERR] AES Key 长度必须为43" >&2
  exit 2
fi
echo "WECHAT_ENCODING_AES_KEY=$KEY" > .env.wechat
echo "WECHAT_APPID=$APPID" >> .env.wechat
echo "[OK] 已写入 .env.wechat，重新启动微信服务以生效"
