#!/usr/bin/env python3
"""汇总 autonomous loop 日志为 CSV/Markdown 报表

读取 `outputs/loop_logs/loop_<period>_round<k>.md` 并提取每轮每法的 total/blue_hits/full_hits
以及调优产生的最佳权重，输出:
 - outputs/loop_summary.csv
 - outputs/loop_summary.md

用法: python3 tools/collect_loop_metrics.py
"""
import re
from pathlib import Path
import csv
import json
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / 'outputs' / 'loop_logs'
OUT_DIR = ROOT / 'outputs'


def parse_log(path: Path):
    txt = path.read_text(encoding='utf-8')
    # Round and period
    m = re.search(r"# 自主循环 Round\s*(\d+) - 期\s*(\S+)", txt)
    if m:
        round_no = int(m.group(1))
        period = m.group(2)
    else:
        round_no = None
        period = None

    # 最佳权重行
    best_weights = None
    m = re.search(r"最佳权重:\s*(\{.*\})", txt)
    if m:
        try:
            best_weights = json.loads(m.group(1).replace("'", '"'))
        except Exception:
            best_weights = m.group(1)

    methods = {}
    # 每法行, 形如: - xiaoliuyao: total=1000 blue_hits=37 full_hits=0 red_dist={...}
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith('- ') and ':' in line:
            # remove leading '- '
            body = line[2:]
            parts = body.split(':', 1)
            if len(parts) != 2:
                continue
            name = parts[0].strip()
            rest = parts[1]
            # find total, blue_hits, full_hits
            ti = {}
            m_tot = re.search(r"total=(\d+)", rest)
            m_blue = re.search(r"blue_hits=(\d+)", rest)
            m_full = re.search(r"full_hits=(\d+)", rest)
            if m_tot:
                ti['total'] = int(m_tot.group(1))
            if m_blue:
                ti['blue_hits'] = int(m_blue.group(1))
            if m_full:
                ti['full_hits'] = int(m_full.group(1))
            if ti:
                methods[name] = ti

    return {
        'file': str(path.name),
        'round': round_no,
        'period': period,
        'best_weights': best_weights,
        'methods': methods,
    }


def main():
    logs = sorted(LOG_DIR.glob('loop_*.md'))
    rows = []
    rounds = []
    for p in logs:
        rec = parse_log(p)
        rounds.append(rec)
        rno = rec['round']
        per = rec['period']
        bw = rec['best_weights']
        for mname, stats in rec['methods'].items():
            rows.append({
                'round': rno,
                'period': per,
                'method': mname,
                'total': stats.get('total', ''),
                'blue_hits': stats.get('blue_hits', ''),
                'full_hits': stats.get('full_hits', ''),
                'best_weights': json.dumps(bw, ensure_ascii=False) if bw else ''
            })

    # write CSV
    csv_path = OUT_DIR / 'loop_summary.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['round','period','method','total','blue_hits','full_hits','best_weights'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # produce markdown summary
    md_path = OUT_DIR / 'loop_summary.md'
    by_method = {}
    for r in rows:
        m = r['method']
        by_method.setdefault(m, []).append(int(r['blue_hits']) if r['blue_hits']!='' else 0)

    lines = []
    lines.append('# 自主循环阶段性指标汇总')
    lines.append('')
    lines.append('## 每方法蓝球命中统计（每轮 blue_hits）')
    lines.append('')
    for m, vals in by_method.items():
        lines.append(f'- {m}: count={len(vals)}, mean={mean(vals):.2f}, median={median(vals):.2f}, min={min(vals)}, max={max(vals)}')
    lines.append('')
    lines.append('## 原始明细（见 loop_summary.csv）')
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    print(f'Wrote {csv_path} and {md_path}')


if __name__ == '__main__':
    main()
