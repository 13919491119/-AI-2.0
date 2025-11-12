#!/usr/bin/env python3
"""简单蓝球专模：历史频率 + 条件（和值分桶）频率

输出:
 - outputs/blue_model_topk_<period>.json
 - outputs/blue_model_summary_<period>.md

用法: python3 tools/blue_ball_model.py --period 2025130 --history 200 --topk 5
"""
import argparse
import csv
import json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
HIST_CSV = ROOT / 'ssq_history.csv'


def load_history(none_ok=False):
    if not HIST_CSV.exists():
        if none_ok:
            return {}
        raise FileNotFoundError(f'{HIST_CSV} not found')
    hist = {}
    with HIST_CSV.open('r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            pid = row['期号']
            reds = [int(row[f'红{i}']) for i in range(1,7)]
            blue = int(row['蓝'])
            hist[pid] = {'reds': reds, 'blue': blue}
    return hist


def bucket_sum(reds):
    s = sum(reds)
    return (s // 10) * 10


def build_blue_model(history, recent_n=200):
    keys = sorted(history.keys())
    recent = keys[-recent_n:]
    overall = Counter()
    cond = defaultdict(Counter)
    for k in recent:
        rec = history[k]
        b = rec['blue']
        overall[b] += 1
        bk = bucket_sum(rec['reds'])
        cond[bk][b] += 1
    return overall, cond, recent


def predict_for_period(period, history, overall, cond, recent, topk=5):
    # If period in history, use its reds to compute conditional; otherwise use mean bucket
    if period in history:
        reds = history[period]['reds']
        bk = bucket_sum(reds)
    else:
        # default to median bucket of recent
        bks = [bucket_sum(history[k]['reds']) for k in recent]
        bk = sorted(bks)[len(bks)//2]

    total_overall = sum(overall.values()) or 1
    # score = 0.6 * overall_freq + 0.4 * cond_freq (normalized)
    scores = {}
    for b in range(1,17):
        o = overall.get(b, 0) / total_overall
        c_total = sum(cond[bk].values()) or 0
        c = (cond[bk].get(b,0) / c_total) if c_total>0 else 0
        scores[b] = 0.6 * o + 0.4 * c
    # sort
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:topk], bk


def write_outputs(period, ranked, bk):
    OUT.mkdir(parents=True, exist_ok=True)
    topk_path = OUT / f'blue_model_topk_{period}.json'
    summary_md = OUT / f'blue_model_summary_{period}.md'
    data = [{'blue': b, 'score': float(s)} for b,s in ranked]
    topk_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f'# 蓝球专模汇总 - 期 {period}', '', f'- 条件分桶 (和值十位): {bk}', '', '## Top 蓝球候选']
    for b,s in ranked:
        lines.append(f'- 蓝 {b}: score={s:.4f}')
    summary_md.write_text('\n'.join(lines), encoding='utf-8')
    return topk_path, summary_md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', default='2025130')
    ap.add_argument('--history', type=int, default=200)
    ap.add_argument('--topk', type=int, default=5)
    args = ap.parse_args()

    history = load_history()
    overall, cond, recent = build_blue_model(history, recent_n=args.history)
    ranked, bk = predict_for_period(args.period, history, overall, cond, recent, topk=args.topk)
    topk_path, summary_md = write_outputs(args.period, ranked, bk)
    print('Wrote', topk_path, summary_md)


if __name__ == '__main__':
    main()
