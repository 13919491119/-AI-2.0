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
from typing import Optional
import os
from pathlib import Path
import json
try:
    from bazi_chart import solar2bazi, lunar2bazi
except Exception:
    solar2bazi = lunar2bazi = None  # type: ignore

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


class BaziEnqueueRequest(BaseModel):
    surname: str
    bazi: str
    gender: str | None = 'neutral'
    count: int | None = 10
    style: str | None = 'neutral'
    single: bool | None = False

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


@app.post("/bazi/naming/enqueue")
def api_enqueue_bazi_naming(req: BaziEnqueueRequest):
    """将起名任务写入队列 queue/bazi_naming.jsonl（与循环程序共享）。"""
    try:
        root = Path(__file__).resolve().parents[1]
        q = root / 'queue' / 'bazi_naming.jsonl'
        q.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'surname': req.surname,
            'bazi': req.bazi,
            'gender': (req.gender or 'neutral'),
            'count': int(req.count or 10),
            'style': (req.style or 'neutral'),
            'single': bool(req.single or False),
        }
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        try:
            import fcntl  # type: ignore
            with open(q, 'a', encoding='utf-8') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            # 无 fcntl 环境时，退化为普通写入
            with open(q, 'a', encoding='utf-8') as f:
                f.write(line)
        return {"status":"ok","queued":True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"enqueue failed: {e}")


# ====== Calendar & BaZi endpoints with tz/sect ======
@app.get("/calendar/solar2lunar")
def api_solar2lunar(year: int, month: int, day: int, hour: int = 12, minute: int = 0, second: int = 0, tz: Optional[str] = None, sect: int = 2):
    """公历转农历并返回八字干支/生肖/节气。
    - tz: 时区（Asia/Shanghai、UTC、UTC+8、UTC-5:30 等），先换算到北京时间再排盘
    - sect: 八字流派 1/2（晚子时跨日规则），默认 2
    """
    if solar2bazi is None:
        raise HTTPException(status_code=500, detail="bazi_chart not available")
    try:
        b = solar2bazi(year, month, day, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        return {
            'status': 'ok',
            'solar': {
                'year': b['solar']['year'], 'month': b['solar']['month'], 'day': b['solar']['day'],
                'hour': hour, 'minute': minute, 'second': second,
            },
            'lunar': b['lunar'],
            'gan_zhi': {'year': b.get('year'), 'month': b.get('month'), 'day': b.get('day'), 'hour': b.get('hour')},
            'sect': b.get('sect'),
            'zodiac': b.get('zodiac'),
            'jie_qi': b.get('jie_qi'),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"solar2lunar failed: {e}")


@app.get("/calendar/lunar2solar")
def api_lunar2solar(year: int, month: int, day: int, is_leap_month: bool = False, hour: int = 12, minute: int = 0, second: int = 0, tz: Optional[str] = None, sect: int = 2):
    """农历转公历并返回八字干支/生肖/节气。
    - tz: 时区（Asia/Shanghai、UTC、UTC+8、UTC-5:30 等），先换算到北京时间再排盘
    - sect: 八字流派 1/2（晚子时跨日规则），默认 2
    """
    if lunar2bazi is None:
        raise HTTPException(status_code=500, detail="bazi_chart not available")
    try:
        b = lunar2bazi(year, month, day, is_leap_month=is_leap_month, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        return {
            'status': 'ok',
            'lunar': {
                'year': b['lunar']['year'], 'month': b['lunar']['month'], 'day': b['lunar']['day'],
                'leap': b['lunar']['leap'], 'month_in_chinese': b['lunar']['month_in_chinese'], 'day_in_chinese': b['lunar']['day_in_chinese'],
            },
            'solar': {
                'year': b['solar']['year'], 'month': b['solar']['month'], 'day': b['solar']['day'],
                'hour': hour, 'minute': minute, 'second': second,
            },
            'gan_zhi': {'year': b.get('year'), 'month': b.get('month'), 'day': b.get('day'), 'hour': b.get('hour')},
            'sect': b.get('sect'),
            'zodiac': b.get('zodiac'),
            'jie_qi': b.get('jie_qi'),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"lunar2solar failed: {e}")


@app.get("/bazi/paipan")
def api_bazi_paipan(source: str = 'solar', year: int = 1990, month: int = 1, day: int = 1, hour: int = 12, minute: int = 0, second: int = 0, is_leap_month: bool = False, tz: Optional[str] = None, sect: int = 2):
    """根据公历或农历自动排盘，返回八字干支四柱与相关信息。
    - source: solar|lunar；农历时可传 is_leap_month
    - tz: 时区（Asia/Shanghai、UTC、UTC+8、UTC-5:30 等），先换算到北京时间再排盘
    - sect: 八字流派 1/2（晚子时跨日规则），默认 2
    """
    if solar2bazi is None or lunar2bazi is None:
        raise HTTPException(status_code=500, detail="bazi_chart not available")
    try:
        src = (source or 'solar').lower()
        if src == 'lunar':
            data = lunar2bazi(year, month, day, is_leap_month=is_leap_month, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        else:
            data = solar2bazi(year, month, day, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        return {'status': 'ok', 'data': data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"bazi paipan failed: {e}")
