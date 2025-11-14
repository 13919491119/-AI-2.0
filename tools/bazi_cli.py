#!/usr/bin/env python3
"""命令行工具：八字排盘（包装 `tools.bazi_lib.BaziCalculator`）。

示例：
  python3 tools/bazi_cli.py --year 1976 --month 11 --day 13 --hour 11 --format json
"""
import argparse
import json
from tools.bazi_lib import BaziCalculator


def to_md(res: dict) -> str:
    lines = ["# 八字排盘结果"]
    lines.append(f"- 年柱: {res.get('年柱')}")
    lines.append(f"- 月柱: {res.get('月柱')}")
    lines.append(f"- 日柱: {res.get('日柱')}")
    lines.append(f"- 时柱: {res.get('时柱')}")
    lines.append(f"- precision: {res.get('precision')}")
    if 'note' in res:
        lines.append(f"- note: {res.get('note')}")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description='八字（四柱）计算 CLI')
    p.add_argument('--year', type=int, required=True)
    p.add_argument('--month', type=int, required=True)
    p.add_argument('--day', type=int, required=True)
    p.add_argument('--hour', type=int, required=True, help='24小时制整数小时')
    p.add_argument('--minute', type=int, default=0)
    p.add_argument('--format', choices=['json', 'md'], default='json')
    args = p.parse_args()

    calc = BaziCalculator()
    res = calc.calculate(args.year, args.month, args.day, args.hour, args.minute)

    if args.format == 'json':
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(to_md(res))


if __name__ == '__main__':
    main()
