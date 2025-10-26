#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Dict

# 兼容直接运行：将项目根加入路径
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ssq_predict_cycle import SSQPredictCycle
from models.adapters import LiuyaoModel, LiurenModel, QimenModel, CulturalDLModel, AIModel


def main():
    cycle = SSQPredictCycle('ssq_history.csv')
    models = [
        LiuyaoModel(cycle),
        LiurenModel(cycle),
        QimenModel(cycle),
        CulturalDLModel(cycle),
        AIModel(cycle),
    ]

    results: Dict[str, Dict] = {}
    # 先训练需要训练的模型
    for m in models:
        try:
            log = m.train(None)
            results.setdefault(m.name, {})['train_log'] = log
        except Exception as e:
            results.setdefault(m.name, {})['train_log'] = f"train error: {e}"

    # 回放评估（扩展指标）
    history = cycle.history
    def metrics_for(model):
        topk_hits = {1: 0, 3: 0, 6: 0}
        pos_recall_total = 0
        pos_recall_hit = 0
        blue_hits = 0
        total = 0
        # 滚动稳定性：分段窗口命中率
        window = max(20, len(history)//5) if len(history) >= 100 else max(10, len(history)//4 or 10)
        windows = []  # 每窗口的命中率（完全命中）
        w_cnt = 0
        w_hit = 0
        for idx, (reds, blue) in enumerate(history):
            pr, pb = model.predict({"issue_idx": idx})
            total += 1
            # Top-k：红球交集大小 >= k 判定为 top-k 命中
            inter = len(set(pr) & set(reds))
            for k in (1, 3, 6):
                if inter >= k:
                    topk_hits[k] += 1
            # 位置召回（逐位相等）统计：红球无序，使用集合交集比例近似
            pos_recall_total += 6
            pos_recall_hit += inter
            # 蓝球独立命中率
            if int(pb) == int(blue):
                blue_hits += 1
            # 完全命中计入窗口
            if set(pr) == set(reds) and int(pb) == int(blue):
                w_hit += 1
            w_cnt += 1
            if w_cnt >= window:
                windows.append(w_hit / float(w_cnt))
                w_cnt, w_hit = 0, 0
        if w_cnt > 0:
            windows.append(w_hit / float(w_cnt))
        metrics = {
            "total": total,
            "topk_hit_rate": {str(k): (topk_hits[k] / float(total)) for k in (1, 3, 6)},
            "pos_recall": (pos_recall_hit / float(pos_recall_total)) if pos_recall_total else 0.0,
            "blue_hit_rate": (blue_hits / float(total)) if total else 0.0,
            "window_size": window,
            "stability": {
                "min": min(windows) if windows else 0.0,
                "max": max(windows) if windows else 0.0,
                "mean": (sum(windows)/len(windows)) if windows else 0.0,
                "samples": len(windows),
            }
        }
        return metrics

    for m in models:
        try:
            results[m.name]['metrics_ext'] = metrics_for(m)
        except Exception as e:
            results[m.name]['metrics_ext'] = {"error": str(e)}

    os.makedirs('reports', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = f'reports/ssq_models_eval_{ts}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[eval] saved to {path}")
    # 写入 latest_eval.json 供运营报告使用
    try:
        with open('reports/latest_eval.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


if __name__ == '__main__':
    main()
