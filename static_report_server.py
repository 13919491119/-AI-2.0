#!/usr/bin/env python3
"""
static_report_server.py
静态网站服务器 - 自动展示运营报告
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from datetime import datetime
import glob

app = FastAPI(title="Static Report Server")

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def home():
    """主页 - 显示可用报告列表"""
    # 查找所有报告文件
    reports = glob.glob("operation_report_*.md")
    reports.sort(reverse=True)  # 最新的在前
    
    report_links = ""
    for report in reports[:10]:  # 显示最近10个报告
        report_name = report.replace('.md', '')
        date_str = report_name.split('_')[-1]
        report_links += f'<li><a href="/report/{report_name}">{date_str} 运营报告</a></li>\n'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>玄机AI运营报告中心</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #fff;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }}
            .info {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            ul {{
                list-style-type: none;
                padding: 0;
            }}
            li {{
                background: rgba(255, 255, 255, 0.1);
                margin: 10px 0;
                padding: 15px;
                border-radius: 10px;
                transition: all 0.3s;
            }}
            li:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: translateX(10px);
            }}
            a {{
                color: #fff;
                text-decoration: none;
                font-size: 1.1em;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔮 玄机AI运营报告中心</h1>
            <div class="info">
                <p>📅 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>📊 报告总数: {len(reports)}</p>
            </div>
            <h2>📋 可用报告列表</h2>
            <ul>
                {report_links if report_links else '<li>暂无报告</li>'}
            </ul>
            <div class="footer">
                <p>Celestial Nexus © 2025</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/report/{report_name}")
def show_report(report_name: str):
    """显示特定报告"""
    report_file = f"{report_name}.md"
    
    if not os.path.exists(report_file):
        return HTMLResponse("<h1>报告不存在</h1>", status_code=404)
    
    # 读取Markdown内容
    with open(report_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 简单的Markdown转HTML (基础版本)
    html_content = md_content.replace('\n## ', '\n<h2>').replace('\n### ', '\n<h3>')
    html_content = html_content.replace('**', '<strong>').replace('**', '</strong>')
    html_content = html_content.replace('\n- ', '\n<li>').replace('\n', '<br>\n')
    html_content = html_content.replace('<br>\n<li>', '<li>')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_name}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
                color: #333;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                color: #667eea;
            }}
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }}
            a {{
                color: #667eea;
                text-decoration: none;
            }}
            .back {{
                display: inline-block;
                margin-bottom: 20px;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back">← 返回列表</a>
            <div class="content">
                {html_content}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "static_report_server"}

if __name__ == "__main__":
    print("🌐 启动静态报告服务器...")
    print("📊 访问地址: http://127.0.0.1:8089")
    uvicorn.run(app, host="0.0.0.0", port=8089)
