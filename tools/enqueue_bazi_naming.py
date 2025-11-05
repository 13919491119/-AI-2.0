#!/usr/bin/env python3
"""
将起名请求写入队列：queue/bazi_naming.jsonl
- 解决中文转义和并发写入：使用 json.dumps + fcntl.flock(APPEND + LOCK_EX)
- 参数：--surname --bazi [--gender female|male|neutral] [--count 10] [--style neutral] [--single 0/1]
"""
import argparse
import json
import os
from pathlib import Path
import sys

QUEUE = Path(__file__).resolve().parent.parent / 'queue' / 'bazi_naming.jsonl'
QUEUE.parent.mkdir(parents=True, exist_ok=True)

def main():
    p = argparse.ArgumentParser(description='Enqueue a BaZi naming task')
    p.add_argument('--surname', required=True, help='姓氏，如 刘')
    p.add_argument('--bazi', required=True, help='八字文本，如 辛酉年 丁未月 壬午日 戊午时')
    p.add_argument('--gender', default='neutral', choices=['female','male','neutral'])
    p.add_argument('--count', type=int, default=10)
    p.add_argument('--style', default='neutral')
    p.add_argument('--single', type=int, default=0, help='是否单名：1 单名，0 双名')
    args = p.parse_args()

    payload = {
        'surname': args.surname,
        'bazi': args.bazi,
        'gender': args.gender,
        'count': args.count,
        'style': args.style,
        'single': bool(args.single),
    }

    try:
        import fcntl
        with open(QUEUE, 'a', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        print(f"enqueued -> {QUEUE}")
    except Exception as e:
        print(f"enqueue failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
