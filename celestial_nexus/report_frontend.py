"""
report_frontend.py
自动化运营报告生成+美化Web前端
- 启动后自动拉取API数据，生成美观的周期运营报告页面
"""
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

API_URL = "http://127.0.0.1:8000/status"

app = FastAPI(title="Celestial Nexus 运营报告前端")
app.mount("/static", StaticFiles(directory="static"), name="static")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang='zh-CN'>
<head>
    <meta charset='utf-8'>
    <title>玄机AI周期运营报告</title>
    <link rel='stylesheet' href='/static/report.css'>
</head>
<body>
    <div class='container'>
        <h1>🔮 玄机AI 周期运营报告</h1>
        <div class='section'>
            <h2>系统状态</h2>
            <ul>
                <li>累计发现模式数：<b>{pattern_count}</b></li>
                <li>系统权重分布：<b>{system_weights}</b></li>
            </ul>
        </div>
        <footer>Celestial Nexus &copy; 2025</footer>
    </div>
</body>
</html>
"""

@app.get("/report", response_class=HTMLResponse)
def report(request: Request):
    try:
        resp = requests.get(API_URL, timeout=3)
        data = resp.json()
        html = HTML_TEMPLATE.format(
            pattern_count=data.get("pattern_count", "-"),
            system_weights=data.get("system_weights", "-")
        )
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h2>报告生成失败: {e}</h2>", status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
