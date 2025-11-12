#!/usr/bin/env python3
"""
Generate detailed score decomposition for Top10 candidates.
Outputs: outputs/top10_ssq_2025130_detailed.json and detailed markdown.
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'outputs'
IN_JSON = OUTDIR / 'top10_ssq_2025130.json'
METHOD_FILES = {
    '小六爻': OUTDIR / 'ssq_xiaoliuyao_2025130.jsonl',
    '小六壬': OUTDIR / 'ssq_xiaoliuren_2025130.jsonl',
    '奇门遁甲': OUTDIR / 'ssq_qimen_2025130.jsonl',
    '紫微斗数': OUTDIR / 'ssq_ziwei_2025130.jsonl',
    'AI融合': OUTDIR / 'ssq_ai_fusion_2025130.jsonl'
}

OUT_JSON = OUTDIR / 'top10_ssq_2025130_detailed.json'
OUT_MD = OUTDIR / 'top10_ssq_2025130_detailed.md'

# load top10
with IN_JSON.open('r', encoding='utf-8') as f:
    top10 = json.load(f)

# load method combos
method_combos = {}
for name,p in METHOD_FILES.items():
    s = set()
    if p.exists():
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    it = json.loads(line)
                    reds = tuple(sorted(int(x) for x in it['reds']))
                    s.add(reds)
                except Exception:
                    pass
    method_combos[name] = s

# build global freq
red_global = Counter()
blue_global = Counter()
for name,p in METHOD_FILES.items():
    if p.exists():
        with p.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    it = json.loads(line)
                    for r in it['reds']:
                        red_global[int(r)] += 1
                    blue_global[int(it['blue'])] += 1
                except Exception:
                    pass

# decompose scoring used earlier
weights = {
    'coverage': 2.5,
    'red_pop': 0.8,
    'blue_pop': 0.5,
    'balance': 1.2,
    'span': 0.9,
    'decade': 0.6
}

def decompose(reds, blue):
    coverage = sum(1 for s in method_combos.values() if tuple(reds) in s)
    red_pop = sum(red_global.get(r,0) for r in reds) / (len(reds) or 1)
    blue_pop = blue_global.get(blue,0)
    odds = sum(1 for r in reds if r%2==1)
    balance = 1 - abs(3-odds)/3
    span = reds[-1]-reds[0]
    span_score = 1 - abs(20-span)/20
    decades = len(set((r-1)//10 for r in reds))
    decade_score = decades/6
    score = (
        weights['coverage']*coverage +
        weights['red_pop']*red_pop +
        weights['blue_pop']*blue_pop +
        weights['balance']*balance +
        weights['span']*span_score +
        weights['decade']*decade_score
    )
    breakdown = {
        'coverage': coverage,
        'coverage_contrib': round(weights['coverage']*coverage,4),
        'red_pop': round(red_pop,4),
        'red_pop_contrib': round(weights['red_pop']*red_pop,4),
        'blue_pop': blue_pop,
        'blue_pop_contrib': round(weights['blue_pop']*blue_pop,4),
        'balance': round(balance,4),
        'balance_contrib': round(weights['balance']*balance,4),
        'span': span,
        'span_score': round(span_score,4),
        'span_contrib': round(weights['span']*span_score,4),
        'decades': decades,
        'decade_score': round(decade_score,4),
        'decade_contrib': round(weights['decade']*decade_score,4),
        'total_score': round(score,4)
    }
    return breakdown

# build detailed list
detailed = []
for it in top10:
    reds = list(it['reds'])
    blue = it['blue']
    breakdown = decompose(reds, blue)
    # which methods cover
    covered_by = [name for name,s in method_combos.items() if tuple(reds) in s]
    detailed.append({
        'reds': reds,
        'blue': blue,
        'breakdown': breakdown,
        'covered_by': covered_by
    })

with OUT_JSON.open('w', encoding='utf-8') as f:
    json.dump(detailed, f, ensure_ascii=False, indent=2)

# write markdown
with OUT_MD.open('w', encoding='utf-8') as f:
    f.write('# Top10 SSQ 详细得分分解（2025130）\n\n')
    for i,d in enumerate(detailed,1):
        f.write(f'## {i}. 红球: {" ".join(map(str,d["reds"]))} 蓝球: {d["blue"]}\n')
        f.write('- 覆盖方法: ' + (', '.join(d['covered_by']) if d['covered_by'] else '无') + '\n')
        b = d['breakdown']
        f.write('- 分项贡献:\n')
        f.write(f'  - 覆盖贡献: {b["coverage_contrib"]} (coverage={b["coverage"]})\n')
        f.write(f'  - 红球热度贡献: {b["red_pop_contrib"]} (avg_red_pop={b["red_pop"]})\n')
        f.write(f'  - 蓝球热度贡献: {b["blue_pop_contrib"]} (blue_pop={b["blue_pop"]})\n')
        f.write(f'  - 奇偶平衡贡献: {b["balance_contrib"]} (balance={b["balance"]})\n')
        f.write(f'  - 跨度贡献: {b["span_contrib"]} (span={b["span"]}, span_score={b["span_score"]})\n')
        f.write(f'  - 十位分布贡献: {b["decade_contrib"]} (decades={b["decades"]}, decade_score={b["decade_score"]})\n')
        f.write(f'- 总评分: {b["total_score"]}\n\n')

print('Wrote detailed json ->', OUT_JSON)
print('Wrote detailed md ->', OUT_MD)
