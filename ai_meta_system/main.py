import argparse
import asyncio
import os
import atexit
import signal
import sys
import time
from typing import Optional

# 复用现有的 autonomous_run 作为核心引擎
import autonomous_run as _core
try:
    # 可选启动本地 HTTP 健康检查服务（由 ai_meta_health 提供）
    import ai_meta_health
except Exception:
    ai_meta_health = None


def run():
    """
    启动 AI智能体元学习体系：
    - 单实例守护
    - 启动预测闭环（含复盘/优化/快照）
    - 低频触发 AutoRL 与可视化刷新（已集成在 autonomous_run 中）
    """
    _core._ensure_single_instance_or_exit()
    # 如果可用，则在后台启动健康检查服务（默认 127.0.0.1:5001）
    try:
        if ai_meta_health is not None:
            host = os.getenv('AI_HEALTH_HOST', '127.0.0.1')
            port = int(os.getenv('AI_HEALTH_PORT', '5001'))
            ai_meta_health.start_in_thread(host=host, port=port)
    except Exception:
        pass
    asyncio.run(_core.main())


def main():
    parser = argparse.ArgumentParser(description="AI智能体元学习体系 - 一键启动入口")
    parser.add_argument("--print-config", action="store_true", help="仅打印当前关键配置与间隔，不启动")
    args = parser.parse_args()

    # 打印关键信息
    cfg = {
        "SSQ_CYCLE_INTERVAL_SECONDS": os.getenv("SSQ_CYCLE_INTERVAL_SECONDS", "0"),
        "SSQ_MAX_ATTEMPTS_PER_ISSUE": os.getenv("SSQ_MAX_ATTEMPTS_PER_ISSUE", "0"),
        "SSQ_MAX_SECONDS_PER_ISSUE": os.getenv("SSQ_MAX_SECONDS_PER_ISSUE", "5"),
        "AUTORL_MIN_INTERVAL_HOURS": os.getenv("AUTORL_MIN_INTERVAL_HOURS", "12"),
        "VIS_MIN_INTERVAL_HOURS": os.getenv("VIS_MIN_INTERVAL_HOURS", "6"),
        "AUTORL_PROMOTE": os.getenv("AUTORL_PROMOTE", "1"),
        "AUTORL_PROMOTE_STRATEGY": os.getenv("AUTORL_PROMOTE_STRATEGY", "promote"),
        "AUTORL_BLEND_ALPHA": os.getenv("AUTORL_BLEND_ALPHA", "0.05"),
        "AUTORL_PROMOTE_TARGET_WEIGHT": os.getenv("AUTORL_PROMOTE_TARGET_WEIGHT", "0.6"),
        "AUTORL_REPLACE_WEIGHT": os.getenv("AUTORL_REPLACE_WEIGHT", "0.85"),
        "AUTORL_PROMOTE_MIN_DELTA": os.getenv("AUTORL_PROMOTE_MIN_DELTA", "0.02"),
        "AUTORL_PROMOTE_LB_DELTA": os.getenv("AUTORL_PROMOTE_LB_DELTA", "0.02"),
    }

    if getattr(args, 'print_config', False):
        print("AI智能体元学习体系 关键配置：")
        for k, v in cfg.items():
            print(f"  {k}={v}")
        return

    # 正式启动：写入 ai_meta_system.pid（放在仓库根）并注册退出清理
    pid_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai_meta_system.pid'))
    try:
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        print(f"[ai_meta_system] wrote PID {os.getpid()} -> {pid_file}", flush=True)
        # 写一个 started 标记，便于判断模块进程已启动
        started_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai_meta_system.started'))
        try:
            with open(started_file, 'w', encoding='utf-8') as sf:
                sf.write(str(time.time()))
            print(f"[ai_meta_system] started -> {started_file}", flush=True)
        except Exception:
            pass
    except Exception:
        pass

    def _cleanup_pid(*_args):
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except Exception:
            pass
        try:
            started_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai_meta_system.started'))
            if os.path.exists(started_file):
                os.remove(started_file)
        except Exception:
            pass

    atexit.register(_cleanup_pid)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, lambda *_: (_cleanup_pid(), sys.exit(0)))
        except Exception:
            pass

    # 启动主循环
    run()


if __name__ == "__main__":
    main()
