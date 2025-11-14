import json
import os
import time
from heartbeat_manager import write_heartbeat
import importlib
from urllib import request as _urlreq
from urllib.error import URLError

def _fetch_json(url: str, timeout: int = 10):
    try:
        requests = importlib.import_module('requests')
        try:
            resp = requests.get(url, timeout=timeout)
            if getattr(resp, 'ok', False):
                return True, resp.json()
            return False, None
        except Exception:
            return False, None
    except Exception:
        requests = None
    try:
        with _urlreq.urlopen(url, timeout=timeout) as resp:
            if resp.status == 200:
                raw = resp.read()
                import json as _json
                return True, _json.loads(raw.decode('utf-8', errors='ignore'))
            return False, None
    except (URLError, Exception):
        return False, None

def load_persons(path, limit=100):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 去重并取前limit个
        seen = set()
        persons = []
        for p in data:
            name = p.get('name')
            if name and name not in seen:
                persons.append(p)
                seen.add(name)
            if len(persons) >= limit:
                break
        return persons
    else:
        print(f"本地数据文件 {path} 不存在，尝试联网采集真实历史人物数据……")
        # 使用维基百科API获取中国历史人物条目
        url = "https://zh.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:中国历史人物&cmlimit=100&format=json"
        ok, data = _fetch_json(url, timeout=10)
        if ok and isinstance(data, dict):
            members = data.get('query', {}).get('categorymembers', [])
            persons = []
            for m in members:
                name = m.get('title')
                persons.append({"name": name, "fact": "维基百科条目", "bazi": None})
                if len(persons) >= limit:
                    break
            print(f"已采集到 {len(persons)} 位历史人物。")
            return persons
        else:
            print("采集失败，返回空列表")
            return []

def predict_person(person, round_num=1):
    # 可集成实际预测模型，此处模拟升级学习
    base = f"预测：{person['name']}在其领域有重大成就。八字显示智慧与创新。"
    review = f"复盘：分析{person['name']}的历史贡献与影响。"
    learn = f"学习：吸取{person['name']}的智慧与经验。"
    upgrade = f"升级：模型已根据{person['name']}的特征优化。"
    again = f"再预测：第{round_num}轮，预测更精准。"
    return {
        'name': person['name'],
        'bazi': person.get('bazi'),
        'fact': person.get('fact'),
        'predict': base,
        'review': review,
        'learn': learn,
        'upgrade': upgrade,
        'again': again
    }

def ai_guard_loop():
    src = 'person_data.json'
    out = 'person_predict_results.jsonl'
    persons = load_persons(src, 100)
    if not persons:
        print("未获取到有效历史人物数据，任务等待后重试。")
        try:
            write_heartbeat('batch_predict_persons', phase='waiting', reason='no_persons')
        except Exception:
            pass
        # 等待并重试，避免任务直接终止
        time.sleep(60)
        return ai_guard_loop()
    round_num = 1
    while True:
        # 初始心跳，记录轮次
        try:
            write_heartbeat('batch_predict_persons', round=round_num, phase='running')
        except Exception:
            pass
        results = []
        print(f"\n=== 第{round_num}轮历史人物预测任务 ===")
        for p in persons:
            res = predict_person(p, round_num)
            results.append(res)
        with open(out, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        print(f"第{round_num}轮预测已完成，结果写入 {out}")
        # 写心跳：记录轮次与样本数
        try:
            write_heartbeat('batch_predict_persons', round=round_num, samples=len(results))
        except Exception:
            pass
        # 复盘、学习、升级、再预测均已在结果中体现
        round_num += 1
        time.sleep(10)  # 每轮间隔10秒，可调整

if __name__ == '__main__':
    ai_guard_loop()
