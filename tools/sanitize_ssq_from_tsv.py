#!/usr/bin/env python3
"""
用权威 TSV (reports/双色球) 重写 ssq_history.csv：
 - 仅保留 TSV 中存在的期号，移除其他测试/脏数据期号。
 - 自动备份原 CSV。
"""
from __future__ import annotations

import os, csv, shutil
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
TSV_PATH = os.path.join(ROOT, 'reports', '双色球')
CSV_PATH = os.path.join(ROOT, 'ssq_history.csv')


def load_tsv(path: str) -> Dict[str, Tuple[List[int], int]]:
    res: Dict[str, Tuple[List[int], int]] = {}
    if not os.path.exists(path):
        return res
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 5:
                continue
            period = parts[0].strip()
            if not period.isdigit():
                continue
            reds_s = parts[3].strip()
            blue_s = parts[4].strip()
            try:
                reds = [int(x) for x in reds_s.split(',') if x.strip()]
                blue = int(blue_s)
            except Exception:
                continue
            if len(reds) == 6 and 1 <= blue <= 16:
                res[period] = (reds, blue)
    return res


def rewrite_csv_from_tsv(tsv_map: Dict[str, Tuple[List[int], int]]) -> str:
    if not tsv_map:
        raise SystemExit('TSV 为空或不可读，放弃重写。')
    bak = CSV_PATH + '.bak.sanitize'
    if os.path.exists(CSV_PATH):
        try:
            shutil.copy2(CSV_PATH, bak)
        except Exception:
            pass
    periods = sorted(tsv_map.keys())
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['期号','红1','红2','红3','红4','红5','红6','蓝'])
        for p in periods:
            reds, blue = tsv_map[p]
            w.writerow([p] + [str(x) for x in reds] + [str(blue)])
    return bak


def main():
    tsv_map = load_tsv(TSV_PATH)
    bak = rewrite_csv_from_tsv(tsv_map)
    print(f'rewritten ssq_history.csv from TSV, backup: {bak}, rows: {len(tsv_map)}')


if __name__ == '__main__':
    main()
