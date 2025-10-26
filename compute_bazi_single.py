"""
Compute and print a formatted BaZi (八字) for a single Gregorian datetime using local bazi_chart.solar2bazi.
Usage: python3 compute_bazi_single.py 1981 12 18 11 30
"""
import sys
from datetime import datetime

def format_bazi(bazi):
    out = []
    out.append(f"年柱: {bazi.get('year')}")
    out.append(f"月柱: {bazi.get('month')}")
    out.append(f"日柱: {bazi.get('day')}")
    out.append(f"时柱: {bazi.get('hour')}")
    out.append(f"天干: {bazi.get('gan')}")
    out.append(f"地支: {bazi.get('zhi')}")
    out.append(f"生肖: {bazi.get('zodiac')}")
    out.append(f"农历: {bazi.get('lunar')}")
    out.append(f"阳历: {bazi.get('solar')}")
    return '\n'.join(out)

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print('用法: python3 compute_bazi_single.py YEAR MONTH DAY HOUR MINUTE')
        sys.exit(1)
    y, m, d, H, M = map(int, sys.argv[1:6])
    try:
        from bazi_chart import solar2bazi
    except Exception as e:
        print('本地排盘库不可用:', e)
        sys.exit(2)
    bazi = solar2bazi(y, m, d, H, M, 0)
    print(format_bazi(bazi))
