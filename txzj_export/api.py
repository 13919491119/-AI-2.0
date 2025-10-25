# ...existing code from celestial_nexus/api.py...
"""
天枢智鉴AI 3.0 FastAPI接口
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ai_core import CelestialNexusAI
import asyncio
import json

app = FastAPI(title="CelestialNexusAI 3.0 API", description="天枢智鉴AI 3.0 智能系统API接口", version="3.0")
ai_instance = CelestialNexusAI()

class RequestData(BaseModel):
    query_type: str
    query_data: dict

from fastapi.responses import HTMLResponse

@app.get("/patterns", response_class=HTMLResponse)
def get_patterns():
    ai = ai_instance
    patterns = ai.learning_memory["knowledge_base"].get("discovered_patterns", [])
    html = """
    <html><head><title>新模式发现可视化</title><meta charset='utf-8'>
    <style>
    body{font-family:Arial,sans-serif;background:#f8f8f8;}
    h2{color:#2b6cb0;}
    .pattern{background:#fff;border-radius:6px;padding:8px 16px;margin:8px 0;box-shadow:0 1px 3px #ccc;}
    .ai{color:#b83280;font-weight:bold;}
    .kb{color:#2b6cb0;font-weight:bold;}
    </style></head><body>
    <h2>🧠 新模式发现可视化</h2>
    <div>共发现 <b>{}</b> 种新模式：</div>
    <div style='margin-top:16px;'>""".format(len(patterns))
    for p in reversed(patterns[-100:]):
        cls = 'ai' if 'AI_' in p else ('kb' if 'desc:' in p or '知识库' in p else '')
        html += f"<div class='pattern {cls}'>{p}</div>"
    html += """</div><hr><div style='color:#888;font-size:13px;'>Powered by CelestialNexusAI 3.0</div></body></html>"""
    return html

@app.get("/status")
def get_status():
    return ai_instance.get_system_status_summary()

@app.post("/process")
async def process_request(data: RequestData):
    resp = await ai_instance.process_request(data.dict())
    return resp

@app.get("/export_state")
def export_state():
    return ai_instance.export_state()

@app.post("/import_state")
def import_state(state: dict):
    try:
        ai_instance.import_state(state=state)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
