import requests # pyright: ignore[reportMissingModuleSource]
import os

class DeepseekAPI:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com/v1"):
        # 默认集成用户提供的 key
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or "sk-cae93ab77e4645ef90fe84198db898bf"
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
        resp = requests.post(url, headers=self.headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def reasoner(self, messages, temperature=0.7, max_tokens=2048):
        return self.chat(messages, model="deepseek-reasoner", temperature=temperature, max_tokens=max_tokens)

# 用法示例：
# api = DeepseekAPI(api_key="your-key")
# result = api.chat([
#     {"role": "system", "content": "你是AI助手。"},
#     {"role": "user", "content": "请用一句话介绍自己。"}
# ])
# print(result)
