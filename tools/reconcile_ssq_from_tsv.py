#!/usr/bin/env python3
"""
对比 reports/双色球（TSV）与 ssq_history.csv 的开奖数据是否一致；
默认仅检测（dry-run），可通过 --apply 选项修复不一致（覆盖对应期号）。

用法：
  python tools/reconcile_ssq_from_tsv.py           # 仅检测差异
  python tools/reconcile_ssq_from_tsv.py --apply   # 备份并覆盖修复
"""
from __future__ import annotations

import os, sys, csv, shutil
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
            # 期号	开奖日期	星期	红球(逗号)	蓝球
            if len(parts) < 5:
                continue
            period = parts[0].strip()
            if not period.isdigit():
                # 跳过表头或无效行
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


def load_csv(path: str) -> List[List[str]]:
    rows: List[List[str]] = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\n')
            if not line:
                continue
            parts = line.split(',')
            rows.append(parts)
    return rows


def is_header(row: List[str]) -> bool:
    if not row:
        return False
    return row[0] in ('期号', 'period')


def compare(tsv_map: Dict[str, Tuple[List[int], int]], csv_rows: List[List[str]]):
    """返回 (存在但不一致的列表, 存在且一致的数量, 缺失的数量)。"""
    mismatches: List[Tuple[str, Tuple[List[int], int], Tuple[List[int], int]]] = []
    present_equal = 0
    missing = 0
    for period, (t_reds, t_blue) in tsv_map.items():
        found = False
        for row in csv_rows:
            if is_header(row):
                continue
            if not row or not row[0].isdigit():
                continue
            if row[0] != period:
                continue
            found = True
            try:
                c_reds = [int(x) for x in row[1:7]]
                c_blue = int(row[7])
            except Exception:
                mismatches.append((period, (t_reds, t_blue), ([], -1)))
                break
            if c_reds == t_reds and c_blue == t_blue:
                present_equal += 1
            else:
                mismatches.append((period, (t_reds, t_blue), (c_reds, c_blue)))
            break
        if not found:
            missing += 1
    return mismatches, present_equal, missing


def apply_fix(csv_rows: List[List[str]], tsv_map: Dict[str, Tuple[List[int], int]]) -> List[List[str]]:
    idx: Dict[str, int] = {}
    for i, row in enumerate(csv_rows):
        if is_header(row):
            continue
        if row and row[0].isdigit():
            idx[row[0]] = i
    # 覆盖已有期号；缺失的期号选择追加
    out = [r[:] for r in csv_rows]
    header_present = any(is_header(r) for r in out)
    for p, (reds, blue) in tsv_map.items():
        rec = [p] + [str(x) for x in reds] + [str(blue)]
        if p in idx:
            out[idx[p]] = rec
        else:
            out.append(rec)
    # 确保表头在顶行（若存在）
    if header_present and not is_header(out[0]):
        # 将第一个出现的表头行移到顶部
        for i, r in enumerate(out):
            if is_header(r):
                hdr = out.pop(i)
                out.insert(0, hdr)
                break
    return out


def main():
    apply = '--apply' in sys.argv
    tsv_map = load_tsv(TSV_PATH)
    csv_rows = load_csv(CSV_PATH)
    mismatches, present_equal, missing = compare(tsv_map, csv_rows)
    print(f"TSV期号总数: {len(tsv_map)}")
    print(f"CSV中数值一致的期号: {present_equal}")
    print(f"CSV缺失的期号: {missing}")
    print(f"CSV存在但不一致的期号: {len(mismatches)}")
    if mismatches:
        print("\n前20条不一致示例:")
        for period, (t_reds, t_blue), (c_reds, c_blue) in mismatches[:20]:
            print(f"  期号 {period}: TSV={t_reds}+{t_blue}  CSV={c_reds}+{c_blue}")

    if apply:
        if not csv_rows:
            print("CSV不存在或为空，无法覆盖。")
            sys.exit(2)
        backup = CSV_PATH + '.bak'
        shutil.copy2(CSV_PATH, backup)
        fixed = apply_fix(csv_rows, tsv_map)
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            for row in fixed:
                w.writerow(row)
        print(f"已按 TSV 修复并写回 CSV，备份: {backup}")


if __name__ == '__main__':
    main()
