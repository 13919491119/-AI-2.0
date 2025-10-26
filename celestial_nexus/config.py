"""
config.py
集中式配置管理，支持高可用部署与参数热更新
"""
import threading

class Config:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.reload()
            return cls._instance
    def reload(self):
        # 可扩展为从文件/环境变量/远程配置中心加载
        self.settings = {
            "pattern_threshold": 0.7,
            "monitor_interval": 60,
            "upgrade_check_interval": 3600
        }
    def get(self, key, default=None):
        return self.settings.get(key, default)
    def set(self, key, value):
        self.settings[key] = value
