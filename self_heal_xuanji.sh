#!/bin/bash
# filepath: /workspaces/-AI-2.0/self_heal_xuanji.sh

set -e

PROJECT_DIR="/workspaces/-AI-2.0"
VENV_DIR="$PROJECT_DIR/.venv"

# 1. 检查并创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate

# 2. 安装依赖
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn requests pydantic openai flask PyGithub matplotlib pandas seaborn markdown pdfkit python-dotenv

# 3. 启动主循环（如已在运行则跳过）
if ! pgrep -f "python3 xuanji_ai_main.py" > /dev/null; then
    nohup python3 xuanji_ai_main.py > ai.log 2>&1 &
    echo "已启动主循环：xuanji_ai_main.py"
else
    echo "主循环已在运行。"
fi

# 4. 启动API服务（如已在运行则跳过）
if ! pgrep -f "uvicorn api_server:app" > /dev/null; then
    nohup $VENV_DIR/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000 > api_server.log 2>&1 &
    echo "已启动API服务：api_server.py"
else
    echo "API服务已在运行。"
fi

# 5. 检查端口监听
echo "==== 端口监听情况 ===="
netstat -tnlp | grep 8000 || echo "API端口未监听，请检查api_server.py是否正常"

# 6. 提示API文档访问方式
echo "如需在主机浏览器查看API文档，可运行："
echo '$BROWSER http://localhost:8000/docs'