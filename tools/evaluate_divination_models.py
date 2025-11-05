#!/usr/bin/env python3
"""
Evaluate divination-based prediction CSV against actual lottery result.
Reads predictions CSV at predictions/2025-11-02_2115_predictions.csv and writes
comparison CSV and a markdown recap.

Usage: python3 tools/evaluate_divination_models.py
"""
import csv
from pathlib import Path
from collections import defaultdict

PRED_CSV = Path('predictions/2025-11-02_2115_predictions.csv')
COMP_CSV = Path('predictions/2025-11-02_2115_comparison.csv')
RECAP_MD = Path('docs/prediction_recap_20251102.md')

# Actual result provided by user
ACTUAL_REDS = {2,12,13,16,19,25}
ACTUAL_BLUE = 10

def read_predictions(path):
    rows = []
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            reds = [int(r[f'red{i}']) for i in range(1,7)]
            rows.append({
                'method': r['method'],
                'group': int(r['group']),
                'reds': reds,
                'blue': int(r['blue'])
            })
    return rows

def evaluate(preds, actual_reds, actual_blue):
    per_method = defaultdict(lambda: {'red_hits':0,'blue_hits':0,'groups':0,'red_hit_counts':[]})
    total_red_hits = 0
    total_blue_hits = 0
    detailed = []
    for p in preds:
        reds_set = set(p['reds'])
        red_hits = len(reds_set & actual_reds)
        blue_hit = 1 if p['blue']==actual_blue else 0
        per_method[p['method']]['red_hits'] += red_hits
        per_method[p['method']]['blue_hits'] += blue_hit
        per_method[p['method']]['groups'] += 1
        per_method[p['method']]['red_hit_counts'].append(red_hits)
        total_red_hits += red_hits
        total_blue_hits += blue_hit
        detailed.append((p['method'], p['group'], p['reds'], p['blue'], red_hits, blue_hit))
    return per_method, total_red_hits, total_blue_hits, detailed

def write_comparison_csv(detailed, path):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['method','group','reds','blue','matched_reds','blue_hit'])
        for row in detailed:
            method, group, reds, blue, red_hits, blue_hit = row
            writer.writerow([method, group, ' '.join(f'{r:02d}' for r in reds), f'{blue:02d}', red_hits, blue_hit])

def write_recap(per_method, total_red_hits, total_blue_hits, detailed, path):
    lines = []
    lines.append('# 复盘报告：2025-11-02 21:15 预测对比')
    lines.append('')
    lines.append('实际开奖号码（用户提供）：')
    lines.append(f'- 红球: {" ".join(str(x) for x in sorted(ACTUAL_REDS))}')
    lines.append(f'- 蓝球: {ACTUAL_BLUE}')
    lines.append('')
    lines.append('## 总体统计')
    total_groups = len(detailed)
    lines.append(f'- 预测组数: {total_groups}')
    lines.append(f'- 总预测红球数: {total_groups * 6}')
    lines.append(f'- 命中红球总数: {total_red_hits}')
    lines.append(f'- 命中蓝球总数: {total_blue_hits}')
    lines.append('')
    lines.append('## 按方法统计')
    for m, stats in sorted(per_method.items()):
        groups = stats['groups']
        red_hits = stats['red_hits']
        blue_hits = stats['blue_hits']
        avg_red_per_group = sum(stats['red_hit_counts'])/groups if groups else 0
        lines.append(f'- 方法 {m}: 红命中 {red_hits}/{groups*6} ({red_hits/(groups*6)*100:.2f}%), 蓝命中 {blue_hits}/{groups}，平均每组红命中 {avg_red_per_group:.2f}')
    lines.append('')
    lines.append('## 命中详情（每组）')
    lines.append('|method|group|reds|blue|matched_reds|blue_hit|')
    lines.append('|---|---:|---|---:|---:|---:|')
    for row in detailed:
        method, group, reds, blue, red_hits, blue_hit = row
        lines.append(f'|{method}|{group}|{" " .join(f"{r:02d}" for r in reds)}|{blue:02d}|{red_hits}|{blue_hit}|')

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    preds = read_predictions(PRED_CSV)
    per_method, total_red_hits, total_blue_hits, detailed = evaluate(preds, ACTUAL_REDS, ACTUAL_BLUE)
    write_comparison_csv(detailed, COMP_CSV)
    write_recap(per_method, total_red_hits, total_blue_hits, detailed, RECAP_MD)
    print('Wrote comparison CSV to', COMP_CSV)
    print('Wrote recap MD to', RECAP_MD)

if __name__ == '__main__':
    main()
