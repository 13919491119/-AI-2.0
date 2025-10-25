# gpt_api.py
"""
GPT大模型API集成模块
支持OpenAI GPT-3/4/5/ChatGPT等云端API对接
"""
import requests

class GPTAPI:
    def __init__(self, api_key, api_url="https://api.openai.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, messages, model="gpt-4", temperature=0.7, max_tokens=1024):
        import os
        import json
        os.environ["PYTHONIOENCODING"] = "utf-8"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        # 使用ensure_ascii=False，保证中文等非ASCII字符正确编码
        data_json = json.dumps(data, ensure_ascii=False)
        response = requests.post(self.api_url, headers=headers, data=data_json.encode('utf-8'), timeout=60)
        response.raise_for_status()
        resp_json = response.json()
        return resp_json

# 使用示例：
# gpt = GPTAPI(api_key="sk-xxx")
# messages = [
#     {"role": "system", "content": "你是AI自学习与优化专家。"},
#     {"role": "user", "content": "请基于以下数据提出优化建议..."}
# ]
# result = gpt.chat(messages)
# print(result["choices"][0]["message"]["content"])
