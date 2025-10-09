from fastapi import FastAPI, Request, BackgroundTasks # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
from typing import Optional, Dict, Any
from xuanji_ai_main import run_xuanji_ai
import time
import json
import logging
import os
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='api_server.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Celestial Nexus API Server",
    description="玄机 AI 系统 API 服务，支持微信公众号集成",
    version="2.0.0"
)

# 状态监控
startup_time = time.time()
request_count = 0

class XuanjiRequest(BaseModel):
    input: str
    source: Optional[str] = "api"
    metadata: Optional[Dict[str, Any]] = None

@app.post("/run_xuanji_ai")
async def run_xuanji_ai_api(req: XuanjiRequest, background_tasks: BackgroundTasks):
    global request_count
    request_count += 1
    
    logger.info(f"收到请求: {req.input[:50]}... 来源: {req.source}")
    
    # 特殊指令预处理
    input_text = req.input.lower()
    
    # 双色球预测请求
    if "双色球" in input_text and ("预测" in input_text or "推荐" in input_text):
        try:
            with open('ai.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                prediction = None
                for i in range(len(lines)-1, -1, -1):
                    if "[自动预测] 红球:" in lines[i]:
                        prediction = lines[i].strip()
                        break
                
                if prediction:
                    return {
                        "result": f"【最新双色球预测】\n{prediction}\n\n预测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        "status": "success"
                    }
        except Exception as e:
            logger.error(f"获取双色球预测失败: {e}")
    
    # 系统状态请求
    elif "系统状态" in input_text or "运行状态" in input_text:
        try:
            with open('xuanji_system_state.json', 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            return {
                "result": f"""【玄机AI系统状态】
累计学习周期: {state.get('cumulative_learning_cycles', '未知')}
系统优化进度: {state.get('optimize_progress', '未知')}
运行周期: {state.get('run_cycle', '未知')}
性能提升: {state.get('perf_improve', '未知')}倍

系统运行正常，持续自主学习与优化中。
""",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
    
    # 周期报告请求
    elif "周期报告" in input_text or "运营报告" in input_text:
        try:
            # 列出reports目录下最新的报告
            reports_dir = os.path.join(os.getcwd(), 'reports')
            if os.path.exists(reports_dir):
                reports = [f for f in os.listdir(reports_dir) if f.startswith('operation_report_')]
                reports.sort(reverse=True)
                
                if reports:
                    latest_report = os.path.join(reports_dir, reports[0])
                    with open(latest_report, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 截取前500个字符作为摘要
                        summary = content[:500] + "...\n\n(完整报告请访问管理后台)"
                        return {
                            "result": f"【最新运营周期报告】\n\n{summary}",
                            "status": "success"
                        }
        except Exception as e:
            logger.error(f"获取周期报告失败: {e}")
    
    # 正常请求 - 交给玄机AI处理
    try:
        # 记录请求来源
        logger.info(f"请求来源: {req.source}, 输入: {req.input[:100]}...")
        
        # 执行玄机AI处理
        result = run_xuanji_ai(req.input)
        
        # 对于微信公众号请求，增强格式化
        if req.source == "刘洪鹏76公众号":
            result = f"【玄机AI回复】\n\n{result}\n\n——刘洪鹏76玄机AI"
        
        return {"result": result}
    except Exception as e:
        logger.error(f"处理请求出错: {e}")
        return {"result": "系统处理您的请求时遇到问题，请稍后再试"}

@app.get("/")
async def root():
    """API 根路径，返回基本信息"""
    return {
        "name": "Celestial Nexus AI API",
        "version": "2.0",
        "status": "运行中",
        "uptime": f"{(time.time() - startup_time):.1f}秒",
        "endpoints": [
            "/", "/run_xuanji_ai", "/status", "/health", "/docs"
        ]
    }

@app.get("/status")
async def status():
    """获取系统状态"""
    try:
        with open('xuanji_system_state.json', 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        return {
            "status": "运行中",
            "uptime": f"{(time.time() - startup_time):.1f}秒",
            "requests": request_count,
            "system_state": state
        }
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return {
            "status": "降级",
            "uptime": f"{(time.time() - startup_time):.1f}秒",
            "requests": request_count,
            "error": str(e)
        }

@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
