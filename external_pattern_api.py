"""
external_pattern_api.py
- 用于对接外部知识服务/AI预测API，动态获取新模式。
- 可根据实际API文档调整。
"""
import requests # pyright: ignore[reportMissingModuleSource]

class ExternalPatternAPI:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key

    def fetch_new_patterns(self, params=None):
        """
        调用外部API获取新模式。如无真实API则返回模拟数据。
        params: dict, 传递给API的参数
        返回: list[dict] 新模式列表
        """
        import datetime, random
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        # 尝试真实API
        try:
            resp = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            patterns = data.get('patterns', [])
            if patterns:
                return patterns
        except Exception:
            pass  # 屏蔽异常打印，直接走模拟分支
        # 返回模拟新模式
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        n = random.randint(1, 2)
        return [
            {
                "pattern_id": f"SIM_{now.replace(' ','_').replace(':','')}_{i}",
                "description": f"模拟新模式_{now}_{i}",
                "score": round(random.uniform(0.7, 0.95), 3),
                "source": "模拟API",
                "created_at": now
            } for i in range(n)
        ]
