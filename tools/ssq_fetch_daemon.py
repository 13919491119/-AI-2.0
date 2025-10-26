#!/usr/bin/env python3
"""
常驻守护：在开奖日（周二/四/日）21:30-22:35 CST 期间，每隔60秒尝试一次抓取并入库；
若当日已成功一次则不再重复。
"""
from __future__ import annotations

import os, time, json
from datetime import datetime, timezone, timedelta


def is_draw_day(now_cst: datetime) -> bool:
    return now_cst.weekday() in (1, 3, 6)


def in_window(now_cst: datetime) -> bool:
    hhmm = now_cst.hour * 100 + now_cst.minute
    return 2130 <= hhmm <= 2235


def main():
    ROOT = os.path.dirname(os.path.dirname(__file__))
    tz_cst = timezone(timedelta(hours=8))
    last_success_date = None
    while True:
        now = datetime.now(tz=tz_cst)
        today = now.strftime('%Y-%m-%d')
        try:
            if is_draw_day(now) and in_window(now) and last_success_date != today:
                # 触发一次
                cmd = f"IMPORT_ANYTIME=1 python3 {os.path.join(ROOT, 'tools', 'fetch_and_store_ssq.py')}"
                print('[daemon] run:', cmd, flush=True)
                rc = os.system(cmd)
                if rc == 0:
                    last_success_date = today
                    print('[daemon] fetched once for', today, flush=True)
        except Exception as e:
            print('[daemon] error:', e, flush=True)
        time.sleep(60)


if __name__ == '__main__':
    main()
