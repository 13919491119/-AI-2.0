"""
wechat_server.py
微信服务端集成 - 自动提供周期运营报告接口
- 支持微信公众号/小程序访问
- 自动拉取最新运营报告并返回
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import requests
import hashlib
import os
from datetime import datetime

app = FastAPI(title="WeChat Integration Server")

# 微信公众号配置（从环境变量读取）
WECHAT_TOKEN = os.getenv("WECHAT_TOKEN", "xuanji_ai_token_2025")
API_URL = "http://127.0.0.1:8000/status"

@app.get("/")
def root():
    return {"service": "WeChat Integration Server", "status": "running"}

@app.get("/wechat")
def wechat_verify(signature: str = "", timestamp: str = "", nonce: str = "", echostr: str = ""):
    """微信服务器验证接口"""
    # 微信接入验证
    token = WECHAT_TOKEN
    tmp_list = [token, timestamp, nonce]
    tmp_list.sort()
    tmp_str = "".join(tmp_list)
    tmp_str = hashlib.sha1(tmp_str.encode()).hexdigest()
    
    if tmp_str == signature:
        return PlainTextResponse(echostr)
    return PlainTextResponse("Invalid signature")

@app.post("/wechat")
async def wechat_message(request: Request):
    """处理微信消息，返回运营报告"""
    # 简化实现：直接返回文本格式的运营报告
    try:
        # 获取系统状态
        resp = requests.get(API_URL, timeout=3)
        data = resp.json()
        
        # 生成报告文本
        report = f"""【玄机AI周期运营报告】
        
系统状态：
✅ 累计发现模式数：{data.get('pattern_count', '-')}
⚖️ 系统权重分布：{data.get('system_weights', '-')}

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Celestial Nexus © 2025"""
        
        # 返回微信格式的响应（简化版本）
        return PlainTextResponse(report)
    except Exception as e:
        return PlainTextResponse(f"报告生成失败: {str(e)}")

@app.get("/report")
def get_report():
    """提供JSON格式的运营报告接口"""
    try:
        resp = requests.get(API_URL, timeout=3)
        data = resp.json()
        
        report = {
            "title": "玄机AI周期运营报告",
            "timestamp": datetime.now().isoformat(),
            "system_status": {
                "pattern_count": data.get("pattern_count", 0),
                "system_weights": data.get("system_weights", {})
            },
            "message": "运营报告已成功生成"
        }
        
        return JSONResponse(report)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
def health():
    """健康检查接口"""
    return {"status": "healthy", "service": "wechat_integration"}

if __name__ == "__main__":
    print("启动微信集成服务器...")
    print("微信验证接口: http://127.0.0.1:8088/wechat")
    print("报告接口: http://127.0.0.1:8088/report")
    uvicorn.run(app, host="0.0.0.0", port=8088)
