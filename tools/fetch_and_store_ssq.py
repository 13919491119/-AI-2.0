#!/usr/bin/env python3
"""
编排流程：
  - 判断是否开奖窗口（可用 IMPORT_ANYTIME=1 覆盖）
  - 调用 providers 抓取最新一期
  - 落库到 SQLite（覆盖同期号），再导出同步 ssq_history.csv
  - 写入 static/ssq_import_status.json
  - 触发后置评估与模型训练（复用 import_ssq_from_tsv 里的钩子）
"""
from __future__ import annotations

import os, json
from typing import Dict, Any
import sys


def is_draw_window_cst(now=None) -> bool:
    from datetime import datetime, timezone, timedelta
    tz_cst = timezone(timedelta(hours=8))
    now_cst = (now or datetime.utcnow()).astimezone(tz_cst)
    if now_cst.weekday() not in (1, 3, 6):
        return False
    hhmm = now_cst.hour * 100 + now_cst.minute
    return 2130 <= hhmm <= 2230


def main():
    ROOT = os.path.dirname(os.path.dirname(__file__))
    # 确保可以以 "tools.*" 形式导入本仓库模块
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    if os.getenv('IMPORT_ANYTIME', '0') != '1':
        if not is_draw_window_cst():
            print(json.dumps({'status': 'skip', 'reason': 'not in draw window CST'}))
            return

    from tools.ssq_providers import fetch_latest
    from ssq_db import upsert_draw, export_csv, sync_from_csv
    from tools.import_ssq_from_tsv import _post_import_hooks  # 直接复用钩子

    # 0) 先将现有 CSV 反向同步到 DB，避免导出时丢失历史
    try:
        sync_from_csv('ssq_history.csv')
    except Exception:
        pass

    payload: Dict[str, Any] = fetch_latest()
    period = payload['period']
    date = payload.get('date')
    week = payload.get('week')
    reds = payload['reds']
    blue = payload['blue']

    # 1) 落库覆盖
    upsert_draw(period, date, week, reds, blue)
    # 2) 导出覆盖 CSV（保证 CSV 和 DB 一致），导出前做一次备份
    try:
        if os.path.exists('ssq_history.csv'):
            import time as _t
            bak = f"ssq_history.csv.bak.{_t.strftime('%Y%m%d_%H%M%S')}"
            try:
                import shutil
                shutil.copy2('ssq_history.csv', bak)
            except Exception:
                pass
    finally:
        export_csv('ssq_history.csv')
    # 3) 状态落盘
    os.makedirs('static', exist_ok=True)
    status = {
        'imported_count': 1,
        'imported_periods': [period],
        'latest_eval': None,
    }
    # 4) 后置钩子：评估/权重历史/训练深度模型/写入状态
    try:
        _post_import_hooks(1, [period])
        # 让 _post_import_hooks 覆盖 static/ssq_import_status.json
    except Exception:
        # 若钩子失败，至少写一个简易状态
        from datetime import datetime
        status['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        with open('static/ssq_import_status.json', 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    print(json.dumps({'status': 'ok', 'period': period, 'reds': reds, 'blue': blue}, ensure_ascii=False))


if __name__ == '__main__':
    from datetime import datetime  # noqa: F401 (used in is_draw_window)
    main()
