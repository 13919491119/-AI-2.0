#!/usr/bin/env python3
"""
自动化权重调优：在历史期上对若干预测方法做网格搜索，寻找对 Top-K 选择最有利的组合权重。

用法示例:
  python3 tools/auto_tune_ai_fusion.py --periods 50 --step 0.25 --topk 10 --target 2025130

输出:
  - prints 最佳权重与得分
  - 写入 outputs/tuned_top10_<target>.jsonl
  - 写入 outputs/tuned_weights_summary.json

注意: 脚本对缺失的历史预测文件会跳过对应期号。
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
from itertools import product
from collections import defaultdict


def load_history(path):
    history = {}
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            pid = row['期号']
            reds = [int(row[f'红{i}']) for i in range(1,7)]
            blue = int(row['蓝'])
            history[pid] = {'reds': set(reds), 'blue': blue}
    return history


def load_predictions_for_period(outputs_dir, method, period):
    path = os.path.join(outputs_dir, f"ssq_{method}_{period}.jsonl")
    if not os.path.exists(path):
        return None
    tickets = []
    with open(path) as f:
        for line in f:
            try:
                obj = json.loads(line)
                reds = tuple(sorted(obj.get('reds', [])))
                blue = int(obj.get('blue'))
                tickets.append((reds, blue))
            except Exception:
                continue
    return tickets


def collect_candidate_pool(outputs_dir, methods, period):
    pool = {}
    for m in methods:
        preds = load_predictions_for_period(outputs_dir, m, period)
        if not preds:
            continue
        for reds, blue in preds:
            key = (tuple(reds), blue)
            pool.setdefault(key, {})
            pool[key][m] = pool[key].get(m, 0) + 1
    return pool


def load_blue_model_scores(outputs_dir, period):
    """Load blue_model_topk_<period>.json and return dict blue->score (normalized)."""
    path = Path(outputs_dir) / f'blue_model_topk_{period}.json'
    if not path.exists():
        return {}
    try:
        arr = json.loads(path.read_text(encoding='utf-8'))
        d = {int(item['blue']): float(item.get('score', 0.0)) for item in arr}
        # normalize to sum=1
        s = sum(d.values())
        if s > 0:
            for k in d:
                d[k] = d[k] / s
        return d
    except Exception:
        return {}


def generate_weight_grid(n_methods, step):
    # generate non-negative weight combinations with given step, then normalize
    vals = [round(i * step, 10) for i in range(int(1/step)+1)]
    combos = []
    for tup in product(vals, repeat=n_methods):
        s = sum(tup)
        if s <= 0:
            continue
        norm = tuple(round(v / s, 6) for v in tup)
        combos.append(norm)
    # dedupe
    uniq = list({c: None for c in combos}.keys())
    return uniq


def score_topk_for_weights(pool, methods, weights, topk, blue_weight=1.0, blue_probs=None):
    # pool: dict key-> {method: count}
    # blue_probs: optional dict mapping blue->probability (0..1) to bias selection towards high-prob blues
    scored = []
    for key, info in pool.items():
        reds, blue = key
        score = 0.0
        for i, m in enumerate(methods):
            if m in info:
                score += weights[i]
        # add predicted blue probability as soft bonus to ranking if available
        if blue_probs and blue in blue_probs:
            score += blue_weight * float(blue_probs.get(blue, 0.0))
        scored.append((score, key))
    scored.sort(reverse=True, key=lambda x: x[0])
    top = [k for _, k in scored[:topk]]
    return top


def evaluate_topk(topk_list, actual, blue_weight=1.0):
    # metric: sum of matched red balls + blue match * blue_weight across selected tickets
    total = 0.0
    for reds, blue in topk_list:
        red_matches = len(set(reds) & actual['reds'])
        blue_match = 1 if blue == actual['blue'] else 0
        total += red_matches + blue_weight * blue_match
    return total


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--periods', type=int, default=50, help='使用最近 N 个期号作为验证集')
    p.add_argument('--step', type=float, default=0.25, help='权重网格的步长（0.25 或 0.2 推荐）')
    p.add_argument('--topk', type=int, default=10, help='每期选择 Top-K 票数')
    p.add_argument('--history', default='ssq_history.csv', help='历史开奖 CSV 路径')
    p.add_argument('--outputs', default='outputs', help='预测文件所在目录')
    p.add_argument('--methods', nargs='+', default=['xiaoliuyao','xiaoliuren','qimen','ziwei'], help='用于融合的基础方法（按顺序）')
    p.add_argument('--blue-weight', type=float, default=1.0, help='蓝球在评价函数中的权重（相当于一颗红球）')
    p.add_argument('--target', default='2025130', help='目标期号，用最优权重生成 Top-K')
    args = p.parse_args()

    history = load_history(args.history)
    all_periods = sorted(history.keys())
    if args.periods > len(all_periods):
        use_periods = all_periods
    else:
        use_periods = all_periods[-args.periods:]

    print(f'使用 {len(use_periods)} 个最近期进行调优: {use_periods[0]} ... {use_periods[-1]}')

    grid = generate_weight_grid(len(args.methods), args.step)
    print(f'权重组合数: {len(grid)} (步长 {args.step})')

    best = None
    best_score = -1.0
    tried = 0

    # pre-load pools for periods
    pools = {}
    for period in use_periods:
        pool = collect_candidate_pool(args.outputs, args.methods, period)
        if pool:
            pools[period] = pool
        else:
            # skip period if no predictions found
            print(f'跳过期号 {period}：未找到任何方法的预测文件')

    if not pools:
        print('未找到任何历史预测文件，退出')
        return

    for weights in grid:
        tried += 1
        total_metric = 0.0
        periods_used = 0
        for period, pool in pools.items():
            actual = history[period]
            topk = score_topk_for_weights(pool, args.methods, weights, args.topk, args.blue_weight)
            metric = evaluate_topk(topk, actual, args.blue_weight)
            total_metric += metric
            periods_used += 1
        if periods_used == 0:
            continue
        avg_metric = total_metric / periods_used
        if avg_metric > best_score:
            best_score = avg_metric
            best = weights

    print('网格搜索完成')
    print('最佳权重:', dict(zip(args.methods, best)))
    print('平均目标值 (每期 Top-K 总命中数):', best_score)

    # 生成 target period Top-K
    target_pool = collect_candidate_pool(args.outputs, args.methods, args.target)
    if not target_pool:
        print(f'目标期 {args.target} 未找到预测文件；无法生成 Top-K')
        return
    topk_target = score_topk_for_weights(target_pool, args.methods, best, args.topk, args.blue_weight)
    out_path = os.path.join(args.outputs, f'tuned_top{args.topk}_{args.target}.jsonl')
    with open(out_path, 'w') as fo:
        for reds, blue in topk_target:
            fo.write(json.dumps({'reds': list(reds), 'blue': blue, 'tuned_weights': dict(zip(args.methods, best))}, ensure_ascii=False) + '\n')

    # 保存 summary
    summary = {'methods': args.methods, 'best_weights': dict(zip(args.methods, best)), 'best_score': best_score, 'periods_used': len(pools)}
    with open(os.path.join(args.outputs, f'tuned_weights_summary_{args.target}.json'), 'w') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print('已写入', out_path)


if __name__ == '__main__':
    main()
