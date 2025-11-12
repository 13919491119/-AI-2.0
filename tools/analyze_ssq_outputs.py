#!/usr/bin/env python3
"""
Analyze SSQ prediction outputs for period 2025130.
Generates a markdown summary and CSVs with frequency statistics.
"""
import json
from pathlib import Path
from collections import Counter, defaultdict
import csv

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'outputs'
SUMMARY = OUTDIR / 'ssq_summary_2025130.md'
CSV_DIR = OUTDIR / 'stats'
CSV_DIR.mkdir(exist_ok=True)

methods = ['ssq_xiaoliuyao_2025130.jsonl','ssq_xiaoliuren_2025130.jsonl','ssq_qimen_2025130.jsonl','ssq_ziwei_2025130.jsonl','ssq_ai_fusion_2025130.jsonl']
method_names = ['小六爻','小六壬','奇门遁甲','紫微斗数','AI融合']

def load(path):
    items = []
    p = OUTDIR / path
    if not p.exists():
        return items
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            try:
                items.append(json.loads(line))
            except Exception:
                pass
    return items

all_stats = {}
all_sets = {}
red_global = Counter()
blue_global = Counter()

for fname, display in zip(methods, method_names):
    items = load(fname)
    red_counter = Counter()
    combo_counter = Counter()
    blue_counter = Counter()
    combos_list = []
    for it in items:
        reds = tuple(sorted(int(x) for x in it['reds']))
        blue = int(it['blue'])
        combo_counter[reds] += 1
        for r in reds:
            red_counter[r] += 1
            red_global[r] += 1
        blue_counter[blue] += 1
        blue_global[blue] += 1
        combos_list.append(set(reds))
    all_stats[display] = {
        'count': len(items),
        'red_freq': red_counter,
        'combo_freq': combo_counter,
        'blue_freq': blue_counter,
        'combos_list': combos_list
    }
    all_sets[display] = combos_list

# pairwise overlap (Jaccard over top combos)
pair_overlap = {}
for a in method_names:
    pair_overlap[a] = {}
    set_a = set()
    # take top 200 combos by freq
    for c,_ in all_stats[a]['combo_freq'].most_common(200):
        set_a.add(tuple(c))
    for b in method_names:
        if a == b:
            pair_overlap[a][b] = 1.0
            continue
        set_b = set()
        for c,_ in all_stats[b]['combo_freq'].most_common(200):
            set_b.add(tuple(c))
        inter = len(set_a & set_b)
        uni = len(set_a | set_b) if len(set_a | set_b)>0 else 1
        pair_overlap[a][b] = round(inter/uni,4)

# write CSVs: red frequencies per method, blue frequencies per method, top combos per method
for display in method_names:
    # red freq
    rc = all_stats[display]['red_freq']
    with (CSV_DIR / f"red_freq_{display}.csv").open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['red','count'])
        for r,c in rc.most_common():
            writer.writerow([r,c])
    # blue freq
    bc = all_stats[display]['blue_freq']
    with (CSV_DIR / f"blue_freq_{display}.csv").open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['blue','count'])
        for b,c in bc.most_common():
            writer.writerow([b,c])
    # top combos
    cc = all_stats[display]['combo_freq']
    with (CSV_DIR / f"top_combos_{display}.csv").open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['rank','reds','count'])
        for i,(combo,cnt) in enumerate(cc.most_common(200),1):
            writer.writerow([i,','.join(map(str,combo)),cnt])

# global hottest reds and blues
with (CSV_DIR / 'red_global.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['red','count'])
    for r,c in red_global.most_common():
        writer.writerow([r,c])
with (CSV_DIR / 'blue_global.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['blue','count'])
    for b,c in blue_global.most_common():
        writer.writerow([b,c])

# write markdown summary
with SUMMARY.open('w', encoding='utf-8') as f:
    f.write('# 双色球预测结果统计报告（期 2025130）\n\n')
    f.write('生成时间：自动化分析\n\n')
    f.write('## 方法概览\n')
    for display in method_names:
        f.write(f'- {display}: 样本数 {all_stats[display]["count"]}\n')
    f.write('\n')

    f.write('## 每方法 Top-10 红球组合（出现次数/示例）\n')
    for display in method_names:
        f.write(f'### {display}\n')
        f.write('| 排名 | 红球组合 | 出现次数 |\n')
        f.write('|---:|---|---:|\n')
        for i,(combo,cnt) in enumerate(all_stats[display]['combo_freq'].most_common(10),1):
            f.write(f'| {i} | {" ".join(map(str,combo))} | {cnt} |\n')
        f.write('\n')

    f.write('## 红球热度（全方法合并）Top-20\n')
    f.write('| 排名 | 红球 | 计数 |\n')
    f.write('|---:|---|---:|\n')
    for i,(r,c) in enumerate(red_global.most_common(20),1):
        f.write(f'| {i} | {r} | {c} |\n')
    f.write('\n')

    f.write('## 蓝球热度（全方法合并）Top-10\n')
    f.write('| 排名 | 蓝球 | 计数 |\n')
    f.write('|---:|---|---:|\n')
    for i,(b,c) in enumerate(blue_global.most_common(10),1):
        f.write(f'| {i} | {b} | {c} |\n')
    f.write('\n')

    f.write('## 方法间 Top-200 组合重合率 (Jaccard)\n')
    f.write('| 方法 | ' + ' | '.join(method_names) + ' |\n')
    f.write('|---' + '|---'*len(method_names) + '|\n')
    for a in method_names:
        f.write('| '+a)
        for b in method_names:
            f.write(f' | {pair_overlap[a][b]}')
        f.write(' |\n')
    f.write('\n')

    f.write('## 结论与说明\n')
    f.write('- 各方法生成逻辑不同，重合率通常较低（[0-1] 区间），AI 融合方法可以在一定程度上覆盖多方法特征。\n')
    f.write('- 若需历史回测（命中率统计），需提供真实历史开奖数据，我可以基于这些输出自动回测并给出命中率与置信度评估。\n')
    f.write('- 以上 CSV 文件位于 `outputs/stats/`，可直接下载并在 Excel 中分析。\n')

print('Wrote summary ->', SUMMARY)
print('CSV stats ->', CSV_DIR)
print('Done')
