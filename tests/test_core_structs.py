import unittest
from core_structs import AutonomousTask, TaskType, TaskStatus, SystemHealthMetrics, HealthStatus

class TestAutonomousTask(unittest.TestCase):
    def test_task_creation(self):
        task = AutonomousTask(
            task_id="T100",
            task_type=TaskType.LIUYAO_ANALYSIS,
            name="单元测试任务",
            status=TaskStatus.PENDING,
            priority=5
        )
        self.assertEqual(task.task_id, "T100")
        self.assertEqual(task.status, TaskStatus.PENDING)

class TestSystemHealthMetrics(unittest.TestCase):
    def test_health_status(self):
        health = SystemHealthMetrics(
            timestamp="2025-10-02 12:00:00",
            cpu_usage=0.5,
            memory_usage=0.5,
            disk_usage=0.5,
            network_latency=10.0,
            health_status=HealthStatus.HEALTHY
        )
        self.assertEqual(health.health_status, HealthStatus.HEALTHY)

if __name__ == "__main__":
    unittest.main()
