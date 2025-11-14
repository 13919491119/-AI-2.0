#!/usr/bin/env python3
"""
Backtest SSQ predictions for a single draw.

Loads JSONL prediction lists from outputs/ (files named like
  ssq_<method>_2025130.jsonl)
Compares each prediction to the provided actual draw and writes a
Markdown report and per-method CSV summary into outputs/.

Usage:
  python3 tools/backtest_ssq_predictions.py --reds 1 5 8 14 19 23 --blue 6

If no args provided, defaults to the 2025130 draw used in the session.
"""
from pathlib import Path
import json
import csv
import argparse
from collections import Counter, defaultdict


OUTDIR = Path('outputs')
METHOD_FILES = {
    '小六爻': OUTDIR / 'ssq_xiaoliuyao_2025130.jsonl',
    '小六壬': OUTDIR / 'ssq_xiaoliuren_2025130.jsonl',
    '奇门遁甲': OUTDIR / 'ssq_qimen_2025130.jsonl',
    '紫微斗数': OUTDIR / 'ssq_ziwei_2025130.jsonl',
    'AI融合': OUTDIR / 'ssq_ai_fusion_2025130.jsonl',
}
TOP10_FILE = OUTDIR / 'top10_ssq_2025130.json'


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--reds', nargs=6, type=int, metavar='R', help='6 red numbers', default=[1,5,8,14,19,23])
    p.add_argument('--blue', type=int, help='blue number', default=6)
    return p.parse_args()


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
                # try to skip broken lines
                continue
    return res


def summarize_predictions(preds, actual_reds_set, actual_blue):
    red_match_counter = Counter()
    blue_match_count = 0
    exact_full_matches = 0
    # also track distribution of (red_matches, blue_match)
    joint = Counter()

    for p in preds:
        reds = p.get('reds') or p.get('red') or []
        blue = p.get('blue')
        # ensure ints
        try:
            reds_set = set(int(r) for r in reds)
        except Exception:
            reds_set = set()
        red_matches = len(actual_reds_set & reds_set)
        red_match_counter[red_matches] += 1
        blue_match = (int(blue) == actual_blue) if blue is not None else False
        if blue_match:
            blue_match_count += 1
        if red_matches == 6 and blue_match:
            exact_full_matches += 1
        joint[(red_matches, int(bool(blue_match)))] += 1

    total = max(len(preds), 1)
    return {
        'total': len(preds),
        'red_match_counter': red_match_counter,
        'blue_match_count': blue_match_count,
        'exact_full_matches': exact_full_matches,
        'joint': joint,
    }


def write_csv_stats(method_name, stats, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f'backtest_stats_{method_name}_2025130.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_predictions', stats['total']])
        writer.writerow(['blue_matches', stats['blue_match_count']])
        writer.writerow(['exact_full_matches', stats['exact_full_matches']])
        # red match distribution
        for i in range(7):
            writer.writerow([f'red_matches_{i}', stats['red_match_counter'].get(i, 0)])
        # joint distribution rows
        writer.writerow([])
        writer.writerow(['red_matches', 'blue_match', 'count'])
        for (r, b), c in sorted(stats['joint'].items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([r, b, c])
    return csv_path


def main():
    args = parse_args()
    actual_reds = [int(x) for x in args.reds]
    actual_reds_set = set(actual_reds)
    actual_blue = int(args.blue)

    report_lines = []
    report_lines.append(f'# SSQ 回测报告 — 期 2025130')
    report_lines.append('')
    report_lines.append(f'真实开奖号码（用于回测）：红 {sorted(actual_reds)}，蓝 {actual_blue}')
    report_lines.append('')

    outputs_dir = OUTDIR

    all_method_stats = {}
    for method, path in METHOD_FILES.items():
        preds = load_jsonl(path)
        stats = summarize_predictions(preds, actual_reds_set, actual_blue)
        csv_path = write_csv_stats(method, stats, outputs_dir)
        all_method_stats[method] = (stats, csv_path)
        # write a summary section
        report_lines.append(f'## 方法：{method}')
        report_lines.append(f'- 读取预测数: {stats["total"]}')
        report_lines.append(f'- 蓝球命中数: {stats["blue_match_count"]} ({stats["blue_match_count"]/max(stats["total"],1):.2%})')
        report_lines.append(f'- 红球命中分布:')
        for i in range(7):
            report_lines.append(f'  - {i} 个红球命中: {stats["red_match_counter"].get(i,0)}')
        report_lines.append(f'- 完全命中（6红+蓝）: {stats["exact_full_matches"]}')
        report_lines.append(f'- 详细 joint CSV: {csv_path}')
        report_lines.append('')

    # Top10
    top10 = []
    if TOP10_FILE.exists():
        try:
            with TOP10_FILE.open('r', encoding='utf-8') as f:
                top10 = json.load(f)
        except Exception:
            top10 = []

    report_lines.append('## Top-10 候选（AI 选择）回测')
    if top10:
        top_stats = summarize_predictions(top10, actual_reds_set, actual_blue)
        report_lines.append(f'- Top10 总数: {top_stats["total"]}')
        report_lines.append(f'- Top10 蓝球命中: {top_stats["blue_match_count"]}')
        for i in range(7):
            report_lines.append(f'  - {i} 个红球命中: {top_stats["red_match_counter"].get(i,0)}')
        top_csv = write_csv_stats('top10', top_stats, outputs_dir)
        report_lines.append(f'- Top10 详细 CSV: {top_csv}')
    else:
        report_lines.append('- 未找到 Top-10 文件，跳过 Top10 回测。')

    # write report
    report_path = outputs_dir / 'backtest_2025130_report.md'
    outputs_dir.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print('Backtest complete. Report ->', report_path)
    for method, (stats, csvp) in all_method_stats.items():
        print(f'{method}: total={stats["total"]}, red6+blue={stats["exact_full_matches"]}, blue_matches={stats["blue_match_count"]}')


if __name__ == '__main__':
    main()
