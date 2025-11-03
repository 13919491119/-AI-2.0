#!/usr/bin/env python3
"""
签名脚本：对 `reports/weights_history/*.json` 中缺少 `sha256` 字段的文件计算 SHA256 并写回。
"""
import os
import json
import hashlib

DIR = 'reports/weights_history'

if not os.path.isdir(DIR):
    print('weights_history 目录不存在，跳过')
    raise SystemExit(0)

for fn in os.listdir(DIR):
    if not fn.endswith('.json'):
        continue
    path = os.path.join(DIR, fn)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        print('无法读取', path)
        continue
    if 'sha256' in data:
        print('已签名，跳过', fn)
        continue
    content = json.dumps(data, ensure_ascii=False, indent=2)
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
    data['sha256'] = sha
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('已签名', fn)
    except Exception as e:
        print('写回失败', fn, e)
