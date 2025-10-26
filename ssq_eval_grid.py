from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import json, os

from ssq_predict_cycle import SSQPredictCycle


@dataclass
class EvalConfig:
    window: int = 100
    temp_red_list: List[float] = None  # type: ignore
    top_p_red_list: List[float] = None  # type: ignore
    alpha_red_list: List[float] = None  # type: ignore
    diversify: bool = True
    seed: int | None = 42
    # 新增：蓝球侧参数与是否写回最佳
    temp_blue_list: List[float] = None  # type: ignore
    top_p_blue_list: List[float] = None  # type: ignore
    alpha_blue_list: List[float] = None  # type: ignore
    apply_best: bool = False

    def __post_init__(self):
        if self.temp_red_list is None:
            self.temp_red_list = [0.7, 0.9, 1.0]
        if self.top_p_red_list is None:
            self.top_p_red_list = [0.8, 0.9, 1.0]
        if self.alpha_red_list is None:
            self.alpha_red_list = [0.0, 0.1, 0.2]
        if self.temp_blue_list is None:
            self.temp_blue_list = [0.7, 0.9, 1.0]
        if self.top_p_blue_list is None:
            self.top_p_blue_list = [0.8, 0.9, 1.0]
        if self.alpha_blue_list is None:
            self.alpha_blue_list = [0.0, 0.1]


def _attempts_for_issue(cycle: SSQPredictCycle, idx: int) -> List[Dict[str, Any]]:
    attempts: List[Dict[str, Any]] = []
    for model in ['liuyao', 'liuren', 'qimen', 'ai']:
        if model == 'liuyao': pr, pb = cycle.predict_liuyao(idx)
        elif model == 'liuren': pr, pb = cycle.predict_liuren(idx)
        elif model == 'qimen': pr, pb = cycle.predict_qimen(idx)
        else: pr, pb = cycle.predict_ai(idx)
        attempts.append({'strategy': model, 'pred_reds': pr, 'pred_blue': pb})
    return attempts


def evaluate_grid(cfg: EvalConfig) -> Dict[str, Any]:
    t0 = time.time()
    cycle = SSQPredictCycle(data_path='ssq_history.csv')
    history = cycle.history
    n = len(history)
    if n == 0:
        return {'status': 'error', 'error': 'no_history'}
    start = max(0, n - int(cfg.window))
    window_idx = list(range(start, n))

    results: List[Dict[str, Any]] = []
    for temp_red in cfg.temp_red_list:
        for top_p_red in cfg.top_p_red_list:
            for alpha_red in cfg.alpha_red_list:
                for temp_blue in cfg.temp_blue_list:
                    for top_p_blue in cfg.top_p_blue_list:
                        for alpha_blue in cfg.alpha_blue_list:
                # 注入参数
                            cycle.temp_red = float(temp_red)
                            cycle.top_p_red = float(top_p_red)
                            cycle.alpha_red = float(alpha_red)
                            cycle.temp_blue = float(temp_blue)
                            cycle.top_p_blue = float(top_p_blue)
                            cycle.alpha_blue = float(alpha_blue)
                            cycle.enforce_candidate_diversity = bool(cfg.diversify)
                            if cfg.seed is not None:
                                import random as _rnd
                                _rnd.seed(int(cfg.seed))

                            red_hits_total = 0
                            blue_hits_total = 0
                            full_match_total = 0
                            count = 0
                            for idx in window_idx:
                                true_reds, true_blue = history[idx]
                                attempts = _attempts_for_issue(cycle, idx)
                                reds, blue = cycle._fuse_from_attempts(attempts)
                                # 计分
                                red_hits_total += len(set(reds) & set(true_reds))
                                blue_hits_total += 1 if blue == true_blue else 0
                                full_match_total += 1 if (set(reds) == set(true_reds) and blue == true_blue) else 0
                                count += 1

                            if count == 0:
                                continue
                            res = {
                                'temp_red': temp_red,
                                'top_p_red': top_p_red,
                                'alpha_red': alpha_red,
                                'temp_blue': temp_blue,
                                'top_p_blue': top_p_blue,
                                'alpha_blue': alpha_blue,
                                'window': count,
                                'red_hits_avg': red_hits_total / float(count),
                                'blue_hit_rate': blue_hits_total / float(count),
                                'full_matches': full_match_total,
                            }
                            # 汇总评分（可调整权重）
                            res['score'] = (
                                res['full_matches'] * 100.0 + res['blue_hit_rate'] * 10.0 + res['red_hits_avg']
                            )
                            results.append(res)

    # 排序，得分高在前
    results.sort(key=lambda x: x['score'], reverse=True)
    out = {
        'status': 'ok',
        'evaluated': len(results),
        'best': results[0] if results else None,
        'results': results,
        'elapsed_sec': round(time.time() - t0, 3),
    }
    # 可选：将最佳结果写回融合配置
    if cfg.apply_best and results:
        best = results[0]
        payload = {}
        path = 'ssq_strategy_weights.json'
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    payload = json.load(f) or {}
            except Exception:
                payload = {}
        fusion = payload.get('fusion') if isinstance(payload, dict) else None
        if not isinstance(fusion, dict):
            fusion = {}
        for k in ['temp_red','top_p_red','alpha_red','temp_blue','top_p_blue','alpha_blue']:
            fusion[k] = float(best.get(k))
        payload['fusion'] = fusion
        # 附加证据
        ev = payload.get('fusion_evidence')
        if not isinstance(ev, list):
            ev = []
        ev.append({
            'generated_at': time.time(),
            'window': cfg.window,
            'score': best.get('score'),
            'best': best,
            'note': 'eval_grid auto-apply',
        })
        payload['fusion_evidence'] = ev
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            out['applied'] = True
        except Exception as e:
            out['applied'] = False
            out['apply_error'] = str(e)
    return out


if __name__ == '__main__':
    out = evaluate_grid(EvalConfig())
    import json
    print(json.dumps(out, ensure_ascii=False, indent=2))
