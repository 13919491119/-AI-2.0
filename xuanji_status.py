import requests

API_URL = "http://localhost:8000/run_xuanji_ai"  # 如部署在云端，请替换为实际IP

def check_status():
    test_inputs = [
        "系统状态",
        "当前周期",
        "学习成果",
        "自我升级情况"
    ]
    for text in test_inputs:
        try:
            resp = requests.post(API_URL, json={"input": text}, timeout=30)
            result = resp.json().get("result", "")
            print(f"【检测项】{text}\n【返回内容】{result}\n{'-'*40}")
        except Exception as e:
            print(f"【检测项】{text}\n【错误】{e}\n{'-'*40}")

if __name__ == "__main__":
    print("开始检测玄机AI2.0自我运营、自学习、自升级状态...\n")
    check_status()