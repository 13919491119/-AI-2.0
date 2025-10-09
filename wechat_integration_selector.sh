#!/bin/bash
# Celestial Nexus AI 微信集成选择器
# 此脚本帮助用户选择合适的微信集成方式

echo "==============================================="
echo "  Celestial Nexus AI 微信集成选择器  "
echo "==============================================="

echo "请选择微信集成方式:"
echo "1) 使用Ngrok模式 (需要Ngrok认证令牌)"
echo "2) 本地简单模式 (仅限本地测试)"
echo "3) 配置FRP内网穿透 (推荐) "
echo "4) 配置Nginx反向代理 (适合生产环境)"
echo "5) 查看详细配置说明"
echo "6) 退出"
echo ""

read -p "请输入选项 [1-6]: " choice

case $choice in
    1)
        echo "您选择了Ngrok模式"
        read -p "请输入您的Ngrok认证令牌 (从 https://dashboard.ngrok.com/get-started/your-authtoken 获取): " NGROK_TOKEN
        
        if [ -z "$NGROK_TOKEN" ]; then
            echo "错误: 未提供Ngrok令牌"
            exit 1
        fi
        
        # 导出令牌为环境变量
        export NGROK_AUTH_TOKEN="$NGROK_TOKEN"
        
        # 运行配置脚本
        echo "正在启动Ngrok模式配置..."
        ./setup_wechat_integration.sh
        ;;
    2)
        echo "您选择了本地简单模式"
        echo "正在启动本地模式配置..."
        ./local_wechat_integration.sh
        ;;
    3)
        echo "您选择了配置FRP内网穿透"
        echo "启动FRP配置助手..."
        ./setup_frp.sh
        ;;
    4)
        echo "您选择了配置Nginx反向代理"
        echo "启动Nginx配置生成器..."
        ./setup_nginx.sh
        ;;
    5)
        echo "打开详细配置说明..."
        if command -v xdg-open > /dev/null; then
            xdg-open PUBLIC_ACCESS_CONFIGURATION.md
        elif command -v open > /dev/null; then
            open PUBLIC_ACCESS_CONFIGURATION.md
        else
            echo "请手动打开文件: PUBLIC_ACCESS_CONFIGURATION.md"
            echo "可使用命令: less PUBLIC_ACCESS_CONFIGURATION.md 或 cat PUBLIC_ACCESS_CONFIGURATION.md"
        fi
        ;;
    6)
        echo "退出选择器"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac