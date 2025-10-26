import requests # pyright: ignore[reportMissingModuleSource]

API_URL = "http://localhost:8000/run_xuanji_ai"

def test_xuanji_ai2(input_text):
    resp = requests.post(API_URL, json={"input": input_text}, timeout=30)
    print(f"输入: {input_text}\n返回: {resp.json().get('result')}")

if __name__ == "__main__":
    # 示例自动化测试
    test_xuanji_ai2("学习成果")
    test_xuanji_ai2("双色球预测")
    test_xuanji_ai2("双色球复盘: 01 02 03 04 05 06|07, 11 12 13 14 15 16|08")
    test_xuanji_ai2("运行玄机AI2.0")
