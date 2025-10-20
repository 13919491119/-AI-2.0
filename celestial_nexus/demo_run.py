from celestial_nexus.ai_core import CelestialNexusAI

async def main():
    ai = CelestialNexusAI()
    await ai.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())