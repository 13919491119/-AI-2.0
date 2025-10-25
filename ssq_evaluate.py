#!/usr/bin/env python3
"""
双色球预测评估脚本
- 读取历史数据与当前策略（含权重融合），计算近期窗口内的命中指标
- 输出 JSON 与 Markdown 到 reports/ 目录

指标：
- 最近N期平均红球命中数、蓝球命中率、Top-K 命中（红球）
- 各策略近N期加权贡献占比（基于 ssq_strategy_weights.json）
"""
from __future__ import annotations

import os
import json
import time
from typing import Dict, List, Tuple

from ssq_predict_cycle import SSQPredictCycle


def evaluate_recent(window: int = 100) -> Dict[str, object]:
    cycle = SSQPredictCycle(data_path='ssq_history.csv')
    history = cycle.history
    if not history:
        return {'error': 'no_history'}

    # 为评估：对每期用当前策略预测该期（非真实可用，但可用于相对表现的稳定观察）
    reds_hits: List[int] = []
    blue_hits: List[int] = []
    # 按策略分别统计
    strategies = ['liuyao', 'liuren', 'qimen', 'ai']
    per_reds_hits: Dict[str, List[int]] = {s: [] for s in strategies}
    per_blue_hits: Dict[str, List[int]] = {s: [] for s in strategies}
    per_issue_details: List[Dict[str, object]] = []
    start = max(0, len(history) - window)
    for idx in range(start, len(history)):
        true_reds, true_blue = history[idx]
        # 使用四个策略一次各出一个候选后做融合
        attempts: List[Dict[str, object]] = []
        for model in strategies:
            if model == 'liuyao':
                pr, pb = cycle.predict_liuyao(idx)
            elif model == 'liuren':
                pr, pb = cycle.predict_liuren(idx)
            elif model == 'qimen':
                pr, pb = cycle.predict_qimen(idx)
            else:
                pr, pb = cycle.predict_ai(idx)
            attempts.append({'strategy': model, 'pred_reds': pr, 'pred_blue': pb})
            # 分策略命中
            rh_m = len(set(pr) & set(true_reds))
            bh_m = 1 if pb == true_blue else 0
            per_reds_hits[model].append(rh_m)
            per_blue_hits[model].append(bh_m)
        fused_reds, fused_blue = cycle._fuse_from_attempts(attempts)
        rh = len(set(fused_reds) & set(true_reds))
        bh = 1 if fused_blue == true_blue else 0
        reds_hits.append(rh)
        blue_hits.append(bh)
        per_issue_details.append({
            'issue_idx': idx,
            'true_reds': sorted(true_reds),
            'true_blue': true_blue,
            'pred_reds': sorted(fused_reds),
            'pred_blue': fused_blue,
            'reds_hit': rh,
            'blue_hit': bh,
        })

    avg_reds_hit = sum(reds_hits) / len(reds_hits) if reds_hits else 0.0
    blue_hit_rate = sum(blue_hits) / len(blue_hits) if blue_hits else 0.0
    # Top-K 红球命中统计（K=2,3,4）
    topk = {
        'red_hit_ge_2': sum(1 for x in reds_hits if x >= 2),
        'red_hit_ge_3': sum(1 for x in reds_hits if x >= 3),
        'red_hit_ge_4': sum(1 for x in reds_hits if x >= 4),
    }
    # 走势数据（最近N期的红/蓝命中序列）
    trend = {
        'reds_hits': reds_hits,
        'blue_hits': blue_hits,
    }

    # 分策略指标汇总
    def _mk_metrics(rhits: List[int], bhits: List[int]) -> Dict[str, object]:
        return {
            'avg_reds_hit': (sum(rhits) / len(rhits)) if rhits else 0.0,
            'blue_hit_rate': (sum(bhits) / len(bhits)) if bhits else 0.0,
            'topk': {
                'red_hit_ge_2': sum(1 for x in rhits if x >= 2),
                'red_hit_ge_3': sum(1 for x in rhits if x >= 3),
                'red_hit_ge_4': sum(1 for x in rhits if x >= 4),
            }
        }

    per_strategy: Dict[str, object] = {}
    for s in strategies:
        per_strategy[s] = _mk_metrics(per_reds_hits[s], per_blue_hits[s])
    # 将融合作为一个条目加入，便于对比
    per_strategy['fusion'] = {
        'avg_reds_hit': avg_reds_hit,
        'blue_hit_rate': blue_hit_rate,
        'topk': topk,
    }

    # 读取权重用于报告
    weights = {}
    try:
        with open('ssq_strategy_weights.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            weights = data.get('weights', {})
    except Exception:
        pass

    report = {
        'window': window,
        'avg_reds_hit': avg_reds_hit,
        'blue_hit_rate': blue_hit_rate,
        'strategy_weights': weights,
        'generated_at': time.time(),
        'topk': topk,
        'trend': trend,
        'per_strategy': per_strategy,
        'details_tail': per_issue_details[-10:],
    }
    return report


def persist(report: Dict[str, object], out_dir: str = 'reports') -> None:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    json_path = os.path.join(out_dir, f'ssq_eval_{ts}.json')
    md_path = os.path.join(out_dir, f'ssq_eval_{ts}.md')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    lines = [
        '# 双色球预测评估摘要',
        '',
        f"- 窗口期数: {report.get('window')}",
        f"- 平均红球命中数: {report.get('avg_reds_hit'):.3f}",
        f"- 蓝球命中率: {report.get('blue_hit_rate'):.3f}",
        '## 当前策略权重',
    ]
    for k, v in (report.get('strategy_weights') or {}).items():
        lines.append(f"- {k}: {v}")
    lines.append('')
    lines.append('## 最近10期详情')
    for d in report.get('details_tail', []):
        lines.append(
            f"- 期次索引 {d['issue_idx']}: 真={d['true_reds']}+{d['true_blue']} 预测={d['pred_reds']}+{d['pred_blue']} 红中{d['reds_hit']} 蓝中{d['blue_hit']}"
        )
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    r = evaluate_recent(window=200)
    persist(r)
    print('✅ 评估完成，输出至 reports/。')
