
import openai # pyright: ignore[reportMissingImports]
import os
from dotenv import load_dotenv # pyright: ignore[reportMissingImports]

load_dotenv()


# 兼容 openai>=1.0.0 新API
class ChatGPTAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def chat(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=2048):
        # openai>=1.0.0: openai.resources.chat.completions.create
        try:
            resp = openai.resources.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp
        except AttributeError:
            # 兼容旧版openai
            resp = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return resp

# 用法示例：
# api = ChatGPTAPI()
# result = api.chat([
#     {"role": "system", "content": "你是双色球智能分析师。"},
#     {"role": "user", "content": "请为2025114期预测一组红球6个、蓝球1个，并给出分析理由。"}
# ])
# print(result["choices"][0]["message"]["content"])