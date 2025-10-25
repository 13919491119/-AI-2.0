# 自动调用 Deepseek API 生成权威八字排盘
import os
from deepseek_api import DeepseekAPI

def get_bazi_deepseek(year, month, day, hour, minute=0, gender=None):
    api = DeepseekAPI()
    prompt = f"请严格按中国权威万年历和八字命理规则，给出阳历{year}年{month}月{day}日{hour}点{minute}分出生的{'女' if gender=='女' else '男'}孩的八字（年柱、月柱、日柱、时柱），只返回四柱，格式如：丙辰、己亥、己巳、庚午。"
    messages = [
        {"role": "system", "content": "你是权威八字排盘专家，严格按中国万年历和八字命理推算。"},
        {"role": "user", "content": prompt}
    ]
    result = api.chat(messages)
    # 解析结果
    content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
    return content

if __name__ == "__main__":
    # 示例：1976年11月13日 11:30 女
    print(get_bazi_deepseek(1976, 11, 13, 11, 30, gender='女'))
