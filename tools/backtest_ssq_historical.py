#!/usr/bin/env python3
"""
Historical rolling backtest for SSQ predictions.

For the last N draws (from `ssq_history.csv`) tries to find prediction files
under `outputs/` named `ssq_<method>_<期号>.jsonl` and aggregates hit rates
across periods per method. Produces Markdown summary and per-method CSVs.

Usage:
  python3 tools/backtest_ssq_historical.py --periods 200

Options:
  --periods N       number of most recent draws to evaluate (default 200)
  --methods m1 m2   subset of methods to evaluate (defaults to all known)
  --outdir path     outputs directory (default: outputs)
  --alpha a         confidence level for CIs (default 0.95)
  --min-preds p     minimum predictions per period to count that period (default 1)

Note: If prediction files are missing for many periods this script will skip
those periods and report how many were missing per method.
"""

from pathlib import Path
import argparse
import csv
import json
from collections import Counter, defaultdict
import math
import statistics


DEFAULT_METHODS = ['小六爻', '小六壬', '奇门遁甲', '紫微斗数', 'AI融合']
PATTERN = 'ssq_{method}_{period}.jsonl'


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--periods', type=int, default=200)
    p.add_argument('--methods', nargs='*', help='methods to include')
    p.add_argument('--outdir', default='outputs')
    p.add_argument('--alpha', type=float, default=0.95)
    p.add_argument('--min-preds', type=int, default=1)
    return p.parse_args()


def read_history(csv_path: Path):
    rows = []
    if not csv_path.exists():
        raise FileNotFoundError(f'{csv_path} not found')
    with csv_path.open('r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            # expect: 期号,红1,红2,红3,红4,红5,红6,蓝
            if len(parts) < 8:
                continue
            period = parts[0]
            try:
                reds = [int(x) for x in parts[1:7]]
                blue = int(parts[7])
            except Exception:
                continue
            rows.append({'period': period, 'reds': sorted(reds), 'blue': blue})
    return rows


def load_jsonl(path: Path):
    if not path.exists():
        return []
    res = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                res.append(json.loads(line))
            except Exception:
                continue
    return res


def wilson_ci(k, n, alpha=0.95):
    # Wilson score interval for proportion
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    z = {0.9:1.645, 0.95:1.96, 0.99:2.576}.get(round(alpha,2), 1.96)
    denom = 1 + z*z/n
    centre = p + z*z/(2*n)
    margin = z * math.sqrt((p*(1-p) + z*z/(4*n))/n)
    lo = (centre - margin)/denom
    hi = (centre + margin)/denom
    return max(0.0, lo), min(1.0, hi)


def analyze_period(preds, actual_reds_set, actual_blue):
    # returns dict of counters for this prediction list
    red_match_counter = Counter()
    blue_match = 0
    total = 0
    for p in preds:
        reds = p.get('reds') or p.get('red') or []
        blue = p.get('blue')
        try:
            reds_set = set(int(x) for x in reds)
        except Exception:
            reds_set = set()
        rmatch = len(actual_reds_set & reds_set)
        red_match_counter[rmatch] += 1
        if blue is not None and int(blue) == actual_blue:
            blue_match += 1
        total += 1
    return {'total': total, 'red_counter': red_match_counter, 'blue_match': blue_match}


def aggregate_metrics(period_results):
    # period_results: list of per-period analyze_period results
    agg = {'total_preds': 0, 'periods': 0, 'red_counter': Counter(), 'blue_match': 0}
    for r in period_results:
        agg['total_preds'] += r['total']
        agg['periods'] += 1
        agg['blue_match'] += r['blue_match']
        for k,v in r['red_counter'].items():
            agg['red_counter'][k] += v
    return agg


def write_method_csv(outdir: Path, method: str, per_period_results, agg):
    outdir.mkdir(parents=True, exist_ok=True)
    csvp = outdir / f'backtest_historical_{method}.csv'
    with csvp.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['period', 'pred_count', 'blue_matches', 'red0','red1','red2','red3','red4','red5','red6'])
        for pr in per_period_results:
            row = [pr['period'], pr['total'], pr['blue_match']]
            for i in range(7):
                row.append(pr['red_counter'].get(i,0))
            w.writerow(row)
        # write aggregated summary
        w.writerow([])
        w.writerow(['aggregate_total_predictions', agg['total_preds']])
        w.writerow(['periods_evaluated', agg['periods']])
        w.writerow(['aggregate_blue_matches', agg['blue_match']])
        for i in range(7):
            w.writerow([f'agg_red_matches_{i}', agg['red_counter'].get(i,0)])
    return csvp


def main():
    args = parse_args()
    outdir = Path(args.outdir)
    methods = args.methods if args.methods else DEFAULT_METHODS

    history = read_history(Path('ssq_history.csv'))
    if not history:
        print('no ssq_history.csv rows found')
        return

    # take last N draws
    recent = history[-args.periods:]

    summary_lines = []
    summary_lines.append(f'# SSQ 历史回测（最近 {len(recent)} 期）')
    summary_lines.append('')

    # mapping from display method name to file stems used by generator
    file_stems = {
        '小六爻': 'xiaoliuyao',
        '小六壬': 'xiaoliuren',
        '奇门遁甲': 'qimen',
        '紫微斗数': 'ziwei',
        'AI融合': 'ai_fusion'
    }

    for method in methods:
        per_period_results = []
        missing = 0
        for row in recent:
            period = row['period']
            # try the generator stems first (english stems), then Chinese name
            stem = file_stems.get(method, method.replace(' ', '_'))
            path = outdir / PATTERN.format(method=stem, period=period)
            alt_path = outdir / PATTERN.format(method=method, period=period)
            if path.exists():
                preds = load_jsonl(path)
            elif alt_path.exists():
                preds = load_jsonl(alt_path)
            else:
                preds = []
            if len(preds) < args.min_preds:
                missing += 1
                continue
            per = analyze_period(preds, set(row['reds']), row['blue'])
            per['period'] = period
            per_period_results.append(per)

        agg = aggregate_metrics(per_period_results)

        # compute metrics and CI
        total_preds = agg['total_preds']
        total_periods = agg['periods']
        blue_k = agg['blue_match']
        blue_rate = blue_k / total_preds if total_preds else 0.0
        blue_ci = wilson_ci(blue_k, total_preds, alpha=args.alpha)

        # at-least metrics: >=3,4,5,6 reds
        at_least = {}
        for thresh in (3,4,5,6):
            k = sum(v for r,v in agg['red_counter'].items() if r >= thresh)
            rate = k / total_preds if total_preds else 0.0
            at_least[thresh] = (k, rate, wilson_ci(k, total_preds, alpha=args.alpha))

        # write per-method CSV
        csvp = write_method_csv(outdir, method.replace(' ', '_'), per_period_results, agg)

        summary_lines.append(f'## 方法：{method}')
        summary_lines.append(f'- 有效期数: {total_periods}（缺失/跳过: {len(recent)-total_periods}）')
        summary_lines.append(f'- 总预测数: {total_preds}')
        summary_lines.append(f'- 蓝球命中: {blue_k} / {total_preds} = {blue_rate:.4%} (CI {blue_ci[0]:.4%} - {blue_ci[1]:.4%})')
        for t,(k,rate,ci) in at_least.items():
            summary_lines.append(f'- 红球 ≥{t}: {k} / {total_preds} = {rate:.4%} (CI {ci[0]:.4%} - {ci[1]:.4%})')
        summary_lines.append(f'- 详细 CSV: {csvp}')
        summary_lines.append('')

    # write overall report
    report_path = outdir / f'backtest_historical_last{len(recent)}.md'
    outdir.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(summary_lines))

    print('Historical backtest complete. Report ->', report_path)


if __name__ == '__main__':
    main()
