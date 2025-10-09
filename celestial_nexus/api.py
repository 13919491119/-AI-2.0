"""
api.py
FastAPI微服务接口，支持多端调用与高可用部署
- 提供7个RESTful端点：健康检查、预测、模式发现、融合结果、系统状态、性能监控、升级操作
"""
from fastapi import FastAPI, HTTPException, Request
import time
from pydantic import BaseModel
from celestial_nexus.ai_core import PatternMemory, AutonomousPatternDiscovery, QuantumFusionEngine
import random
from xuanji_ai_main import run_xuanji_ai

app = FastAPI(title="Celestial Nexus AI Service")

# Prometheus metrics (lazy optional)
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROM = True
except ImportError:
    Counter = Histogram = None  # type: ignore
    def generate_latest():  # type: ignore
        return b''
    CONTENT_TYPE_LATEST = 'text/plain'
    _PROM = False

if _PROM:
    API_REQ_TOTAL = Counter('celestial_api_requests_total','Total API requests',['path','method','status'])
    API_REQ_LAT = Histogram('celestial_api_request_latency_seconds','API request latency',['path'])

@app.middleware('http')
async def metrics_middleware(request: Request, call_next):  # type: ignore
    start = time.time()
    response = await call_next(request)
    if _PROM:
        path = request.url.path
        # 限制 path 粒度，常用端点保留，其他归类
        if path not in {"/health","/discover","/patterns","/fuse","/status","/monitor","/upgrade"}:
            path = 'other'
        API_REQ_TOTAL.labels(path=path, method=request.method, status=response.status_code).inc()
        API_REQ_LAT.labels(path=path).observe(time.time()-start)
    return response

@app.get('/metrics')
def metrics():
    if not _PROM:
        return {"error":"prometheus-client not installed"}
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# 全局引擎实例
memory = PatternMemory()
discoverer = AutonomousPatternDiscovery(memory)
fusion = QuantumFusionEngine()

class PredictRequest(BaseModel):
    system_scores: dict

class RunRequest(BaseModel):
    input: str
    source: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/discover")
def discover_patterns(n: int = 1000):
    discoverer.discover_patterns(n)
    return {"total_patterns": memory.count()}

@app.get("/patterns")
def get_patterns(threshold: float = 0.7):
    return {"patterns": memory.filter(threshold)}

@app.post("/fuse")
def fuse_scores(req: PredictRequest):
    score = fusion.fuse(req.system_scores)
    return {"fusion_score": score}

@app.get("/status")
def status():
    return {
        "pattern_count": memory.count(),
        "system_weights": fusion.system_weights
    }

@app.get("/monitor")
def monitor():
    # 简化性能监控
    return {"uptime": random.randint(1000,9999), "health": "good"}

@app.post("/upgrade")
def upgrade():
    # 升级操作示意
    return {"upgrade": "triggered"}

@app.post("/run_xuanji_ai")
def run_ai(req: RunRequest):
    try:
        result = run_xuanji_ai(req.input)
        if req.source == '刘洪鹏76公众号':
            result = f"【玄机AI回复】\n\n{result}\n\n——刘洪鹏76玄机AI"
        return {"result": result, "status": "success"}
    except Exception as e:
        return {"result": f"处理失败: {e}", "status": "error"}
