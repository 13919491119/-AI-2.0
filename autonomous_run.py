"""
自主模式脚本：持续运行AI系统
"""
import asyncio
from celestial_nexus import CelestialNexusAI


import subprocess

async def main():
    ai = CelestialNexusAI()
    await ai.start_autonomous_engines()
    while True:
        # 每30秒自动生成周期运营报告
        subprocess.run(['python', 'system_monitor_report.py'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
