#!/usr/bin/env python3
"""
双色球自动调优器（最小可行）
- 基于历史数据，评估现有策略（六爻/小六壬/奇门/AI）的命中表现
- 生成策略权重文件 ssq_strategy_weights.json 供预测闭环读取
- 可选生成号码先验分布 ssq_ball_priors.json 作为后续增强的基础

权重计算思路（简化稳健）：
- 对每期，以各策略单次预测为样本，统计：
  - 红球命中数（0-6）
  - 蓝球命中（0/1）
- 指标：score = 红球命中均值/6 * 0.7 + 蓝球命中率 * 0.3
- 归一化到和为1（若全为0则回退为均匀权重）

依赖：仅使用现有模块与标准库。sklearn/xgboost 不存在时 AI 策略自动降级为随机，不会异常。
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Tuple

from ssq_data import SSQDataManager
from ssq_predict_cycle import SSQPredictCycle


def evaluate_strategy_on_history(cycle: SSQPredictCycle, strategy: str) -> Tuple[float, float, int]:
    """返回 (红球平均命中率, 蓝球命中率, 样本数)。"""
    reds_hit_total = 0
    blue_hit_total = 0
    samples = 0
    for idx, (true_reds, true_blue) in enumerate(cycle.history):
        if strategy == 'liuyao':
            pred_reds, pred_blue = cycle.predict_liuyao(idx)
        elif strategy == 'liuren':
            pred_reds, pred_blue = cycle.predict_liuren(idx)
        elif strategy == 'qimen':
            pred_reds, pred_blue = cycle.predict_qimen(idx)
        elif strategy == 'ai':
            pred_reds, pred_blue = cycle.predict_ai(idx)
        else:
            continue
        reds_hit = len(set(pred_reds) & set(true_reds))
        blue_hit = 1 if pred_blue == true_blue else 0
        reds_hit_total += reds_hit
        blue_hit_total += blue_hit
        samples += 1
    if samples == 0:
        return 0.0, 0.0, 0
    return (reds_hit_total / samples / 6.0), (blue_hit_total / samples), samples


def compute_weights(metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    # score = reds_rate*0.7 + blue_rate*0.3
    raw_scores = {
        k: metrics[k].get('reds_rate', 0.0) * 0.7 + metrics[k].get('blue_rate', 0.0) * 0.3
        for k in metrics.keys()
    }
    total = sum(raw_scores.values())
    if total <= 1e-9:
        # 均匀回退
        n = max(1, len(raw_scores))
        return {k: 1.0 / n for k in raw_scores.keys()}
    return {k: (v / total) for k, v in raw_scores.items()}


def build_ball_priors(history: List[Tuple[List[int], int]]) -> Dict[str, Dict[str, int]]:
    red_freq = {str(n): 0 for n in range(1, 34)}
    blue_freq = {str(n): 0 for n in range(1, 17)}
    for reds, blue in history:
        for r in reds:
            red_freq[str(r)] += 1
        blue_freq[str(blue)] += 1
    return {'red': red_freq, 'blue': blue_freq}


def main():
    parser = argparse.ArgumentParser(description='SSQ 自动调优器')
    parser.add_argument('--data', default='ssq_history.csv', help='历史CSV路径')
    parser.add_argument('--out', default='ssq_strategy_weights.json', help='权重输出文件')
    parser.add_argument('--priors', default='ssq_ball_priors.json', help='号码先验输出文件')
    parser.add_argument('--train-ai', action='store_true', help='调优前先训练AI模型（若可用）')
    parser.add_argument('--window', type=int, default=0, help='仅使用最近window期进行评估（0表示全部历史）')
    parser.add_argument('--ema', type=float, default=0.6, help='与历史权重进行EMA融合的alpha（0-1），0表示不融合')
    parser.add_argument('--eval-grid', action='store_true', help='在调优过程中执行参数网格评估，并采纳最佳融合参数')
    parser.add_argument('--grid-window', type=int, default=100, help='网格评估窗口大小')
    args = parser.parse_args()

    cycle = SSQPredictCycle(data_path=args.data)
    if args.train_ai:
        try:
            _ = cycle.ai_model.train()
        except Exception:
            pass

    strategies = ['liuyao', 'liuren', 'qimen', 'ai']
    metrics: Dict[str, Dict[str, float]] = {}
    # 可选窗口裁剪
    if args.window and args.window > 0:
        cycle.history = cycle.history[-args.window:]
    for s in strategies:
        reds_rate, blue_rate, samples = evaluate_strategy_on_history(cycle, s)
        metrics[s] = {
            'reds_rate': round(reds_rate, 6),
            'blue_rate': round(blue_rate, 6),
            'samples': samples,
        }

    weights = compute_weights(metrics)
    # 可选：运行网格评估，获取最佳融合参数
    fusion = None
    fusion_evidence = None
    if getattr(args, 'eval_grid', False):
        try:
            from ssq_eval_grid import evaluate_grid, EvalConfig
            grid_out = evaluate_grid(EvalConfig(window=int(args.grid_window)))
            if isinstance(grid_out, dict) and grid_out.get('status') == 'ok' and grid_out.get('best'):
                best = grid_out['best']
                fusion = {
                    'temp_red': float(best.get('temp_red', 1.0)),
                    'top_p_red': float(best.get('top_p_red', 1.0)),
                    'alpha_red': float(best.get('alpha_red', 0.0)),
                    # 保留蓝球参数为默认，由运行时或后续评估决定
                }
                fusion_evidence = {
                    'best': best,
                    'evaluated': grid_out.get('evaluated'),
                    'elapsed_sec': grid_out.get('elapsed_sec'),
                    'window': grid_out.get('best', {}).get('window'),
                }
        except Exception:
            fusion = None
            fusion_evidence = None
    # EMA 融合历史权重
    if args.ema and args.ema > 0:
        try:
            with open(args.out, 'r', encoding='utf-8') as f:
                old_payload = json.load(f)
                old_w = old_payload.get('weights', {}) if isinstance(old_payload, dict) else {}
        except Exception:
            old_w = {}
        if old_w:
            keys = set(old_w.keys()) | set(weights.keys())
            merged = {}
            for k in keys:
                o = float(old_w.get(k, 0.0))
                n = float(weights.get(k, 0.0))
                merged[k] = (1 - args.ema) * o + args.ema * n
            total = sum(merged.values())
            if total > 0:
                weights = {k: v / total for k, v in merged.items()}
    payload = {
        'metrics': metrics,
        'weights': {k: round(float(v), 6) for k, v in weights.items()},
        'generated_at': __import__('time').time(),
        'ema_alpha': args.ema,
        'window': args.window,
    }
    if fusion:
        payload['fusion'] = fusion
    if fusion_evidence:
        payload['fusion_evidence'] = fusion_evidence

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"✅ 已写入策略权重 -> {args.out}: {payload['weights']}")

    priors = build_ball_priors(cycle.history)
    with open(args.priors, 'w', encoding='utf-8') as f:
        json.dump(priors, f, ensure_ascii=False, indent=2)
    print(f"✅ 已写入号码先验 -> {args.priors}")

    # 记录权重历史
    try:
        import os as _os
        _os.makedirs('reports', exist_ok=True)
        hist_path = _os.path.join('reports', 'ssq_weights_history.jsonl')
        with open(hist_path, 'a', encoding='utf-8') as hf:
            hf.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == '__main__':
    main()
