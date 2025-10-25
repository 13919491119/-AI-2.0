#!/usr/bin/env python3
"""
从系统文件 reports/双色球 导入真实开奖期号、日期、号码到 ssq_history.csv。
格式（TSV）：
  期号	开奖日期	星期	红球号码(逗号分隔)	蓝球
  示例：2025115	2025-10-07	二	02,03,08,19,24,30	02
注意：文件中可能存在表头行、顺序非严格、以及前置历史数据；导入器会按期号去重追加。
"""
from __future__ import annotations

import os
import csv
from typing import Tuple, List

ROOT = os.path.dirname(os.path.dirname(__file__))
TSV_PATH = os.path.join(ROOT, 'reports', '双色球')
CSV_PATH = os.path.join(ROOT, 'ssq_history.csv')


def read_existing_periods(csv_path: str) -> set[str]:
    periods: set[str] = set()
    if not os.path.exists(csv_path):
        return periods
    with open(csv_path, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split(',')
            if not parts or not parts[0].isdigit():
                continue
            periods.add(parts[0])
    return periods


def parse_tsv(path: str) -> List[Tuple[str, List[int], int]]:
    out: List[Tuple[str, List[int], int]] = []
    if not os.path.exists(path):
        return out
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split('\t')
            # 容错：跳过无效/表头行
            if len(parts) < 5:
                continue
            period = parts[0].strip()
            if not period.isdigit():
                continue
            reds_text = parts[3].strip()
            blue_text = parts[4].strip()
            try:
                reds = [int(x) for x in reds_text.split(',') if x.strip()]
                blue = int(blue_text)
            except Exception:
                continue
            if len(reds) == 6 and 1 <= blue <= 16:
                out.append((period, reds, blue))
    return out


def append_new_records(csv_path: str, records: List[Tuple[str, List[int], int]]) -> int:
    existing = read_existing_periods(csv_path)
    to_write = [(p, r, b) for (p, r, b) in records if p not in existing]
    if not to_write:
        return 0
    new_file = not os.path.exists(csv_path)
    with open(csv_path, 'a', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(['期号','红1','红2','红3','红4','红5','红6','蓝'])
        for period, reds, blue in to_write:
            w.writerow([period] + reds + [blue])
    return len(to_write)


def is_draw_window_cst(now=None) -> bool:
    """按中国福利彩票双色球开奖日（周二/周四/周日）在北京时间 21:30-22:30 之间才导入。
    可在开发/联调时使用 IMPORT_ANYTIME=1 覆盖。
    """
    from datetime import datetime, timezone, timedelta
    tz_cst = timezone(timedelta(hours=8))
    now_cst = (now or datetime.utcnow()).astimezone(tz_cst)
    # 周二=1 周四=3 周日=6（Python: Mon=0..Sun=6）
    if now_cst.weekday() not in (1, 3, 6):
        return False
    hhmm = now_cst.hour * 100 + now_cst.minute
    # 收紧到 21:30-22:30，更贴近实际开奖时段
    return 2130 <= hhmm <= 2230


def _post_import_hooks(imported_count: int, imported_periods: list[str]) -> None:
    """导入后：评估、状态落盘、权重历史记录（轻量，可容错）。"""
    import time
    import json
    from datetime import datetime

    # 1) 快速评估（不必持久化到 Markdown），输出 JSON 报告并同步 latest_eval.json
    latest_eval_path = None
    try:
        try:
            from ssq_evaluate import evaluate_recent
            report = evaluate_recent(window=200)
        except Exception:
            report = None
        if report:
            os.makedirs(os.path.join(ROOT, 'reports'), exist_ok=True)
            ts = time.strftime('%Y%m%d_%H%M%S')
            eval_json = os.path.join(ROOT, 'reports', f'ssq_eval_{ts}.json')
            with open(eval_json, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            latest_eval_path = os.path.join(ROOT, 'reports', 'latest_eval.json')
            # 覆盖 latest_eval.json 软链/文件
            try:
                # 如果存在旧软链或文件，先删除
                if os.path.lexists(latest_eval_path):
                    os.remove(latest_eval_path)
                # 创建软链指向最新文件；若不支持则回退复制
                rel_target = os.path.basename(eval_json)
                os.symlink(rel_target, latest_eval_path)
            except Exception:
                # 回退为复制
                try:
                    with open(eval_json, 'r', encoding='utf-8') as src, open(latest_eval_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                except Exception:
                    latest_eval_path = None
    except Exception:
        latest_eval_path = None

    # 2) 记录权重历史（若存在）
    try:
        weights_path = os.path.join(ROOT, 'ssq_strategy_weights.json')
        if os.path.exists(weights_path):
            with open(weights_path, 'r', encoding='utf-8') as f:
                wobj = json.load(f)
            os.makedirs(os.path.join(ROOT, 'reports'), exist_ok=True)
            hist_path = os.path.join(ROOT, 'reports', 'ssq_weights_history.jsonl')
            rec = {
                'ts': datetime.utcnow().isoformat() + 'Z',
                'weights': wobj.get('weights'),
                'fusion': wobj.get('fusion'),
            }
            with open(hist_path, 'a', encoding='utf-8') as hf:
                hf.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # 3) 训练/更新深度文化模型（可容错）
    try:
        from cultural_deep_model import CulturalDeepModel
        from ssq_data import SSQDataManager
        out_path = os.getenv('SSQ_CULDL_PATH', os.path.join(ROOT, 'models', 'cultural_deep.joblib'))
        dm = SSQDataManager(csv_path=CSV_PATH)
        mdl = CulturalDeepModel()
        try:
            win = int(os.getenv('SSQ_CULDL_WINDOW', '5000'))
        except Exception:
            win = 5000
        hist = dm.history[-win:] if win and len(dm.history) > win else dm.history
        if mdl.fit(hist):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            mdl.save(out_path)
    except Exception:
        pass

    # 4) 状态文件（供前端/静态页读取）
    try:
        status_dir = os.path.join(ROOT, 'static')
        os.makedirs(status_dir, exist_ok=True)
        status_path = os.path.join(status_dir, 'ssq_import_status.json')
        status_obj = {
            'imported_count': imported_count,
            'imported_periods': imported_periods,
            'latest_eval': ('reports/' + os.path.basename(latest_eval_path)) if latest_eval_path else None,
            'updated_at': datetime.utcnow().isoformat() + 'Z',
        }
        with open(status_path, 'w', encoding='utf-8') as sf:
            json.dump(status_obj, sf, ensure_ascii=False, indent=2)
    except Exception:
        pass


def main():
    # 若设置了 IMPORT_ANYTIME=1，则跳过开奖时间窗口限制
    if os.getenv('IMPORT_ANYTIME', '0') != '1':
        if not is_draw_window_cst():
            print("imported=0 (skip: not in draw window CST)")
            return
    records = parse_tsv(TSV_PATH)
    existing_before = read_existing_periods(CSV_PATH)
    n = append_new_records(CSV_PATH, records)
    # 计算本次真正导入的期号列表
    imported_periods = []
    if n > 0:
        existing_after = read_existing_periods(CSV_PATH)
        imported_periods = sorted(list(existing_after - existing_before))
    print(f"imported={n}")
    # 可通过环境变量强制执行后置钩子（即使没有新数据），便于联调/手动触发
    if n > 0 or os.getenv('FORCE_POST_HOOKS', '0') == '1':
        _post_import_hooks(n, imported_periods)


if __name__ == '__main__':
    main()
