"""
test_api.py
API集成测试：FastAPI接口
"""
import unittest
from fastapi.testclient import TestClient
from celestial_nexus.api import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
    def test_discover_and_patterns(self):
        r = self.client.post("/discover?n=10")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/patterns?threshold=0.7")
        self.assertEqual(r.status_code, 200)
        self.assertIn("patterns", r.json())
    def test_fuse(self):
        r = self.client.post("/fuse", json={"system_scores": {"小六壬":0.8,"六爻":0.8,"八字":0.8,"奇门遁甲":0.8,"紫微斗数":0.8}})
        self.assertEqual(r.status_code, 200)
        self.assertIn("fusion_score", r.json())

if __name__ == "__main__":
    unittest.main()
