#!/usr/bin/env python3
"""
Score and select top-10 SSQ combinations per AI fusion outputs (and include other method coverage).
Output: outputs/top10_ssq_2025130.json and outputs/top10_ssq_2025130.md
"""
import json
from pathlib import Path
from collections import Counter
import math

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'outputs'
OUTDIR.mkdir(exist_ok=True)

INPUT = OUTDIR / 'ssq_ai_fusion_2025130.jsonl'
METHOD_FILES = {
    '小六爻': OUTDIR / 'ssq_xiaoliuyao_2025130.jsonl',
    '小六壬': OUTDIR / 'ssq_xiaoliuren_2025130.jsonl',
    '奇门遁甲': OUTDIR / 'ssq_qimen_2025130.jsonl',
    '紫微斗数': OUTDIR / 'ssq_ziwei_2025130.jsonl',
    'AI融合': OUTDIR / 'ssq_ai_fusion_2025130.jsonl'
}

# load ai fusion candidates
candidates = []
if INPUT.exists():
    with INPUT.open('r', encoding='utf-8') as f:
        for line in f:
            try:
                it = json.loads(line)
                reds = tuple(sorted(int(x) for x in it['reds']))
                blue = int(it['blue'])
                candidates.append({'reds':reds,'blue':blue})
            except Exception:
                pass

# load method combos for coverage
method_combos = {}
for name, p in METHOD_FILES.items():
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

# global freq counters (from previous analysis outputs/stats)
# fallback: compute from all method files if stats missing
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

# scoring function: weighted sum of features
# features: method_coverage_count (how many methods include this combo),
# red_popularity_score (avg freq of reds), blue_pop_score, odd_even_balance_score, span_score

def score_combo(reds, blue):
    # method coverage
    coverage = sum(1 for s in method_combos.values() if reds in s)
    # red popularity
    red_pop = sum(red_global.get(r,0) for r in reds) / (len(reds) or 1)
    # blue pop
    blue_pop = blue_global.get(blue,0)
    # odd/even balance (closer to 3:3 better)
    odds = sum(1 for r in reds if r%2==1)
    balance = 1 - abs(3-odds)/3  # 1 is perfect 3:3, lower otherwise
    # span (preferred moderate spans: penalize too small or too large)
    span = reds[-1]-reds[0]
    span_score = 1 - abs(20-span)/20  # best around span=20
    # unique dispersion (count of distinct decades)
    decades = len(set((r-1)//10 for r in reds))
    decade_score = decades/6
    # final weighted score
    score = (
        2.5 * coverage +
        0.8 * (red_pop) +
        0.5 * blue_pop +
        1.2 * balance +
        0.9 * span_score +
        0.6 * decade_score
    )
    # normalize a bit
    return score

# score all candidates
scored = []
for it in candidates:
    s = score_combo(it['reds'], it['blue'])
    scored.append({'reds': it['reds'], 'blue': it['blue'], 'score': round(s,4)})

# sort and pick top 10, ensure uniqueness
scored.sort(key=lambda x: (-x['score'], x['reds']))
top10 = []
seen = set()
for it in scored:
    key = (it['reds'], it['blue'])
    if key in seen:
        continue
    top10.append(it)
    seen.add(key)
    if len(top10) >= 10:
        break

# save outputs
with (OUTDIR / 'top10_ssq_2025130.json').open('w', encoding='utf-8') as f:
    json.dump(top10, f, ensure_ascii=False, indent=2)

with (OUTDIR / 'top10_ssq_2025130.md').open('w', encoding='utf-8') as f:
    f.write('# Top 10 SSQ 候选（期 2025130，AI评分）\n\n')
    f.write('| 排名 | 红球 | 蓝球 | 得分 | 覆盖方法数 | 主要原因说明 |\n')
    f.write('|---:|---|---:|---:|---:|---|\n')
    for i,it in enumerate(top10,1):
        coverage = sum(1 for s in method_combos.values() if it['reds'] in s)
        # reason summary
        reasons = []
        if coverage>0:
            reasons.append(f'被{coverage}种方法覆盖')
        # high freq reds
        avg_red_freq = sum(red_global.get(r,0) for r in it['reds'])/6
        if avg_red_freq > 5:
            reasons.append('红球历史热度高')
        # balance
        odds = sum(1 for r in it['reds'] if r%2==1)
        if abs(3-odds)==0:
            reasons.append('奇偶平衡良好')
        # span
        span = it['reds'][-1]-it['reds'][0]
        if 12<=span<=26:
            reasons.append('跨度适中')
        if not reasons:
            reasons = ['综合评分高']
        f.write(f'| {i} | {" ".join(map(str,it["reds"]))} | {it["blue"]} | {it["score"]} | {coverage} | {"; ".join(reasons)} |\n')

print('Wrote top10 ->', OUTDIR / 'top10_ssq_2025130.json')
print('Wrote md ->', OUTDIR / 'top10_ssq_2025130.md')

if __name__ == '__main__':
    pass
