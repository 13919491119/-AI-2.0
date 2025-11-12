#!/usr/bin/env python3
"""
自主循环智能体 (Autonomous Meta-Learning Loop) for SSQ predictions.

功能步骤 (一轮循环):
 1. 生成指定期号 (或下一期) 的 5 种方法各 N=1000 组预测: 小六爻 / 小六壬 / 奇门遁甲 / 紫微斗数 / AI融合
 2. 基于生成结果执行候选评分与 Top-10 选择 (调用现有逻辑复制/内嵌)
 3. 对照真实开奖号码 (若已公布) 进行单期回测，输出回测摘要
 4. 使用最近 M 个期的历史预测 + 开奖数据做权重网格调优 (复用 auto_tune_ai_fusion 逻辑的核心函数裁剪)
 5. 生成调优后权重下的目标期 Top-10 (tuned) 并比较差异
 6. 记录本轮学习日志 (JSON + Markdown)，更新一个持久 state 文件
 7. 进入下一期 (期号 +1) 或按配置保持在同一期重复蒙特卡洛加深 (可选)

持久化:
  - outputs/autonomous_loop_state.json : 保存最近最佳权重、轮次、期号历史
  - outputs/loop_logs/loop_<period>_round<k>.md : 每轮 Markdown 报告

用法:
  python3 tools/agent_autonomous_loop.py \
      --start-period 2025130 \
      --rounds 3 \
      --samples 1000 \
      --history-periods 50 \
      --weight-step 0.25 \
      --stay-same-period 0
"""
import argparse
import json
import os
import sys
import time
import math
from pathlib import Path
from itertools import product
from collections import Counter
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'outputs'
STATE_FILE = OUTDIR / 'autonomous_loop_state.json'
LOG_DIR = OUTDIR / 'loop_logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ Helpers: reuse generation functions dynamically ------------------

GEN_SCRIPT = ROOT / 'tools' / 'generate_ssq_predictions.py'
SELECT_SCRIPT = ROOT / 'tools' / 'select_top10_ssq.py'
BACKTEST_SCRIPT = ROOT / 'tools' / 'backtest_ssq_predictions.py'
TUNE_SCRIPT = ROOT / 'tools' / 'auto_tune_ai_fusion.py'

METHOD_STEMS = ['xiaoliuyao','xiaoliuren','qimen','ziwei','ai_fusion']

def run_cmd(cmd, capture=False):
    print(f'[run] {cmd}')
    if capture:
        res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(res.stdout)
        return res.stdout
    else:
        subprocess.run(cmd, shell=True, check=True)


def load_jsonl(path: Path):
    if not path.exists():
        return []
    items = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
            except Exception:
                pass
    return items


def load_history_csv(csv_path: Path):
    import csv
    hist = {}
    with csv_path.open('r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            pid = row['期号']
            reds = [int(row[f'红{i}']) for i in range(1,7)]
            blue = int(row['蓝'])
            hist[pid] = {'reds': reds, 'red_set': set(reds), 'blue': blue}
    return hist


def summarize_single_period(period: str, history, top10_path: Path):
    draw = history.get(period)
    if not draw:
        return {'status': 'no_actual'}
    # gather predictions stats for each method
    stats = {}
    for stem in METHOD_STEMS:
        f = OUTDIR / f'ssq_{stem}_{period}.jsonl'
        preds = load_jsonl(f)
        red_counter = Counter()
        blue_hits = 0
        full_hits = 0
        for p in preds:
            reds = p.get('reds', [])
            red_matches = len(set(reds) & draw['red_set'])
            red_counter[red_matches] += 1
            if p.get('blue') == draw['blue']:
                blue_hits += 1
            if red_matches == 6 and p.get('blue') == draw['blue']:
                full_hits += 1
        stats[stem] = {
            'total': len(preds),
            'red_dist': dict(red_counter),
            'blue_hits': blue_hits,
            'full_hits': full_hits
        }
    # top10
    top10 = []
    if top10_path.exists():
        try:
            top10 = json.loads(top10_path.read_text(encoding='utf-8'))
        except Exception:
            top10 = []
    top10_eval = None
    if top10:
        rc = Counter()
        bh = 0
        for t in top10:
            rm = len(set(t['reds']) & draw['red_set'])
            rc[rm] += 1
            if t['blue'] == draw['blue']:
                bh += 1
        top10_eval = {
            'red_dist': dict(rc),
            'blue_hits': bh
        }
    return {'status': 'ok', 'period': period, 'actual': draw, 'methods': stats, 'top10': top10_eval}


def grid_weights(n_methods, step):
    vals = [round(i*step, 10) for i in range(int(1/step)+1)]
    combos = []
    for tup in product(vals, repeat=n_methods):
        s = sum(tup)
        if s <= 0:
            continue
        norm = tuple(round(v/s,6) for v in tup)
        combos.append(norm)
    uniq = list({c: None for c in combos}.keys())
    return uniq


def collect_pool(period, methods):
    pool = {}
    for m in methods:
        path = OUTDIR / f'ssq_{m}_{period}.jsonl'
        preds = load_jsonl(path)
        for p in preds:
            reds = tuple(sorted(p.get('reds', [])))
            blue = p.get('blue')
            key = (reds, blue)
            pool.setdefault(key, {})
            pool[key][m] = pool[key].get(m,0)+1
    return pool


def score_by_weights(pool, methods, weights, k):
    scored = []
    for key, info in pool.items():
        s = 0.0
        for i,m in enumerate(methods):
            if m in info:
                s += weights[i]
        scored.append((s, key))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [key for _,key in scored[:k]]


def evaluate_combo_list(combo_list, actual, blue_w=1.0):
    tot = 0.0
    for reds, blue in combo_list:
        red_matches = len(set(reds) & actual['red_set'])
        blue_match = 1 if blue == actual['blue'] else 0
        tot += red_matches + blue_w * blue_match
    return tot


def tune_weights(history, periods, methods, step, topk, blue_w):
    pools = {}
    usable = []
    for p in periods:
        pool = collect_pool(p, methods)
        if pool:
            pools[p] = pool
            usable.append(p)
    if not pools:
        return None, 0, []
    best = None
    best_score = -1.0
    grid = grid_weights(len(methods), step)
    for w in grid:
        acc = 0.0
        for pid, pool in pools.items():
            actual = history.get(pid)
            if not actual:
                continue
            top = score_by_weights(pool, methods, w, topk)
            acc += evaluate_combo_list(top, actual, blue_w)
        avg = acc / max(len(pools),1)
        if avg > best_score:
            best_score = avg
            best = w
    return {'weights': best, 'score': best_score}, len(pools), usable


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def next_period(pid: str):
    try:
        return str(int(pid)+1)
    except Exception:
        return pid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start-period', default='2025130')
    ap.add_argument('--rounds', type=int, default=1, help='循环轮数 (无限可用 -1)')
    ap.add_argument('--samples', type=int, default=1000, help='每方法生成样本数')
    ap.add_argument('--history-periods', type=int, default=50, help='用于权重调优的最近期数')
    ap.add_argument('--weight-step', type=float, default=0.25)
    ap.add_argument('--blue-weight', type=float, default=1.0)
    ap.add_argument('--topk', type=int, default=10)
    ap.add_argument('--stay-same-period', type=int, default=0, help='是否在同一期重复蒙特卡洛 (1=是)')
    ap.add_argument('--sleep', type=float, default=0.0, help='各轮之间休眠秒数')
    ap.add_argument('--history-csv', default='ssq_history.csv')
    args = ap.parse_args()

    OUTDIR.mkdir(exist_ok=True)
    history = load_history_csv(Path(args.history_csv))
    state = load_state()

    period = state.get('last_period', args.start_period)
    total_rounds = 0
    target_rounds = args.rounds

    while True:
        total_rounds += 1
        print(f"==== 自主循环 Round {total_rounds} / period {period} ====")
        # Step1 生成
        run_cmd(f"python3 {GEN_SCRIPT} --period {period} --n {args.samples}")

        # Step2 选择 Top10 (当前 select_top10 固定 2025130 文件名，需在使用前复制/适配)
        # 为复用现有脚本的硬编码 2025130，我们临时复制文件名称到该期，再运行脚本，然后再把输出改名。
        # 1) 备份原有 2025130 文件 (如果存在) -> 暂不覆盖 (简单方案: 软链接/复制)
        # 简化: 复制当前期 ai_fusion 文件为 2025130 文件名，然后运行脚本，再重命名输出。
        tmp_map = {}
        fixed_pid = '2025130'
        if period != fixed_pid:
            for stem in METHOD_STEMS:
                src = OUTDIR / f'ssq_{stem}_{period}.jsonl'
                if src.exists():
                    dst = OUTDIR / f'ssq_{stem}_{fixed_pid}.jsonl'
                    tmp_map[dst] = dst.read_text(encoding='utf-8') if dst.exists() else None
                    dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
            run_cmd(f"python3 {SELECT_SCRIPT}")
            # 重命名输出 top10 文件为当前期
            top_json = OUTDIR / 'top10_ssq_2025130.json'
            top_md = OUTDIR / 'top10_ssq_2025130.md'
            if top_json.exists():
                renamed_json = OUTDIR / f'top10_ssq_{period}.json'
                renamed_json.write_text(top_json.read_text(encoding='utf-8'), encoding='utf-8')
            if top_md.exists():
                renamed_md = OUTDIR / f'top10_ssq_{period}.md'
                renamed_md.write_text(top_md.read_text(encoding='utf-8'), encoding='utf-8')
            # 恢复之前的 2025130 文件
            for dst, old_content in tmp_map.items():
                if old_content is None:
                    dst.unlink(missing_ok=True)
                else:
                    dst.write_text(old_content, encoding='utf-8')
        else:
            run_cmd(f"python3 {SELECT_SCRIPT}")

        # Step3 回测 (需要真实开奖号码才有效)
        actual = history.get(period)
        backtest_output = None
        if actual:
            reds_cli = ' '.join(str(r) for r in sorted(actual['reds']))
            run_cmd(f"python3 {BACKTEST_SCRIPT} --reds {reds_cli} --blue {actual['blue']}")
            backtest_output = OUTDIR / 'backtest_2025130_report.md'
            # 复制回测报告为当前期专属
            if backtest_output.exists():
                (OUTDIR / f'backtest_{period}_report.md').write_text(backtest_output.read_text(encoding='utf-8'), encoding='utf-8')

        # Step4 权重调优 + 生成 tuned Top10
        hist_keys = sorted(history.keys())
        recent = hist_keys[-args.history_periods:]
        tune_cmd = f"python3 {TUNE_SCRIPT} --periods {args.history_periods} --step {args.weight_step} --topk {args.topk} --target {period}"
        run_cmd(tune_cmd)
        tuned_json = OUTDIR / f'tuned_top10_{period}.jsonl'
        weight_summary = OUTDIR / f'tuned_weights_summary_{period}.json'

        # Step5 汇总单期表现
        single_summary = summarize_single_period(period, history, OUTDIR / f'top10_ssq_{period}.json')

        # Step6 写日志
        loop_log = LOG_DIR / f'loop_{period}_round{total_rounds}.md'
        lines = []
        lines.append(f"# 自主循环 Round {total_rounds} - 期 {period}")
        lines.append('')
        lines.append('## 生成与选择')
        lines.append(f'- 生成样本数/方法: {args.samples}')
        lines.append(f'- Top10 文件: top10_ssq_{period}.json')
        if tuned_json.exists():
            lines.append(f'- 调优 Top10: {tuned_json.name}')
        if weight_summary.exists():
            ws = json.loads(weight_summary.read_text(encoding='utf-8'))
            lines.append(f"- 最佳权重: {ws.get('best_weights')} (score={ws.get('best_score')})")
        if single_summary.get('status') == 'ok':
            lines.append('\n## 单期回测摘要')
            lines.append(f"- 真实开奖: 红 {single_summary['actual']['reds']} 蓝 {single_summary['actual']['blue']}")
            lines.append('- 方法表现:')
            for m, st in single_summary['methods'].items():
                lines.append(f"  - {m}: total={st['total']} blue_hits={st['blue_hits']} full_hits={st['full_hits']} red_dist={st['red_dist']}")
            if single_summary['top10']:
                lines.append(f"- Top10 命中: red_dist={single_summary['top10']['red_dist']} blue_hits={single_summary['top10']['blue_hits']}")
        else:
            lines.append('\n## 单期回测摘要')
            lines.append('- 尚无真实开奖号码，等待公布')
        lines.append('\n## 元学习注记')
        lines.append('- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)')
        lines.append('- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模')
        loop_log.write_text('\n'.join(lines), encoding='utf-8')

        # Step7 更新状态
        state['last_period'] = period
        state.setdefault('rounds', 0)
        state['rounds'] = state['rounds'] + 1
        state['last_update'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        save_state(state)
        print(f'[state] 更新 state -> {STATE_FILE}')
        print(f'[log] 写入 {loop_log}')

        # 轮次终止判定
        if target_rounds != -1 and total_rounds >= target_rounds:
            print('达到指定轮次，结束。')
            break
        # 下一期
        if args.stay_same_period:
            pass
        else:
            period = next_period(period)
        if args.sleep > 0:
            time.sleep(args.sleep)


if __name__ == '__main__':
    main()
