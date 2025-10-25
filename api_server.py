# 导入和app定义提前
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time, json, logging, os, datetime, subprocess
from bazi_naming import generate_names
from bazi_chart import solar2bazi, lunar2bazi

app = FastAPI(
    title="Celestial Nexus API Server",
    description="玄机 AI 系统 API 服务，支持微信公众号集成",
    version="2.0.0"
)
# 双色球预测API模型
class SsqPredictRequest(BaseModel):
    date: str
    time: str
    period: str
    calendar: str
    predict_time: str
    mode: str

# 新增API路由
@app.post("/api/ssq_predict")
async def api_ssq_predict(req: SsqPredictRequest):
    """
    接收前端双色球预测参数，调用融合预测逻辑，返回结果。
    """
    try:
        # 解析参数，调用ssq_predict_cycle
        from ssq_predict_cycle import SSQPredictCycle
        cycle = SSQPredictCycle(data_path='ssq_history.csv')
        idx = len(cycle.history) - 1
        # 根据mode选择模型
        if req.mode == '小六爻':
            reds, blue = cycle.predict_liuyao(idx)
        elif req.mode == '小六壬':
            reds, blue = cycle.predict_liuren(idx)
        elif req.mode == '奇门遁甲':
            reds, blue = cycle.predict_qimen(idx)
        elif req.mode == '紫薇奇数':
            reds, blue = cycle.predict_ai(idx) # 可自定义紫薇逻辑
        else:
            # AI融合预测
            attempts = []
            for model in ['liuyao','liuren','qimen','ai']:
                if model == 'liuyao': pr, pb = cycle.predict_liuyao(idx)
                elif model == 'liuren': pr, pb = cycle.predict_liuren(idx)
                elif model == 'qimen': pr, pb = cycle.predict_qimen(idx)
                else: pr, pb = cycle.predict_ai(idx)
                attempts.append({'strategy': model, 'pred_reds': pr, 'pred_blue': pb})
            reds, blue = cycle._fuse_from_attempts(attempts)
        return JSONResponse({
            'status': 'ok',
            'date': req.date,
            'period': req.period,
            'mode': req.mode,
            'pred_reds': sorted(reds),
            'pred_blue': int(blue),
        })
    except Exception as e:
        return JSONResponse({'status': 'error', 'error': str(e)})
from fastapi import FastAPI, Request, BackgroundTasks # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
from typing import Optional, Dict, Any
from xuanji_ai_main import run_xuanji_ai
import time
import json
import logging
import os
import datetime
import subprocess
from bazi_naming import generate_names  # 简易八字起名
from bazi_chart import solar2bazi, lunar2bazi
# 注：具体转换由 bazi_chart 处理，这里不直接依赖 lunar_python

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
        # 加入融合参数与supervisor摘要
        fusion = None
        try:
            with open('ssq_strategy_weights.json', 'r', encoding='utf-8') as wf:
                ws = json.load(wf)
                if isinstance(ws, dict):
                    fusion = ws.get('fusion')
        except Exception:
            fusion = None
        sup_summary = []
        try:
            import subprocess
            out = subprocess.check_output(['supervisorctl', 'status'], stderr=subprocess.STDOUT, text=True, timeout=3)
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            # 仅挑选关键服务
            for ln in lines:
                if any(key in ln for key in ['xuanji_api','xuanji_predict','xuanji_tuner','xuanji_evaluator','xuanji_optimize']):
                    sup_summary.append(ln)
        except Exception:
            sup_summary = []
        
        return {
            "status": "运行中",
            "uptime": f"{(time.time() - startup_time):.1f}秒",
            "requests": request_count,
            "system_state": state,
            "fusion": fusion,
            "supervisor": sup_summary,
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


@app.get("/ssq/status")
async def ssq_status():
    """返回SSQ权重与最近评估文件摘要路径"""
    weights, eval_reports = {}, []
    latest_weight_entry = None
    try:
        with open('ssq_strategy_weights.json', 'r', encoding='utf-8') as f:
            w = json.load(f)
            weights = w.get('weights', {})
    except Exception:
        pass
    # 追加读取最近一条权重历史
    try:
        path = os.path.join('reports', 'ssq_weights_history.jsonl')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    latest_weight_entry = json.loads(line)
    except Exception:
        latest_weight_entry = None
    try:
        rep_dir = os.path.join(os.getcwd(), 'reports')
        if os.path.exists(rep_dir):
            eval_reports = [
                os.path.join('reports', f) for f in os.listdir(rep_dir) if f.startswith('ssq_eval_')
            ]
            eval_reports.sort()
            eval_reports = eval_reports[-5:]
    except Exception:
        pass
    return {
        'weights': weights,
        'latest_weights_history': latest_weight_entry,
        'recent_eval_reports': eval_reports,
    }


@app.post("/ssq/tune")
async def ssq_tune(background_tasks: BackgroundTasks, window: int = 500, ema: float = 0.6, train_ai: bool = False):
    """后台触发一次调优（可选窗口与EMA）"""
    cmd = ['python', 'ssq_auto_tuner.py', '--data', 'ssq_history.csv', '--out', 'ssq_strategy_weights.json', '--priors', 'ssq_ball_priors.json']
    if window and window > 0:
        cmd += ['--window', str(window)]
    if ema and ema > 0:
        cmd += ['--ema', str(ema)]
    if train_ai:
        cmd += ['--train-ai']
    def run_cmd():
        try:
            subprocess.run(cmd, check=False)
        except Exception as e:
            logger.error(f"SSQ 调优执行失败: {e}")
    background_tasks.add_task(run_cmd)
    return {'status': 'scheduled', 'cmd': ' '.join(cmd)}


@app.get("/ssq/eval")
async def ssq_eval_latest(window: int = 0):
    """返回最近一次评估的JSON内容（如存在）"""
    try:
        # 若传入 window>0，则直接临时评估返回，不落盘
        if window and window > 0:
            try:
                from ssq_evaluate import evaluate_recent
                data = evaluate_recent(window=window)
                return {'status': 'ok', 'file': None, 'data': data}
            except Exception as e:
                logger.error(f"即时评估失败: {e}")
                return {'status': 'error', 'error': str(e)}
        rep_dir = os.path.join(os.getcwd(), 'reports')
        if not os.path.exists(rep_dir):
            return {'status': 'no_reports'}
        files = [f for f in os.listdir(rep_dir) if f.startswith('ssq_eval_') and f.endswith('.json')]
        if not files:
            return {'status': 'no_reports'}
        files.sort()
        latest = os.path.join(rep_dir, files[-1])
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {'status': 'ok', 'file': os.path.join('reports', files[-1]), 'data': data}
    except Exception as e:
        logger.error(f"读取评估报告失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.post("/ssq/eval")
async def ssq_eval_run(background_tasks: BackgroundTasks):
    """后台触发一次评估生成"""
    def run_cmd():
        try:
            subprocess.run(['python', 'ssq_evaluate.py'], check=False)
        except Exception as e:
            logger.error(f"SSQ 评估执行失败: {e}")
    background_tasks.add_task(run_cmd)
    return {'status': 'scheduled'}


@app.get("/ssq/eval_grid")
async def ssq_eval_grid(window: int = 100, diversify: bool = True, seed: int | None = 42, apply: bool = False):
    """参数化网格评估：对比 red/blue 双侧 temp/top-p/alpha 组合在最近窗口内的表现。
    - apply=True: 将最佳组合写回 ssq_strategy_weights.json 的 fusion 字段，并记录 fusion_evidence。
    """
    try:
        from ssq_eval_grid import evaluate_grid, EvalConfig
        cfg = EvalConfig(window=window, diversify=diversify, seed=seed, apply_best=bool(apply))
        out = evaluate_grid(cfg)
        return out
    except Exception as e:
        logger.error(f"eval_grid 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/ssq/selfcheck")
async def ssq_selfcheck():
    """轻量自检：验证融合逻辑、参数加载（fusion/env）与多候选多样性是否工作，返回一组摘要。"""
    try:
        from ssq_predict_cycle import SSQPredictCycle
        cyc = SSQPredictCycle(data_path='ssq_history.csv')
        history = cyc.history
        if not history:
            return {'status': 'error', 'error': 'no_history'}
        idx = len(history) - 1
        attempts = []
        for m in ['liuyao','liuren','qimen','ai']:
            if m == 'liuyao': pr, pb = cyc.predict_liuyao(idx)
            elif m == 'liuren': pr, pb = cyc.predict_liuren(idx)
            elif m == 'qimen': pr, pb = cyc.predict_qimen(idx)
            else: pr, pb = cyc.predict_ai(idx)
            attempts.append({'strategy': m, 'pred_reds': pr, 'pred_blue': pb})
        # 单组融合
        reds, blue = cyc._fuse_from_attempts(attempts)
        # 多候选生成
        cands = cyc.generate_candidates_from_attempts(attempts, count=5)
        # 统计多样性（平均重合度）
        overlaps = []
        for i in range(len(cands)):
            for j in range(i+1, len(cands)):
                overlaps.append(len(set(cands[i]['reds']) & set(cands[j]['reds'])))
        avg_overlap = sum(overlaps)/len(overlaps) if overlaps else 0.0
        return {
            'status': 'ok',
            'fusion_params': {
                'alpha_red': cyc.alpha_red,
                'temp_red': cyc.temp_red,
                'top_p_red': cyc.top_p_red,
                'alpha_blue': cyc.alpha_blue,
                'temp_blue': cyc.temp_blue,
                'top_p_blue': cyc.top_p_blue,
                'diversify': cyc.enforce_candidate_diversity,
                'max_overlap': cyc.max_overlap_reds,
            },
            'cultural_gamma': getattr(cyc, 'cultural_gamma', None),
            'one_fused': {'reds': reds, 'blue': blue},
            'candidates': cands,
            'avg_overlap': round(avg_overlap, 3),
        }
    except Exception as e:
        logger.error(f"selfcheck 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/ssq/predict")
async def ssq_predict(
    count: int = 1,
    train_ai: bool = False,
    diversify: Optional[bool] = None,
    temp_red: Optional[float] = None,
    temp_blue: Optional[float] = None,
    top_p_red: Optional[float] = None,
    top_p_blue: Optional[float] = None,
    max_overlap: Optional[int] = None,
    seed: Optional[int] = None,
):
    """基于当前策略与权重返回融合预测候选（不落盘）。
    - count>1: 生成多组候选并按重合度阈值去相似。
    - 可选参数：diversify、temp_*/top_p_*（温度与top-p采样）、max_overlap（红球最多重合数）、seed（可复现随机种子）。
    """
    try:
        from ssq_predict_cycle import SSQPredictCycle
        cycle = SSQPredictCycle(data_path='ssq_history.csv')
        if train_ai:
            try:
                _ = cycle.ai_model.train()
            except Exception:
                pass
        history = cycle.history
        if not history:
            return {'status': 'error', 'error': 'no_history'}
        idx = len(history) - 1
        true_reds, true_blue = history[idx]  # 用最近一期的期次上下文做基准
        # 临时注入参数（仅当显式传入时覆盖），否则使用权重文件中的最佳融合参数
        try:
            if diversify is not None:
                cycle.enforce_candidate_diversity = bool(diversify)
            if temp_red is not None:
                cycle.temp_red = float(temp_red)
            if temp_blue is not None:
                cycle.temp_blue = float(temp_blue)
            if top_p_red is not None:
                cycle.top_p_red = float(top_p_red)
            if top_p_blue is not None:
                cycle.top_p_blue = float(top_p_blue)
            if max_overlap is not None:
                cycle.max_overlap_reds = int(max_overlap)
            if seed is not None:
                import random as _rnd
                _rnd.seed(int(seed))
        except Exception:
            pass
        attempts = []
        for model in ['liuyao','liuren','qimen','ai']:
            if model == 'liuyao': pr, pb = cycle.predict_liuyao(idx)
            elif model == 'liuren': pr, pb = cycle.predict_liuren(idx)
            elif model == 'qimen': pr, pb = cycle.predict_qimen(idx)
            else: pr, pb = cycle.predict_ai(idx)
            attempts.append({'strategy': model, 'pred_reds': pr, 'pred_blue': pb})
        n = max(1, min(50, int(count)))
        if n == 1:
            reds, blue = cycle._fuse_from_attempts(attempts)
            out = [{'reds': sorted(reds), 'blue': int(blue)}]
        else:
            out = cycle.generate_candidates_from_attempts(attempts, count=n)
        return {'status': 'ok', 'candidates': out, 'params': {
            'diversify': bool(cycle.enforce_candidate_diversity),
            'temp_red': float(cycle.temp_red), 'temp_blue': float(cycle.temp_blue),
            'top_p_red': float(cycle.top_p_red), 'top_p_blue': float(cycle.top_p_blue),
            'alpha_red': float(cycle.alpha_red),
            'max_overlap': int(cycle.max_overlap_reds), 'seed': seed,
        }}
    except Exception as e:
        logger.error(f"即时融合预测失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/bazi/name")
async def bazi_name(surname: str, bazi: str, gender: str = 'neutral', count: int = 10, style: str = 'neutral', single: bool = False):
    """根据八字（干支）与姓氏生成候选名字与解释。
    参数：
      - surname: 姓氏
      - bazi: 八字干支文本（如：辛酉年 丁未月 壬午日 戊午时）
      - gender: male|female|neutral
      - count: 返回数量
      - style: classic|elegant|modern|neutral
      - single: 是否单字名
    示例：/bazi/name?surname=李&bazi=辛酉年%20丁未月%20壬午日%20戊午时&gender=male&style=modern&single=false&count=8
    """
    try:
        data = generate_names(surname=surname, bazi_text=bazi, gender=gender, count=count, style=style, single=single)
        return {'status': 'ok', 'data': data}
    except Exception as e:
        logger.error(f"八字起名失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/calendar/solar2lunar")
async def api_solar2lunar(year: int, month: int, day: int, hour: int = 12, minute: int = 0, second: int = 0, tz: str | None = None, sect: int = 2):
    """公历转农历，并返回对应干支/生肖信息。
    - tz: 时区，如 Asia/Shanghai、UTC、UTC+8、UTC-5:30 等，默认 Asia/Shanghai
    - sect: 八字流派 1/2（晚子时跨日规则），默认 2
    """
    try:
        b = solar2bazi(year, month, day, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        return {
            'status': 'ok',
            'solar': {
                'year': b['solar']['year'],
                'month': b['solar']['month'],
                'day': b['solar']['day'],
                'hour': hour, 'minute': minute, 'second': second,
            },
            'lunar': b['lunar'],
            'gan_zhi': {
                'year': b.get('year'),
                'month': b.get('month'),
                'day': b.get('day'),
                'hour': b.get('hour'),
            },
            'sect': b.get('sect'),
            'zodiac': b.get('zodiac'),
            'jie_qi': b.get('jie_qi'),
        }
    except Exception as e:
        logger.error(f"solar2lunar 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/calendar/lunar2solar")
async def api_lunar2solar(year: int, month: int, day: int, is_leap_month: bool = False, hour: int = 12, minute: int = 0, second: int = 0, tz: str | None = None, sect: int = 2):
    """农历转公历，并返回对应干支/生肖信息。
    - tz: 时区，如 Asia/Shanghai、UTC、UTC+8、UTC-5:30 等，默认 Asia/Shanghai
    - sect: 八字流派 1/2（晚子时跨日规则），默认 2
    """
    try:
        b = lunar2bazi(year, month, day, is_leap_month=is_leap_month, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        return {
            'status': 'ok',
            'lunar': {
                'year': b['lunar']['year'],
                'month': b['lunar']['month'],
                'day': b['lunar']['day'],
                'leap': b['lunar']['leap'],
                'month_in_chinese': b['lunar']['month_in_chinese'],
                'day_in_chinese': b['lunar']['day_in_chinese'],
            },
            'solar': {
                'year': b['solar']['year'], 'month': b['solar']['month'], 'day': b['solar']['day'],
                'hour': hour, 'minute': minute, 'second': second,
            },
            'gan_zhi': {
                'year': b.get('year'),
                'month': b.get('month'),
                'day': b.get('day'),
                'hour': b.get('hour'),
            },
            'sect': b.get('sect'),
            'zodiac': b.get('zodiac'),
            'jie_qi': b.get('jie_qi'),
        }
    except Exception as e:
        logger.error(f"lunar2solar 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/bazi/paipan")
async def api_bazi_paipan(source: str = 'solar', year: int = 1990, month: int = 1, day: int = 1, hour: int = 12, minute: int = 0, second: int = 0, is_leap_month: bool = False, tz: str | None = None, sect: int = 2):
    """根据公历或农历自动排盘，返回八字干支四柱与相关信息。
    - source: solar|lunar；农历时可传 is_leap_month
    - tz: 时区，如 Asia/Shanghai、UTC、UTC+8、UTC-5:30 等，默认 Asia/Shanghai
    - sect: 八字流派 1/2（晚子时跨日规则），默认 2
    """
    try:
        source = (source or 'solar').lower()
        if source == 'lunar':
            data = lunar2bazi(year, month, day, is_leap_month=is_leap_month, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        else:
            data = solar2bazi(year, month, day, hour=hour, minute=minute, second=second, tz=tz, sect=sect)
        return {'status': 'ok', 'data': data}
    except Exception as e:
        logger.error(f"bazi paipan 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/ssq/weights_history")
async def ssq_weights_history(limit: int = 200):
    """返回权重历史（JSONL）最近N条"""
    try:
        path = os.path.join('reports', 'ssq_weights_history.jsonl')
        if not os.path.exists(path):
            return {'status': 'no_history'}
        lines = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(json.loads(line))
        return {'status': 'ok', 'items': lines[-limit:]}
    except Exception as e:
        logger.error(f"读取权重历史失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.get("/ssq/eval_multi")
async def ssq_eval_multi(window: int = 120, n: int = 5, diversify: bool = True, seed: int | None = 42):
    """评估多候选（Top-N）情景下的准确度提升：
    - window: 最近窗口期数
    - n: 每期生成候选数量（1..50）
    - diversify: 是否启用多样性约束
    - seed: 随机种子（可复现）
    返回：avg_best_reds_hit、blue_hit_rate_any、full_matches 等。
    """
    try:
        from ssq_eval_multi import evaluate_multi
        out = evaluate_multi(window=window, n=n, diversify=diversify, seed=seed)
        return out
    except Exception as e:
        logger.error(f"eval_multi 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.post("/ssq/import_now")
async def ssq_import_now(force: bool = False):
    """
    手动触发从 reports/双色球 导入真实开奖。
    - force=true: 设置 IMPORT_ANYTIME=1，忽略开奖时间窗口（仅联调/测试使用）。
    返回：imported 数量与最近的状态文件/最新评估路径。
    """
    try:
        env = os.environ.copy()
        if force:
            env['IMPORT_ANYTIME'] = '1'
        proc = subprocess.run(
            ['python', 'tools/import_ssq_from_tsv.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.getcwd(),
            timeout=60,
            check=False,
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        imported = 0
        for line in out.splitlines():
            if line.strip().startswith('imported='):
                try:
                    imported = int(line.strip().split('=', 1)[1])
                except Exception:
                    pass
        # 读取状态文件与 latest_eval
        status_path = os.path.join('static', 'ssq_import_status.json')
        status = None
        try:
            if os.path.exists(status_path):
                with open(status_path, 'r', encoding='utf-8') as f:
                    status = json.load(f)
        except Exception:
            status = None
        latest_eval = None
        try:
            rep_dir = os.path.join('reports')
            if os.path.exists(rep_dir):
                files = [f for f in os.listdir(rep_dir) if f.startswith('ssq_eval_') and f.endswith('.json')]
                files.sort()
                if files:
                    latest_eval = os.path.join('reports', files[-1])
        except Exception:
            latest_eval = None
        return {
            'status': 'ok',
            'imported': imported,
            'stdout': out[-2000:],
            'stderr': err[-2000:],
            'status_file': status,
            'latest_eval': latest_eval,
        }
    except Exception as e:
        logger.error(f"import_now 失败: {e}")
        return {'status': 'error', 'error': str(e)}


@app.post("/ssq/fetch_now")
async def ssq_fetch_now(force: bool = False):
    """
    触发互联网抓取最新双色球：
    - force=true: 设置 IMPORT_ANYTIME=1，忽略开奖时间窗口（仅联调/测试使用）。
    返回抓取结果（period/balls）或 skip 原因。
    """
    try:
        import subprocess, os
        env = os.environ.copy()
        if force:
            env['IMPORT_ANYTIME'] = '1'
        proc = subprocess.Popen(
            ['python', 'tools/fetch_and_store_ssq.py'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
        )
        out = proc.communicate()[0].decode('utf-8', errors='ignore')
        return {"status": "ok", "output": out}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
