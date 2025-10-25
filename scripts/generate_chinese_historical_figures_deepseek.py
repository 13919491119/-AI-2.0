"""
自动调用 DeepSeek LLM 批量生成中国历史人物数据，标准格式：姓名、朝代、主要成就、简介。
"""
import json
from deepseek_api import deepseek_chat

OUTPUT_PATH = "../person_data_deepseek.json"

PROMPT = (
    "请生成100位中国历史人物的标准化数据，每位包含：姓名、朝代、主要成就、简介。"
    "输出格式为JSON数组，每个元素结构如下："
    "{\"name\":\"姓名\",\"dynasty\":\"朝代\",\"achievement\":\"主要成就\",\"summary\":\"简介\"}"
    "，不要包含多余内容。"
)

def main():
    result = deepseek_chat(PROMPT)
    # 解析并保存
    try:
        data = json.loads(result)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(data)} 条历史人物数据到 {OUTPUT_PATH}")
    except Exception as e:
        print("解析或保存失败：", e)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            f.write(result)
        print("原始内容已保存，需人工检查格式。")

if __name__ == "__main__":
    def main():
        from deepseek_api import DeepseekAPI
        try:
            api = DeepseekAPI()
        except Exception as e:
            print("API密钥未配置或初始化失败：", e)
            return
        messages = [
            {"role": "system", "content": "你是中国历史人物知识专家，输出严格JSON格式。"},
            {"role": "user", "content": PROMPT}
        ]
        try:
            resp = api.chat(messages)
            result = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            data = json.loads(result)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"已保存 {len(data)} 条历史人物数据到 {OUTPUT_PATH}")
        except Exception as e:
            print("API调用或解析失败：", e)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                f.write(str(resp))
            print("原始内容已保存，需人工检查格式。")

    if __name__ == "__main__":
        main()
