deploy_xuanji_ai.sh
# filepath: /workspaces/-AI-2.0/deploy_xuanji_ai.sh

# 1. 基础环境
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git wkhtmltopdf

# 2. 拉取/更新代码（请替换为你的仓库地址）
if [ ! -d xuanji-ai ]; then
    git clone https://github.com/yourname/xuanji-ai.git
    cd xuanji-ai
else
    cd xuanji-ai
    git pull
fi

# 3. 虚拟环境与依赖
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn requests pydantic openai flask PyGithub matplotlib pandas seaborn markdown pdfkit python-dotenv

# 4. systemd服务配置
SERVICE_FILE=/etc/systemd/system/xuanji_api.service
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=XuanjiAI API Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/.venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. 启动并设置自启动
sudo systemctl daemon-reload
sudo systemctl enable xuanji_api
sudo systemctl restart xuanji_api

echo "✅ 玄机AI系统已部署并自启动，API服务监听8000端口。"
echo "可通过 http://<你的云服务器IP>:8000/docs 访问API文档。"