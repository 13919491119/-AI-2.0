"""
演示脚本：快速体验AI系统主要功能
"""
import asyncio
from celestial_nexus import CelestialNexusAI

async def main():
    ai = CelestialNexusAI()
    await ai.start_autonomous_engines()
    result = await ai.process_request({
        "query_type": "divination",
        "query_data": {"question": "近期事业发展如何?"}
    })
    print("预测结果:", result)
    status = ai.get_system_status_summary()
    print("系统状态:", status)
    await ai.stop_autonomous_engines()

if __name__ == "__main__":
    asyncio.run(main())
