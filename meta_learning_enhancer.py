#!/usr/bin/env python3
"""元学习结果增强器
读取 deep_learning_cycle_results.jsonl ，为缺失字段补齐：
 - metric 占位（当前随机示例）
 - model_version 简单自增
 - quality_tag 基于随机/类型打标签
输出： deep_learning_cycle_results_enriched.jsonl
可周期运行（由守护进程监控或 cron/systemd 定时）。
"""
import os
import json
import random
from typing import List, Dict

SRC = 'deep_learning_cycle_results.jsonl'
DST = 'deep_learning_cycle_results_enriched.jsonl'


def load_lines(path: str) -> List[Dict]:
    items = []
    if not os.path.exists(path):
        return items
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def enrich(items: List[Dict]) -> List[Dict]:
    enriched = []
    version_counter = 1
    for it in items:
        it = dict(it)
        if 'model_version' not in it:
            it['model_version'] = version_counter
            version_counter += 1
        if 'metric' not in it:
            # 伪指标：区分不同类型基础权重
            base = {'ssq': 0.5, 'person': 0.7, 'question': 0.6}.get(it.get('type'), 0.55)
            it['metric'] = round(base + random.uniform(-0.05, 0.05), 4)
        if 'quality_tag' not in it:
            it['quality_tag'] = 'ok' if it['metric'] >= 0.55 else 'review'
        enriched.append(it)
    return enriched


def write_lines(path: str, items: List[Dict]):
    with open(path, 'w', encoding='utf-8') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')


def main():
    data = load_lines(SRC)
    if not data:
        print('[meta_learning_enhancer] 无数据可增强')
        return
    enhanced = enrich(data)
    write_lines(DST, enhanced)
    print(f'[meta_learning_enhancer] 已写入增强结果 {DST} ({len(enhanced)} 条)')

if __name__ == '__main__':
    main()
