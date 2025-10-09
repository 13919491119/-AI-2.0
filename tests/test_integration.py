"""
test_integration.py
测试微信集成、静态网站和系统自检功能
"""
import unittest
import requests
import subprocess
import time
import os


class TestWeChatServer(unittest.TestCase):
    """测试微信服务器集成"""
    
    @classmethod
    def setUpClass(cls):
        """启动测试前准备"""
        # 确保核心API服务运行
        try:
            resp = requests.get("http://127.0.0.1:8000/health", timeout=2)
        except:
            print("警告: 核心API服务未运行，某些测试可能失败")
    
    def test_wechat_server_exists(self):
        """测试wechat_server.py文件存在"""
        self.assertTrue(os.path.exists("wechat_server.py"))
    
    def test_wechat_health_endpoint(self):
        """测试微信服务健康检查端点"""
        try:
            resp = requests.get("http://127.0.0.1:8088/health", timeout=3)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "healthy")
        except requests.exceptions.RequestException:
            self.skipTest("微信服务未启动")
    
    def test_wechat_report_endpoint(self):
        """测试微信报告端点"""
        try:
            resp = requests.get("http://127.0.0.1:8088/report", timeout=3)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("title", data)
        except requests.exceptions.RequestException:
            self.skipTest("微信服务未启动")


class TestStaticReportServer(unittest.TestCase):
    """测试静态报告服务器"""
    
    def test_static_server_exists(self):
        """测试static_report_server.py文件存在"""
        self.assertTrue(os.path.exists("static_report_server.py"))
    
    def test_static_server_health(self):
        """测试静态服务器健康检查"""
        try:
            resp = requests.get("http://127.0.0.1:8089/health", timeout=3)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "healthy")
        except requests.exceptions.RequestException:
            self.skipTest("静态服务器未启动")


class TestSystemCheck(unittest.TestCase):
    """测试系统自检功能"""
    
    def test_system_check_exists(self):
        """测试system_check.py文件存在"""
        self.assertTrue(os.path.exists("system_check.py"))
    
    def test_system_check_executable(self):
        """测试system_check.py可执行"""
        self.assertTrue(os.access("system_check.py", os.X_OK))
    
    def test_system_check_runs(self):
        """测试系统自检可以运行"""
        result = subprocess.run(
            ["python3", "system_check.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 自检应该返回0（成功）或1（有问题）
        self.assertIn(result.returncode, [0, 1])
        self.assertIn("系统自检", result.stdout)


class TestReportGenerator(unittest.TestCase):
    """测试报告生成器"""
    
    def test_report_generator_exists(self):
        """测试generate_operation_report.py文件存在"""
        self.assertTrue(os.path.exists("generate_operation_report.py"))
    
    def test_report_generation(self):
        """测试报告生成功能"""
        # 清理旧报告
        old_reports = [f for f in os.listdir('.') if f.startswith('operation_report_') and f.endswith('.md')]
        
        try:
            # 生成报告
            result = subprocess.run(
                ["python3", "generate_operation_report.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 检查是否生成了新报告
            new_reports = [f for f in os.listdir('.') if f.startswith('operation_report_') and f.endswith('.md')]
            
            if result.returncode == 0:
                self.assertGreater(len(new_reports), len(old_reports), "应该生成了新报告")
                
                # 验证报告内容
                if new_reports:
                    latest_report = max(new_reports)
                    with open(latest_report, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.assertIn("玄机AI周期运营报告", content)
                        self.assertIn("系统状态概览", content)
        except subprocess.TimeoutExpired:
            self.skipTest("报告生成超时，可能是API服务未启动")


class TestSetupScripts(unittest.TestCase):
    """测试部署脚本"""
    
    def test_wechat_setup_script_exists(self):
        """测试微信部署脚本存在"""
        self.assertTrue(os.path.exists("setup_wechat_integration.sh"))
    
    def test_start_all_script_updated(self):
        """测试start_all.sh包含新服务"""
        with open("start_all.sh", 'r') as f:
            content = f.read()
            self.assertIn("wechat_server.py", content)
            self.assertIn("static_report_server.py", content)
            self.assertIn("system_check.py", content)


if __name__ == "__main__":
    unittest.main()
