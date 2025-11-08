#!/usr/bin/env python3
"""统一心跳写入工具：
提供函数/脚本写入 heartbeats/<name>.json ，包含 ts、pid、extra。
也可被其他脚本直接调用： from heartbeat_manager import write_heartbeat
"""
import os
import sys
import json
import time

ROOT = os.path.abspath(os.path.dirname(__file__))
HB_DIR = os.path.join(ROOT, 'heartbeats')


def write_heartbeat(name: str, **kwargs):
    os.makedirs(HB_DIR, exist_ok=True)
    data = {'ts': time.time(), 'pid': os.getpid()}
    data.update(kwargs)
    path = os.path.join(HB_DIR, f'{name}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return path


def main():
    if len(sys.argv) < 2:
        print('Usage: heartbeat_manager.py <name> [key=value ...]')
        sys.exit(2)
    name = sys.argv[1]
    extras = {}
    for kv in sys.argv[2:]:
        if '=' in kv:
            k, v = kv.split('=', 1)
            # 尝试将数字转型
            try:
                v_cast = float(v) if '.' in v else int(v)
            except Exception:
                v_cast = v
            extras[k] = v_cast
    path = write_heartbeat(name, **extras)
    print(f'[heartbeat_manager] wrote -> {path}')

if __name__ == '__main__':
    main()
