#!/usr/bin/env python3
"""
Generate predictions for a range of historical periods by calling
tools/generate_ssq_predictions.py for each period.

Usage:
  python3 tools/generate_historical_predictions.py --periods 100 --n 200

This will take the last N periods from ssq_history.csv and for each period
generate n predictions per method and write them to outputs/ as
  ssq_<method>_<period>.jsonl

Be cautious: large N*n may create many files and use CPU/disk.
"""

from pathlib import Path
import subprocess
import argparse
import csv


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--periods', type=int, default=100, help='number of recent periods to generate')
    p.add_argument('--n', type=int, default=200, help='predictions per method per period')
    return p.parse_args()


def read_periods(csv_path: Path):
    rows = []
    with csv_path.open('r', encoding='utf-8') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) < 8:
                continue
            rows.append(parts[0])
    return rows


def main():
    args = parse_args()
    csvp = Path('ssq_history.csv')
    if not csvp.exists():
        print('ssq_history.csv not found')
        return
    periods = read_periods(csvp)
    if not periods:
        print('no periods found in ssq_history.csv')
        return
    recent = periods[-args.periods:]

    for i, period in enumerate(recent, 1):
        print(f'[{i}/{len(recent)}] Generating for period {period} (n={args.n})')
        res = subprocess.run(['python3', 'tools/generate_ssq_predictions.py', '--period', period, '--n', str(args.n)], capture_output=True, text=True)
        if res.returncode != 0:
            print(f'Error generating for {period}:', res.stderr)
            # continue to next
        else:
            print(res.stdout.splitlines()[-3:])

    print('Done generating historical predictions')


if __name__ == '__main__':
    main()
