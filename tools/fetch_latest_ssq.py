#!/usr/bin/env python3
"""
增量采集最新一期双色球数据并追加到 ssq_history.csv。
默认使用模拟数据（方便内网/离线环境），也可通过环境变量或本地文件切换为真实数据源：
  - 模式：FETCH_MODE=mock|file
  - 当 FETCH_MODE=file 时，从 data/latest_ssq.json 读取形如：
    {"period":"2025123","reds":[1,2,3,4,5,6],"blue":7}
由 supervisor 每日/开奖日调度执行。
"""
from __future__ import annotations

import os
import csv
import json
import random
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
CSV = os.path.join(ROOT, 'ssq_history.csv')
DATA_DIR = os.path.join(ROOT, 'data')
LATEST_FILE = os.path.join(DATA_DIR, 'latest_ssq.json')


def read_last_period(csv_path: str) -> str | None:
    if not os.path.exists(csv_path):
        return None
    last = None
    with open(csv_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if not parts or not parts[0].isdigit():
                continue
            last = parts[0]
    return last


def mock_fetch(next_period: str | None) -> dict:
    # 生成一个“看起来合理”的期号
    if next_period and next_period.isdigit():
        period = str(int(next_period) + 1)
    else:
        period = datetime.utcnow().strftime('%Y%j')  # 年+儒略日，避免撞号
    reds = sorted(random.sample(range(1,34), 6))
    blue = random.randint(1,16)
    return {"period": period, "reds": reds, "blue": blue}


def file_fetch(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not (isinstance(data, dict) and data.get('period') and data.get('reds') and data.get('blue')):
        raise ValueError('invalid latest_ssq.json')
    return {"period": str(data['period']), "reds": list(map(int, data['reds'])), "blue": int(data['blue'])}


def append_row(csv_path: str, period: str, reds: list[int], blue: int) -> bool:
    # 避免重复追加
    last = read_last_period(csv_path)
    if last == period:
        return False
    new = not os.path.exists(csv_path)
    with open(csv_path, 'a', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['期号','红1','红2','红3','红4','红5','红6','蓝'])
        w.writerow([period] + reds + [blue])
    return True


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    mode = os.getenv('FETCH_MODE', 'mock').strip().lower()
    last = read_last_period(CSV)
    if mode == 'file':
        payload = file_fetch(LATEST_FILE)
    else:
        payload = mock_fetch(last)
    ok = append_row(CSV, payload['period'], payload['reds'], payload['blue'])
    print(json.dumps({"status": "ok", "appended": ok, "payload": payload}, ensure_ascii=False))


if __name__ == '__main__':
    main()
