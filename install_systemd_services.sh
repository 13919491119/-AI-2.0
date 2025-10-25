#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "[warn] systemctl 不可用（容器或非 systemd 环境），可改用 tools/guard_loops.sh 守护。" >&2
  exit 1
fi

UNIT_DIR="/etc/systemd/system"
sudo cp -f systemd/xuanji-autonomous.service "$UNIT_DIR/"
sudo cp -f systemd/xuanji-person.service "$UNIT_DIR/"

# 可选环境变量配置文件
if [ ! -f /etc/default/xuanji-ai ]; then
  sudo bash -lc 'cat >/etc/default/xuanji-ai <<EOF
# 覆盖闭环参数
SSQ_CONSULT_EXTERNAL=1
SSQ_CYCLE_INTERVAL_SECONDS=600
# 取消尝试上限（0 或负数为不限），改用按时间控制
SSQ_MAX_ATTEMPTS_PER_ISSUE=0
# 单期时间上限（秒），建议 3~10 之间按资源调整
SSQ_MAX_SECONDS_PER_ISSUE=5
# Deepseek 等密钥（请替换为真实值）
DEEPSEEK_API_KEY=
EOF'
fi

sudo systemctl daemon-reload
sudo systemctl enable xuanji-autonomous.service xuanji-person.service
sudo systemctl restart xuanji-autonomous.service xuanji-person.service
sudo systemctl --no-pager --full status xuanji-autonomous.service xuanji-person.service | cat

echo "[ok] systemd 服务已安装并启动。可使用：sudo journalctl -u xuanji-autonomous -f"
