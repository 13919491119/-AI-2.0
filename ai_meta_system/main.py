import argparse
import asyncio
import os
from typing import Optional

# 复用现有的 autonomous_run 作为核心引擎
import autonomous_run as _core


def run():
    """
    启动 AI智能体元学习体系：
    - 单实例守护
    - 启动预测闭环（含复盘/优化/快照）
    - 低频触发 AutoRL 与可视化刷新（已集成在 autonomous_run 中）
    """
    _core._ensure_single_instance_or_exit()
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

    # 正式启动
    run()


if __name__ == "__main__":
    main()
