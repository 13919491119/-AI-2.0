"""
自主模式脚本：持续运行AI系统
增加单实例守护：通过 PID 文件避免重复启动。
增强：统一心跳写入到 heartbeats/autonomous_run.json，周期循环与内部自检更新丰富字段。
"""
import asyncio
import os
import atexit
import signal
from celestial_nexus import CelestialNexusAI
from ssq_cycle_runner import run_ssq_cycle_and_summarize
import subprocess
import sys
import time
import traceback
import json
try:
    from heartbeat_manager import write_heartbeat
except Exception:  # 最小降级：若模块不存在，定义简化写入
    def write_heartbeat(name: str, **kwargs):
        data = {'ts': time.time(), 'pid': os.getpid()}
        data.update(kwargs)
        os.makedirs('heartbeats', exist_ok=True)
        path = os.path.join('heartbeats', f'{name}.json')
        try:
            import json as _json
            with open(path, 'w', encoding='utf-8') as f:
                _json.dump(data, f)
        except Exception:
            pass
        return path

# 可选：自适应调度模块
try:
    from ai_meta_system import autoadapt as _autoadapt
except Exception:  # noqa: E722
    _autoadapt = None

ROOT = os.path.dirname(__file__)
PID_FILE = os.path.join(ROOT, 'autonomous_run.pid')
READY_FILE = os.path.join(ROOT, 'autonomous_run.ready')
LEGACY_HEARTBEAT_FILE = os.path.join(ROOT, 'reports', 'autonomy_heartbeat.json')  # 保留兼容
ADAPT_FILE = os.path.join(ROOT, 'ai_meta_autoadapt.json')
ERR_LOG = os.path.join(ROOT, 'logs', 'autonomous_run.err.log')
UNIFIED_HB_NAME = 'autonomous_run'
UNIFIED_HB_PATH = os.path.join(ROOT, 'heartbeats', f'{UNIFIED_HB_NAME}.json')

def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def _write_pid_file():
    # ensure the directory for the pid file exists (should be repo root)
    pid_dir = os.path.dirname(PID_FILE)
    if pid_dir:
        os.makedirs(pid_dir, exist_ok=True)
    with open(PID_FILE, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    try:
        # write a short trace to stdout for observability
        print(f"[autonomous_run] wrote PID {os.getpid()} -> {PID_FILE}", flush=True)
    except Exception:
        pass

def _remove_pid_file():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass
    try:
        if os.path.exists(READY_FILE):
            os.remove(READY_FILE)
    except Exception:
        pass

def _ensure_single_instance_or_exit():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r', encoding='utf-8') as f:
                old_pid = int((f.read() or '0').strip() or '0')
        except Exception:
            old_pid = 0
        if old_pid > 0 and _pid_is_running(old_pid):
            # 已有实例在运行，直接退出
            raise SystemExit(f"[autonomous_run] 已有实例在运行 (PID={old_pid})，本次启动取消。")
    _write_pid_file()
    # 注册退出清理
    atexit.register(_remove_pid_file)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, lambda *_: (_remove_pid_file(), exit(0)))
        except Exception:
            pass

async def main():
    ai = CelestialNexusAI()
    await ai.start_autonomous_engines()
    # 标记已就绪（由 autonomous_run 的主循环确认）
    try:
        os.makedirs(os.path.dirname(READY_FILE), exist_ok=True)
        with open(READY_FILE, 'w', encoding='utf-8') as f:
            f.write(str(time.time()))
        print(f"[autonomous_run] ready -> {READY_FILE}", flush=True)
    except Exception:
        pass

    # 立即写入一次启动心跳（确保健康检测不出现缺失）
    try:
        write_heartbeat(UNIFIED_HB_NAME, mode='startup', status='ready', pid=os.getpid())
        print('[autonomous_run] startup heartbeat written', flush=True)
    except Exception:
        pass

    # 启动心跳写入任务，供外部监控使用（每30秒更新一次统一 heartbeats/autonomous_run.json）
    LEGACY_FILE = os.path.join(ROOT, 'autonomous_heartbeat.json')

    async def _heartbeat_loop():
        while True:
            try:
                # 基础心跳（轻量）
                write_heartbeat(UNIFIED_HB_NAME, mode='loop', loop='steady')
                # 兼容旧路径写入（不保证字段完全一致）
                try:
                    with open(LEGACY_FILE, 'w', encoding='utf-8') as lf:
                        json.dump({'timestamp': time.time(), 'pid': os.getpid()}, lf)
                except Exception:
                    pass
            except Exception:
                pass
            await asyncio.sleep(30)

    asyncio.create_task(_heartbeat_loop())
    # 启动双色球历史循环评估的周期任务（默认每天执行一次）
    async def _ssq_cycle_loop():
        # 最小单位：一轮闭环完成后即可再次启动。将默认间隔设为0（可通过环境变量覆盖）。
        try:
            interval = int(os.getenv('SSQ_CYCLE_INTERVAL_SECONDS', '0'))
        except Exception:
            interval = 0
        loop_count = 0
        last_error = None
        last_autorl_ts = 0.0
        last_vis_ts = 0.0
        while True:
            try:
                # 在后台线程执行，避免阻塞事件循环
                start_ts = time.time()
                await asyncio.to_thread(
                        run_ssq_cycle_and_summarize,
                        'ssq_history.csv',
                        'closed-loop',
                        {
                            # 默认取消尝试上限（0 或负数视为不限），改用按时间控制
                            'max_attempts_per_issue': int(os.getenv('SSQ_MAX_ATTEMPTS_PER_ISSUE', '0')),
                            'consult_external': os.getenv('SSQ_CONSULT_EXTERNAL', '0') == '1',
                            # 每期时间上限（秒）：默认5秒，可在 /etc/default/xuanji-ai 调整
                            'max_seconds_per_issue': float(os.getenv('SSQ_MAX_SECONDS_PER_ISSUE', '5')),
                        },
                    )
                loop_count += 1
                # 写入 heartbeat，记录上次完成时间与耗时与轮次
                try:
                    os.makedirs(os.path.dirname(UNIFIED_HB_PATH), exist_ok=True)
                    dur = max(0.0, time.time() - start_ts)
                    rich_hb = {
                        'last_completed': time.time(),
                        'duration_seconds': dur,
                        'loop_count': loop_count,
                        'last_error': None,
                        'next_interval_sec': int(max(0, interval)),
                        'last_autorl_ts': float(last_autorl_ts or 0.0),
                        'last_visual_ts': float(last_vis_ts or 0.0),
                        'pid_file': os.path.abspath(PID_FILE),
                        'ready_file': os.path.abspath(READY_FILE),
                        'adapt_file': os.path.abspath(ADAPT_FILE),
                    }
                    # 统一心跳（丰富字段）
                    write_heartbeat(UNIFIED_HB_NAME, mode='ssq_cycle', **rich_hb)
                    # 兼容旧路径
                    try:
                        with open(LEGACY_FILE, 'w', encoding='utf-8') as lf:
                            legacy = {'timestamp': time.time(), 'pid': os.getpid(), 'loop_count': loop_count}
                            json.dump(legacy, lf)
                    except Exception:
                        pass
                    print(f"[autonomous_run] unified heartbeat updated", flush=True)
                except Exception:
                    pass
                # 在每轮闭环结束后，触发批量复盘与优化（如果脚本存在）
                try:
                    replay_script = 'ssq_batch_replay_learn.py'
                    optimizer_script = 'optimize_models.py'
                    if os.path.exists(replay_script):
                        subprocess.run([sys.executable, replay_script], check=False)
                    if os.path.exists(optimizer_script):
                        subprocess.run([sys.executable, optimizer_script], check=False)
                    # 低频触发 AutoRL（轻量版 PBT + 元指标门控），默认最短间隔12小时
                    try:
                        _maybe_run_autorl()
                        # 记录最后一次 AutoRL 时间戳
                        if os.path.exists(_AUTORL_STAMP):
                            with open(_AUTORL_STAMP, 'r', encoding='utf-8') as f:
                                last_autorl_ts = float((f.read() or '0').strip() or '0')
                    except Exception:
                        pass
                    # 低频刷新可视化（汇总最新复盘/权重/AutoRL best），默认最短间隔6小时
                    try:
                        _maybe_generate_visualizations()
                        if os.path.exists(_VIS_STAMP):
                            with open(_VIS_STAMP, 'r', encoding='utf-8') as f:
                                last_vis_ts = float((f.read() or '0').strip() or '0')
                    except Exception:
                        pass
                except Exception:
                    # 复盘/优化步骤的异常不应导致主循环退出，记录到错误日志并更新 heartbeat
                    last_error = traceback.format_exc()[:4096]
                    try:
                        os.makedirs(os.path.dirname(ERR_LOG), exist_ok=True)
                        with open(ERR_LOG, 'a', encoding='utf-8') as ef:
                            ef.write(f"[{time.ctime()}] Exception in replay/optimize:\n")
                            ef.write(last_error + "\n\n")
                    except Exception:
                        pass
                    write_heartbeat(UNIFIED_HB_NAME, mode='ssq_cycle_error', loop_count=loop_count, last_error=last_error[:512])
            except Exception:
                # 捕获主循环异常，记录并在 heartbeat 中写入 last_error
                last_error = traceback.format_exc()[:8192]
                try:
                    os.makedirs(os.path.dirname(ERR_LOG), exist_ok=True)
                    with open(ERR_LOG, 'a', encoding='utf-8') as ef:
                        ef.write(f"[{time.ctime()}] main loop error:\n")
                        ef.write(last_error + "\n\n")
                except Exception:
                    pass
                write_heartbeat(UNIFIED_HB_NAME, mode='main_loop_error', loop_count=loop_count, last_error=last_error[:512])
            # 可选：根据上一轮耗时与配置进行自适应调整下一轮间隔
            try:
                if _autoadapt is not None:
                    new_interval = _autoadapt.compute_next_interval(
                        status_path=UNIFIED_HB_PATH,
                        cfg={
                            'min_seconds': int(os.getenv('SSQ_ADAPT_MIN_SECONDS', '0')),
                            'max_seconds': int(os.getenv('SSQ_ADAPT_MAX_SECONDS', '3600')),
                            'default_seconds': int(os.getenv('SSQ_CYCLE_INTERVAL_SECONDS', '0')),
                        },
                        out_path=ADAPT_FILE,
                    )
                    if isinstance(new_interval, (int, float)):
                        interval = int(max(0, new_interval))
            except Exception:
                pass
            # 支持0秒间隔：上一轮结束后立即进入下一轮（请谨慎评估资源占用）
            await asyncio.sleep(max(0, interval))
    asyncio.create_task(_ssq_cycle_loop())
    while True:
        # 每30秒自动生成周期运营报告
        subprocess.run(['python', 'system_monitor_report.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(30)

if __name__ == "__main__":
    _ensure_single_instance_or_exit()
    asyncio.run(main())

# --------- 附加：AutoRL 调度（低频） ---------
_AUTORL_STAMP = os.path.join('reports', 'autorl_runs', 'last_run.txt')

def _maybe_run_autorl():
    """根据时间间隔触发一次轻量 AutoRL 运行。失败不影响主流程。"""
    try:
        min_hours = float(os.getenv('AUTORL_MIN_INTERVAL_HOURS', '12'))
    except Exception:
        min_hours = 12.0
    now = time.time()
    last = 0.0
    try:
        if os.path.exists(_AUTORL_STAMP):
            with open(_AUTORL_STAMP, 'r', encoding='utf-8') as f:
                last = float((f.read() or '0').strip() or '0')
    except Exception:
        last = 0.0
    if (now - last) < (min_hours * 3600.0):
        return  # 未到间隔
    os.makedirs(os.path.dirname(_AUTORL_STAMP), exist_ok=True)
    # 运行轻量 AutoRL：使用较小种群与代数，限制训练步数
    try:
        subprocess.run([sys.executable, '-m', 'autorl.runner', '--population', '8', '--generations', '4', '--train-steps', '250', '--eval-steps', '250'], check=False)
    except Exception:
        pass


# --------- 附加：Visualization 调度（低频） ---------
_VIS_STAMP = os.path.join('reports', 'visualization', 'last_gen.txt')

def _maybe_generate_visualizations():
    """按时间间隔运行 reports/generate_visualizations.py。失败不影响主流程。"""
    try:
        min_hours = float(os.getenv('VIS_MIN_INTERVAL_HOURS', '6'))
    except Exception:
        min_hours = 6.0
    now = time.time()
    last = 0.0
    try:
        if os.path.exists(_VIS_STAMP):
            with open(_VIS_STAMP, 'r', encoding='utf-8') as f:
                last = float((f.read() or '0').strip() or '0')
    except Exception:
        last = 0.0
    if (now - last) < (min_hours * 3600.0):
        return
    script = os.path.join('reports', 'generate_visualizations.py')
    if os.path.exists(script):
        try:
            subprocess.run([sys.executable, script], check=False)
        except Exception:
            pass
    try:
        os.makedirs(os.path.dirname(_VIS_STAMP), exist_ok=True)
        with open(_VIS_STAMP, 'w', encoding='utf-8') as f:
            f.write(str(now))
    except Exception:
        pass
    # 更新时间戳
    try:
        with open(_AUTORL_STAMP, 'w', encoding='utf-8') as f:
            f.write(str(now))
    except Exception:
        pass
