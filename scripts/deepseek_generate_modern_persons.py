"""
自动调用DeepSeek API生成近现代100位有影响力人物（含出生年月日），并自动集成到AI数理与文化深度学习推演计划循环。
"""
import requests
import json
import os

def deepseek_generate_persons(api_key, output_path, count=100):
    prompt = f"请用JSON数组格式列出{count}位有影响力的近现代人物，每个元素包含：姓名、国籍、出生年月日（如1900-01-01）、主要成就。不要虚构人物。"
    url = "https://api.deepseek.com/v1/chat/completions"  # 假设API地址，实际请替换
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",  # 实际模型名请替换
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 8000
    }
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    content = resp.json()['choices'][0]['message']['content']
    try:
        persons = json.loads(content)
    except Exception:
        content = content[content.find('['):content.rfind(']')+1]
        persons = json.loads(content)
    with open(output_path, 'w', encoding='utf-8') as f:
        for p in persons:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f"已保存{len(persons)}条人物数据到{output_path}")
    return output_path

def auto_integrate_to_cultural_deep(output_path):
    # 假设 auto_learn_cultural_deep.py 支持读取此jsonl并自动进入推演循环
    # 这里只做触发或软链接/复制，实际可根据主循环脚本接口调整
    import shutil
    target = "person_knowledge_base.txt"  # 假设主循环读取此文件
    shutil.copyfile(output_path, target)
    print(f"已自动集成到AI数理与文化深度学习推演计划历史人物库: {target}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="自动生成并集成近现代人物数据到AI文化深度学习循环")
    parser.add_argument('--output', type=str, default='reports/persons_deepseek.jsonl', help='输出文件路径')
    parser.add_argument('--count', type=int, default=100, help='生成数量')
    parser.add_argument('--api_key', type=str, default=os.getenv('DEEPSEEK_API_KEY'), help='DeepSeek API Key')
    args = parser.parse_args()
    if not args.api_key:
        print("请通过--api_key参数或DEEPSEEK_API_KEY环境变量提供API密钥")
        exit(1)
    out_path = deepseek_generate_persons(args.api_key, args.output, args.count)
    auto_integrate_to_cultural_deep(out_path)
