import asyncio
from ai_core import CelestialNexusAI

if __name__ == "__main__":
    ai = CelestialNexusAI()
    # 每3秒输出一次完整美化状态报告
    asyncio.run(ai.autonomous_run(cycle_interval=3, report_interval=1))
