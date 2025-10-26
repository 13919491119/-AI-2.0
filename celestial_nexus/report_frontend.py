"""
report_frontend.py
自动化运营报告生成+美化Web前端
- 启动后自动拉取API数据，生成美观的周期运营报告页面
"""
def _get_requests():
    try:
        import requests  # type: ignore
        return requests
    except Exception:
        return None
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os, json, importlib
# 尝试加载 .env（若安装了 python-dotenv）
try:
    _dotenv = importlib.import_module("dotenv")
    if hasattr(_dotenv, "load_dotenv"):
        _dotenv.load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
except Exception:
    pass
try:  # 动态导入，避免静态分析误报
    CORSMiddleware = importlib.import_module("fastapi.middleware.cors").CORSMiddleware  # type: ignore
except Exception:
    CORSMiddleware = None  # type: ignore

API_URL = "http://127.0.0.1:8000/status"

app = FastAPI(title="Celestial Nexus 运营报告前端")
app.mount("/static", StaticFiles(directory="static"), name="static")
if CORSMiddleware is not None:
    # 允许来自本机静态站点等页面的跨域调用
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
        <div class='section'>
            <h2>运行状态报告</h2>
            <p>
                <a href='/status_report' target='_blank'>查看最新“学习/复盘/预测/升级”运行状态报告</a>
            </p>
        </div>
        <footer>Celestial Nexus &copy; 2025</footer>
    </div>
</body>
</html>
"""

@app.get("/report", response_class=HTMLResponse)
def report(request: Request):
    try:
        req = _get_requests()
        data = {}
        if req is not None:
            resp = req.get(API_URL, timeout=3)
            data = resp.json()
        html = HTML_TEMPLATE.format(
            pattern_count=data.get("pattern_count", "-"),
            system_weights=data.get("system_weights", "-")
        )
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h2>报告生成失败: {e}</h2>", status_code=500)

# 新增：展示最新状态报告（以 <pre> 形式直出 Markdown 文本，避免引入额外依赖）
@app.get("/status_report", response_class=HTMLResponse)
def status_report():
    import glob, datetime
    reports_dir = os.path.join(os.getcwd(), 'reports')
    if not os.path.exists(reports_dir):
        return HTMLResponse("<h2>报告目录不存在</h2>", status_code=404)
    # 优先当天，否则选择最近的 ssq_status_*.md
    today = datetime.datetime.now().strftime('%Y%m%d')
    preferred = os.path.join(reports_dir, f'ssq_status_{today}.md')
    md_path = preferred if os.path.exists(preferred) else None
    if md_path is None:
        paths = sorted(glob.glob(os.path.join(reports_dir, 'ssq_status_*.md')))
        if paths:
            md_path = paths[-1]
    if not md_path:
        return HTMLResponse("<h2>未找到状态报告</h2>", status_code=404)
    try:
        # 读取最新时间快照（若存在），以展示双时区时间
        status_json = os.path.join(os.getcwd(), 'static', 'status.json')
        utc_ts = local_ts = tz_name = None
        if os.path.exists(status_json):
            try:
                with open(status_json, 'r', encoding='utf-8') as jf:
                    snap = json.load(jf)
                utc_ts = snap.get('timestamp')
                local_ts = snap.get('local_time')
                tz_name = snap.get('timezone') or 'Asia/Shanghai'
            except Exception:
                pass
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 简单包裹为 <pre>，保留 markdown 文本可读性
        html = f"""
        <!DOCTYPE html>
        <html lang='zh-CN'>
        <head>
            <meta charset='utf-8'>
            <title>最新运行状态报告</title>
            <link rel='stylesheet' href='/static/report.css'>
            <style>
                pre {{ white-space: pre-wrap; word-break: break-word; }}
                .container {{ max-width: 900px; margin: 32px auto; padding: 0 16px; }}
                .meta {{ color:#6b7280; font-size:14px; margin-top:6px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <h1>🛰️ 最新运行状态报告</h1>
                <div class='meta'>文件：{os.path.basename(md_path)}
                {('<br/>生成时间（UTC）：'+utc_ts) if utc_ts else ''}
                {('｜北京时间（'+tz_name+'）：'+local_ts) if local_ts else ''}
                </div>
                <pre>{content}</pre>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h2>读取报告失败: {e}</h2>", status_code=500)

# 新增：展示最新运营周期报告（operation_report_*.md）
@app.get("/operation_report", response_class=HTMLResponse)
def operation_report():
    import glob
    try:
        reports_dir = os.path.join(os.getcwd(), 'reports')
        paths = sorted(glob.glob(os.path.join(reports_dir, 'operation_report_*.md')))
        if not paths:
            return HTMLResponse("<h2>未找到运营周期报告</h2>", status_code=404)
        md_path = paths[-1]
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        html = f"""
        <!DOCTYPE html>
        <html lang='zh-CN'>
        <head>
            <meta charset='utf-8'>
            <title>最新运营周期报告</title>
            <link rel='stylesheet' href='/static/report.css'>
            <style> pre {{ white-space: pre-wrap; word-break: break-word; }} .container {{ max-width: 900px; margin: 32px auto; padding: 0 16px; }} </style>
        </head>
        <body>
            <div class='container'>
                <h1>📈 最新运营周期报告</h1>
                <p>文件：{os.path.basename(md_path)}</p>
                <pre>{content}</pre>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h2>读取运营报告失败: {e}</h2>", status_code=500)

# 互联网联通性自检：返回最新一次自检 JSON，如不存在可提示运行 tools/self_test_internet.py
@app.get("/internet_self_test", response_class=HTMLResponse)
def internet_self_test():
    try:
        p = os.path.join(os.getcwd(), 'static', 'internet_self_test.json')
        if not os.path.exists(p):
            return HTMLResponse("<h2>尚未执行过互联网自检，请运行 tools/self_test_internet.py</h2>", status_code=404)
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        html = f"""
        <!DOCTYPE html>
        <html lang='zh-CN'>
        <head>
            <meta charset='utf-8'>
            <title>互联网自检结果</title>
            <link rel='stylesheet' href='/static/report.css'>
            <style> .container {{ max-width: 900px; margin: 32px auto; padding: 0 16px; }} pre {{ white-space: pre-wrap; word-break: break-word; }} </style>
        </head>
        <body>
            <div class='container'>
                <h1>🌐 互联网自检结果</h1>
                <pre>{json.dumps(data, ensure_ascii=False, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<h2>读取自检结果失败: {e}</h2>", status_code=500)

# 联网检索 API：接收 {"query":"...", "max_results":3}，返回摘要与来源
@app.post("/web_research")
async def web_research(req: Request):
    try:
        payload = await req.json()
        query = (payload.get("query") or "").strip()
        max_results = int(payload.get("max_results") or 3)
        if not query:
            return JSONResponse({"error": "query 不能为空"}, status_code=400)
        # 延迟导入，避免服务启动时阻塞
        try:
            from internet_research import research_and_summarize  # type: ignore
        except Exception as e:
            return JSONResponse({"error": f"导入失败: {e}"}, status_code=500)
        out = research_and_summarize(query, max_results=max_results)
        return JSONResponse(out)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
