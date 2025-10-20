import pytest
from celestial_nexus.ai_core import CelestialNexusAI

@pytest.mark.asyncio
async def test_learning_engine():
    ai = CelestialNexusAI()
    patterns = await ai.learning_engine.discover_patterns()
    assert len(patterns) > 0

@pytest.mark.asyncio
async def test_monitoring_engine():
    ai = CelestialNexusAI()
    health = await ai.monitoring_engine.check_health()
    assert "score" in health