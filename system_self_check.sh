#!/bin/bash
# 系统自检脚本：检查核心运行、关键端点、配置匹配、指标可访问
set -euo pipefail
BASE_WECHAT=${BASE_WECHAT:-http://127.0.0.1:9090}
BASE_API=${BASE_API:-http://127.0.0.1:8000}
TOKEN=${WECHAT_TOKEN:-celestial_nexus_ai_token}
ORIGINAL_ID_EXPECT=${WECHAT_ORIGINAL_ID:-}
REDIS_URL=${WECHAT_REDIS_URL:-}

pass_count=0; fail_count=0

check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "[PASS] $name"; pass_count=$((pass_count+1))
  else
    echo "[FAIL] $name"; fail_count=$((fail_count+1))
  fi
}

# 1. WeChat 健康
check "WeChat /health" curl -s "$BASE_WECHAT/health"
# 2. API 健康
check "API /health" curl -s "$BASE_API/health"
# 3. 签名计算与验证(GET)（本地）
ts=$(date +%s); nonce=testnonce; sig=$(python - <<PY
import hashlib,os
T=os.environ.get('WECHAT_TOKEN','celestial_nexus_ai_token')
import sys
print(hashlib.sha1(''.join(sorted([T,'$ts','$nonce'])).encode()).hexdigest())
PY
)
resp=$(curl -s "$BASE_WECHAT/wechat?signature=$sig&timestamp=$ts&nonce=$nonce&echostr=ping")
if [ "$resp" = "ping" ]; then echo "[PASS] 签名验证"; pass_count=$((pass_count+1)); else echo "[FAIL] 签名验证"; fail_count=$((fail_count+1)); fi

# 4. 指标可访问
check "WeChat metrics" curl -s "$BASE_WECHAT/metrics"
check "API metrics" curl -s "$BASE_API/metrics"

# 5. 原始ID 检查（如果期望值设置）
if [ -n "$ORIGINAL_ID_EXPECT" ]; then
  oid=$(curl -s "$BASE_WECHAT/health" | grep -o '"original_id":"[^"]*"' | cut -d '"' -f4)
  if [ "$oid" = "$ORIGINAL_ID_EXPECT" ]; then
    echo "[PASS] 原始ID匹配 ($oid)"; pass_count=$((pass_count+1))
  else
    echo "[FAIL] 原始ID不匹配: $oid != $ORIGINAL_ID_EXPECT"; fail_count=$((fail_count+1))
  fi
fi

# 6. Redis 去重检测（如果配置）
if [ -n "$REDIS_URL" ]; then
  python - <<PY >/dev/null 2>&1 && echo "[PASS] Redis 连接" || echo "[FAIL] Redis 连接"
import redis,os
r=redis.Redis.from_url(os.environ['WECHAT_REDIS_URL'])
r.ping()
PY
fi

# 汇总
echo "--- SUMMARY ---"
echo "PASS: $pass_count  FAIL: $fail_count"
if [ $fail_count -gt 0 ]; then exit 1; fi
