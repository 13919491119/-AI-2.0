#!/bin/bash
# 一键自动连接微信公众号（无人工交互）
# 逻辑：
# 1) 读取 .env.wechat 环境（若存在），加载APPID/APPSECRET/ENCODING_AES_KEY/WECHAT_TOKEN/NGROK_AUTH_TOKEN/FRP变量等
# 2) 若存在 WECHAT_LINK_PENDING.md 且未设置 FORCE_WECHAT_LINK=1，则自动删除以允许接入
# 3) 优先选择隧道：若 NGROK_AUTH_TOKEN 存在 -> 使用 python wechat_server.py 自启并输出 ngrok URL
#    否则若 FRP_* 变量存在 -> 尝试运行 frp/start_frpc.sh；若不存在则提示
#    否则默认本地 9090 开发模式
# 4) 生产方式启动：start_wechat_gunicorn.sh 后台常驻（若 USE_NGROK=true 则仍仅本地，建议使用pyngrok）
# 5) 运行 system_self_check.sh 验证健康状态；失败将输出日志并退出非零

set -euo pipefail

cd "$(dirname "$0")"

echo "[auto-connect] 启动微信公众号一键连接流程"

# 1) 加载环境变量
if [ -f .env.wechat ]; then
  echo "[auto-connect] 加载 .env.wechat"
  # 按键=值格式导入（忽略注释行）
  export $(grep -E '^[A-Z0-9_]+=' .env.wechat | xargs)
fi
export WECHAT_TOKEN=${WECHAT_TOKEN:-celestial_nexus_ai_token}
export WECHAT_PORT=${WECHAT_PORT:-9090}
export STRICT_WECHAT_VERIFY=${STRICT_WECHAT_VERIFY:-1}
export USE_NGROK=${USE_NGROK:-false}

# 2) 自动解除接入阻塞
if [ -f WECHAT_LINK_PENDING.md ] && [ "${FORCE_WECHAT_LINK:-}" != "1" ]; then
  echo "[auto-connect] 检测到 WECHAT_LINK_PENDING.md，自动删除以允许接入"
  rm -f WECHAT_LINK_PENDING.md || true
fi

# 3) 选择隧道方案（尽量自动化）
PUBLIC_URL=""
if [ -n "${NGROK_AUTH_TOKEN:-}" ]; then
  echo "[auto-connect] 检测到 NGROK_AUTH_TOKEN，使用 pyngrok 为 9090 建立公网隧道"
  /opt/conda/bin/conda run -p /opt/conda --no-capture-output pip show pyngrok >/dev/null 2>&1 || \
    /opt/conda/bin/conda run -p /opt/conda --no-capture-output pip install -q pyngrok
  # 先确保 gunicorn 已启动
  if ! pgrep -f "gunicorn_wechat.conf.py" >/dev/null 2>&1; then
    nohup bash -lc './start_wechat_gunicorn.sh' >> wechat_server.log 2>&1 &
    sleep 3
  fi
  # 后台开启到本地 9090 的隧道，并将 URL 写入文件
  cat > .start_ngrok.py <<PY
from pyngrok import ngrok, conf
import os, time
token = os.environ.get('NGROK_AUTH_TOKEN','')
if token:
  conf.get_default().auth_token = token
region = os.environ.get('NGROK_REGION','')
if region:
  conf.get_default().region = region
# 建立HTTP隧道并启用TLS，从而提供HTTPS(443)地址
tunnel = ngrok.connect(addr=os.environ.get('WECHAT_PORT','9090'), proto='http', bind_tls=True)
# 优先选择HTTPS隧道
url = tunnel.public_url
try:
  tunnels = ngrok.get_tunnels()
  https = [t.public_url for t in tunnels if t.public_url.startswith('https://')]
  if https:
    url = https[0]
except Exception:
  pass
with open('ngrok_url.txt','w') as f:
  f.write(url)
print(url, flush=True)
while True:
  time.sleep(60)
PY
  nohup /opt/conda/bin/conda run -p /opt/conda --no-capture-output python .start_ngrok.py > ngrok.out 2>&1 &
  echo "[auto-connect] 等待ngrok建立隧道..."
  for i in $(seq 1 15); do
    if [ -s ngrok_url.txt ]; then break; fi; sleep 1; done
  PUBLIC_URL="$(cat ngrok_url.txt 2>/dev/null || true)"
  if [ -z "$PUBLIC_URL" ]; then
    echo "[auto-connect][warn] 未抓取到ngrok地址，退回本地URL"
    PUBLIC_URL="http://localhost:${WECHAT_PORT}"
  fi
elif [ -f frp/start_frpc.sh ]; then
  echo "[auto-connect] 检测到 FRP 客户端脚本，尝试启动"
  (cd frp && bash start_frpc.sh >/dev/null 2>&1 &)
  PUBLIC_URL="${PUBLIC_URL:-http://localhost:${WECHAT_PORT}}"
else
  echo "[auto-connect] 未配置隧道，先使用本地模式（仅本地测试可用）"
  PUBLIC_URL="http://localhost:${WECHAT_PORT}"
fi

# 4) 使用 Gunicorn 生产方式常驻（如已在开发服上监听亦可直接通过，但推荐gunicorn）
if ! pgrep -f "gunicorn_wechat.conf.py" >/dev/null 2>&1; then
  echo "[auto-connect] 启动 gunicorn 微信服务"
  nohup bash -lc './start_wechat_gunicorn.sh' >> wechat_server.log 2>&1 &
  sleep 3
fi

# 5) 健康检查与签名验证
echo "[auto-connect] 运行系统自检..."
bash system_self_check.sh || {
  echo "[auto-connect][error] 自检失败，最近日志："
  tail -n 80 wechat_server.log || true
  exit 1
}

echo "[auto-connect] 自检通过，建议在公众号后台配置如下："
echo "URL: ${PUBLIC_URL}/wechat"
echo "Token: ${WECHAT_TOKEN}"
echo "当前端口: ${WECHAT_PORT}"

exit 0
