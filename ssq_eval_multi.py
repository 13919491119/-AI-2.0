#!/usr/bin/env python3
"""
多候选（Top-N）评估：
- 对最近窗口内的每一期，生成N组融合候选，统计最佳红球命中、是否命中蓝球、是否出现完全匹配等指标。
- 用于评估在“推荐多组号码”场景下的实际效果提升。
"""
from __future__ import annotations

import time
from typing import Dict, List, Tuple, Optional

from ssq_predict_cycle import SSQPredictCycle


def evaluate_multi(window: int = 100, n: int = 5, diversify: bool = True, seed: Optional[int] = 42) -> Dict[str, object]:
    cyc = SSQPredictCycle(data_path='ssq_history.csv')
    # 注入多样性和随机种子（仅对本次评估生效）
    try:
        cyc.enforce_candidate_diversity = bool(diversify)
        if seed is not None:
            import random as _rnd
            _rnd.seed(int(seed))
    except Exception:
        pass

    history = cyc.history
    if not history:
        return {'status': 'error', 'error': 'no_history'}

    start = max(0, len(history) - int(window))
    best_reds_hits: List[int] = []
    blue_hit_any: List[int] = []
    full_matches: int = 0
    details_tail: List[Dict[str, object]] = []
    n_eff = max(1, min(50, int(n)))

    for idx in range(start, len(history)):
        true_reds, true_blue = history[idx]
        # 四策略各出一组，作为融合输入
        attempts: List[Dict[str, object]] = []
        for model in ['liuyao','liuren','qimen','ai']:
            if model == 'liuyao': pr, pb = cyc.predict_liuyao(idx)
            elif model == 'liuren': pr, pb = cyc.predict_liuren(idx)
            elif model == 'qimen': pr, pb = cyc.predict_qimen(idx)
            else: pr, pb = cyc.predict_ai(idx)
            attempts.append({'strategy': model, 'pred_reds': pr, 'pred_blue': pb})
        # 生成N组候选
        cands = cyc.generate_candidates_from_attempts(attempts, count=n_eff)
        # 统计本期最优红命中、是否任一命中蓝球、是否出现完全匹配
        brh = 0
        bh_any = 0
        fm = 0
        for c in cands:
            cr = c['reds']
            cb = c['blue']
            rh = len(set(cr) & set(true_reds))
            if rh > brh:
                brh = rh
            if cb == true_blue:
                bh_any = 1
            if set(cr) == set(true_reds) and cb == true_blue:
                fm = 1
        best_reds_hits.append(brh)
        blue_hit_any.append(bh_any)
        full_matches += fm
        if idx >= len(history) - 10:  # 收集最近10期详情
            details_tail.append({
                'issue_idx': idx,
                'true_reds': sorted(true_reds),
                'true_blue': true_blue,
                'best_reds_hit': brh,
                'blue_hit_any': bh_any,
                'n_candidates': n_eff,
            })

    # 汇总窗口级指标
    avg_best_reds_hit = (sum(best_reds_hits) / len(best_reds_hits)) if best_reds_hits else 0.0
    blue_hit_rate_any = (sum(blue_hit_any) / len(blue_hit_any)) if blue_hit_any else 0.0
    topk_multi = {
        'best_red_hit_ge_2': sum(1 for x in best_reds_hits if x >= 2),
        'best_red_hit_ge_3': sum(1 for x in best_reds_hits if x >= 3),
        'best_red_hit_ge_4': sum(1 for x in best_reds_hits if x >= 4),
    }

    return {
        'status': 'ok',
        'window': int(window),
        'n': n_eff,
        'diversify': bool(diversify),
        'avg_best_reds_hit': avg_best_reds_hit,
        'blue_hit_rate_any': blue_hit_rate_any,
        'full_matches': full_matches,
        'topk_multi': topk_multi,
        'details_tail': details_tail,
        'generated_at': time.time(),
    }


if __name__ == '__main__':
    out = evaluate_multi(window=120, n=5, diversify=True, seed=42)
    import json
    print(json.dumps(out, ensure_ascii=False, indent=2))
