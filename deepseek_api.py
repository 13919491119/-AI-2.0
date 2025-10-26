import os
import json
from typing import Any, Dict

def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    """POST JSON with 'requests' if available, else fall back to urllib."""
    try:
        import requests  # type: ignore
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # urllib 回退
        import urllib.request
        import urllib.error
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # type: ignore[attr-defined]
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
            # 尝试解析错误响应
            try:
                body = e.read().decode("utf-8")
                return json.loads(body)
            except Exception:
                raise

class DeepseekAPI:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com/v1"):
        """
        DeepSeek API 客户端。

        安全说明：不再内置默认密钥，必须通过参数或环境变量 DEEPSEEK_API_KEY 提供。
        """
        key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not configured. Set environment variable or pass api_key explicitly."
            )
        self.api_key = key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def chat(self, messages, model="deepseek-chat", temperature=0.7, max_tokens=2048):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        return _post_json(url, headers=self.headers, payload=payload, timeout=60)

    def reasoner(self, messages, temperature=0.7, max_tokens=2048):
        return self.chat(messages, model="deepseek-reasoner", temperature=temperature, max_tokens=max_tokens)

# 用法示例：
# api = DeepseekAPI(api_key="your-key")
# result = api.chat([
#     {"role": "system", "content": "你是AI助手。"},
#     {"role": "user", "content": "请用一句话介绍自己。"}
# ])
# print(result)
