#!/bin/bash
# 一键本地签名验证脚本
BASE=${1:-http://127.0.0.1:9090}
TOKEN=${WECHAT_TOKEN:-celestial_nexus_ai_token}
TS=$(date +%s)
NONCE=testnonce
SIG=$(python - <<PY
import hashlib,os
TOKEN=os.environ.get('WECHAT_TOKEN','celestial_nexus_ai_token')
import sys
print(hashlib.sha1(''.join(sorted([TOKEN,'${TS}','${NONCE}'])).encode()).hexdigest())
PY
)
ECHO=verify_ok
URL="${BASE}/wechat?signature=${SIG}&timestamp=${TS}&nonce=${NONCE}&echostr=${ECHO}"
echo "[VERIFY] GET $URL"
RESP=$(curl -s -m 5 "$URL")
if [ "$RESP" = "$ECHO" ]; then
  echo "[PASS] 签名与服务端匹配，返回: $RESP"
  exit 0
else
  echo "[FAIL] 期望=$ECHO 实际=$RESP"
  exit 1
fi
