"""
test_ai_core.py
单元测试：自主新模式发现与量子融合引擎
"""
import unittest
from celestial_nexus.ai_core import PatternMemory, AutonomousPatternDiscovery, QuantumFusionEngine

class TestAICore(unittest.TestCase):
    def test_pattern_discovery(self):
        memory = PatternMemory()
        discoverer = AutonomousPatternDiscovery(memory)
        discoverer.discover_patterns(100)
        self.assertGreaterEqual(memory.count(), 100)
        self.assertTrue(any(p['confidence'] >= 0.7 for p in memory.patterns))
    def test_quantum_fusion(self):
        fusion = QuantumFusionEngine()
        scores = {k: 0.8 for k in fusion.system_weights}
        result = fusion.fuse(scores)
        self.assertTrue(0 <= result <= 1)

if __name__ == "__main__":
    unittest.main()
