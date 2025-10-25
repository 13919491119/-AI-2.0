"""
自主模式脚本：持续运行AI系统
增加单实例守护：通过 PID 文件避免重复启动。
"""
import asyncio
import os
import atexit
import signal
from celestial_nexus import CelestialNexusAI
from ssq_cycle_runner import run_ssq_cycle_and_summarize


import subprocess

PID_FILE = os.path.join(os.getcwd(), 'autonomous_run.pid')

def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def _write_pid_file():
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True) if os.path.dirname(PID_FILE) else None
    with open(PID_FILE, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))

def _remove_pid_file():
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
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
    # 启动双色球历史循环评估的周期任务（默认每天执行一次）
    async def _ssq_cycle_loop():
        # 最小单位：一轮闭环完成后即可再次启动。将默认间隔设为0（可通过环境变量覆盖）。
        interval = int(os.getenv('SSQ_CYCLE_INTERVAL_SECONDS', '0'))
        while True:
            try:
                # 在后台线程执行，避免阻塞事件循环
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
