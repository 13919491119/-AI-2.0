workspaces/-AI-2.0/self_heal_xuanji.sh
#!/bin/bash
# filepath: /workspaces/-AI-2.0/self_heal_xuanji.sh

set -e

# 1. 检查用户名
USER_NAME=$(whoami)
PROJECT_DIR="/workspaces/-AI-2.0"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python3"

# 2. 检查并修正主循环 systemd 服务文件
MAIN_SERVICE="/etc/systemd/system/xuanji_main.service"
cat > /tmp/xuanji_main.service <<EOF
[Unit]
Description=XuanjiAI Main Loop
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON xuanji_ai_main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo mv /tmp/xuanji_main.service $MAIN_SERVICE

# 3. 检查并修正 API systemd 服务文件
API_SERVICE="/etc/systemd/system/xuanji_api.service"
cat > /tmp/xuanji_api.service <<EOF
[Unit]
Description=XuanjiAI API Service
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo mv /tmp/xuanji_api.service $API_SERVICE

# 4. 检查依赖环境
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn requests pydantic openai flask PyGithub matplotlib pandas seaborn markdown pdfkit python-dotenv

# 5. 重新加载 systemd 并启动服务
sudo systemctl daemon-reload
sudo systemctl enable xuanji_main
sudo systemctl restart xuanji_main
sudo systemctl enable xuanji_api
sudo systemctl restart xuanji_api

# 6. 检查服务状态
echo "==== 主循环服务状态 ===="
sudo systemctl status xuanji_main --no-pager
echo "==== API服务状态 ===="
sudo systemctl status xuanji_api --no-pager

# 7. 检查API端口监听
echo "==== 端口监听情况 ===="
netstat -tnlp | grep 8000 || echo "API端口未监听，请检查api_server.py是否正常"

# 8. 提示API文档访问方式
echo "如需在主机浏览器查看API文档，可运行："
echo '$BROWSER http://localhost:8000/docs'