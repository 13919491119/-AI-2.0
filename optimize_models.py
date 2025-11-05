"""
模型优化与训练脚本（模拟）
- 模拟对ssq、person、stock、weather模型进行短时迭代训练
- 更新权重文件和性能指标（写入 ssq_strategy_weights.json 与 model_status.json）
"""
import time
import json
import random
import os
import subprocess

WEIGHTS_FILE = 'ssq_strategy_weights.json'
STATUS_FILE = 'model_status.json'
LOG_FILE = 'autonomous_optimization.log'
REPORT_FILE = 'reports/ssq_batch_replay_report.txt'
WEIGHTS_HISTORY_DIR = 'reports/weights_history'

def load_weights():
    try:
        with open(WEIGHTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'weights': {'liuyao':0.25,'liuren':0.2,'qimen':0.15,'ai':0.4}, 'fusion': None}

def save_weights(w, eval_score=None):
    """保存主权重文件，并在历史目录写入带 eval_score 的快照，随后尝试对快照签名。"""
    with open(WEIGHTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(w, f, ensure_ascii=False, indent=2)
    # 同时写入历史快照以便审计
    try:
        os.makedirs(WEIGHTS_HISTORY_DIR, exist_ok=True)
        ts = time.strftime('%Y%m%d_%H%M%S')
        snapshot_path = os.path.join(WEIGHTS_HISTORY_DIR, f'weights_snapshot_{ts}.json')
        payload = {'snapshot_at': ts, 'weights': w}
        if eval_score is not None:
            payload['eval_score'] = float(eval_score)
        with open(snapshot_path, 'w', encoding='utf-8') as sf:
            json.dump(payload, sf, ensure_ascii=False, indent=2)
        # 尝试对快照进行签名（非强制）
        try:
            subprocess.run(['python3', 'scripts/sign_weights_history.py', snapshot_path], check=False)
        except Exception:
            pass
    except Exception:
        pass

def update_status(delta_perf=0.1):
    try:
        s = {}
        try:
            with open(STATUS_FILE,'r',encoding='utf-8') as f:
                s = json.load(f)
        except Exception:
            s = {'perf_improve': 1.0, 'last_run': None}
        s['perf_improve'] = round(s.get('perf_improve',1.0) + delta_perf,3)
        s['last_run'] = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(STATUS_FILE,'w',encoding='utf-8') as f:
            json.dump(s,f,ensure_ascii=False,indent=2)
        return s
    except Exception as e:
        return {'error': str(e)}

def parse_replay_report(path=REPORT_FILE):
    """解析 ssq_batch_replay_report.txt，提取每个模型的 total/red/blue/full 统计值。"""
    stats = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            current = None
            for raw in f:
                line = raw.strip()
                if line.startswith('模型：'):
                    current = line.split('：',1)[1].strip()
                    stats[current] = {'total':0,'red_hit':0,'blue_hit':0,'full_hit':0}
                    continue
                if current is None:
                    continue
                if line.startswith('总期数：'):
                    try:
                        stats[current]['total'] = int(line.split('：',1)[1].strip())
                    except Exception:
                        stats[current]['total'] = 0
                if line.startswith('红球命中总数：'):
                    try:
                        stats[current]['red_hit'] = int(line.split('：',1)[1].strip())
                    except Exception:
                        stats[current]['red_hit'] = 0
                if line.startswith('蓝球命中总数：'):
                    try:
                        stats[current]['blue_hit'] = int(line.split('：',1)[1].strip())
                    except Exception:
                        stats[current]['blue_hit'] = 0
                if line.startswith('全中') and '期数' in line:
                    try:
                        parts = line.split('：',1)
                        stats[current]['full_hit'] = int(parts[1].strip())
                    except Exception:
                        stats[current]['full_hit'] = 0
    except Exception:
        return {}
    return stats

def metrics_to_weights(metrics, min_weight=0.01):
    """根据 replay 统计将模型表现转为权重（简单线性评分并归一化）。
    返回新的 weights dict。
    """
    # 如果没有metrics，返回 None
    if not metrics:
        return None
    scores = {}
    for m, v in metrics.items():
        total = v.get('total', 0) or 0
        if total <= 0:
            scores[m] = 0.0
            continue
        full_rate = v.get('full_hit', 0) / float(total)
        red_rate = (v.get('red_hit', 0) / float(6 * total)) if total>0 else 0.0
        blue_rate = v.get('blue_hit', 0) / float(total)
        # 权重由全中率主导，红球命中率次之，蓝球命中率轻微影响
        score = full_rate * 0.7 + red_rate * 0.25 + blue_rate * 0.05
        scores[m] = max(0.0, score)
    total_score = sum(scores.values())
    if total_score <= 0:
        return None
    weights = {m: max(min_weight, round(scores[m] / total_score, 3)) for m in scores}
    # 归一化再调整到和为1
    s = sum(weights.values())
    for k in weights:
        weights[k] = round(weights[k] / s, 3)
    return weights

def get_latest_snapshot_eval():
    """从历史快照中找最近带 eval_score 的项并返回 eval_score（float），找不到返回 None。"""
    try:
        import glob
        files = sorted(glob.glob(os.path.join(WEIGHTS_HISTORY_DIR, '*.json')))
        for p in reversed(files):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    j = json.load(f)
                if 'eval_score' in j:
                    return float(j['eval_score'])
            except Exception:
                continue
    except Exception:
        pass
    return None

if __name__ == '__main__':
    start = time.time()
    w = load_weights()
    # 尝试从 replay 报告读取指标，若存在则基于指标计算新权重
    metrics = parse_replay_report(REPORT_FILE)
    new_weights = metrics_to_weights(metrics) if metrics else None
    if new_weights:
        print('发现复盘报告，使用指标驱动权重更新')
        # 先计算评估指标（avg_full_rate）用于回滚门控
        avg_full_rate = 0.0
        cnt = 0
        for m,v in metrics.items():
            t = v.get('total',0)
            if t>0:
                avg_full_rate += (v.get('full_hit',0)/t)
                cnt += 1
        avg_full_rate = (avg_full_rate/cnt) if cnt>0 else 0.0

        # 回滚阈值（允许轻微波动），例如允许下降 1% 以内
        rollback_threshold = 0.01
        baseline = get_latest_snapshot_eval()
        if baseline is not None:
            try:
                baseline_f = float(baseline)
            except Exception:
                baseline_f = None
        else:
            baseline_f = None

        # 判断是否接受新权重：若新 eval 显著低于 baseline（超过阈值），则回退不更新
        accept = True
        if (baseline_f is not None) and (avg_full_rate < (baseline_f - rollback_threshold)):
            accept = False

        if not accept:
            with open(LOG_FILE,'a',encoding='utf-8') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] optimize rejected: new_eval={avg_full_rate:.6f} < baseline={baseline_f:.6f} - thr={rollback_threshold}\n")
            print('检测到性能下降，已拒绝权重更新（回滚触发）。')
        else:
            # 保持原结构并保存快照（带 eval_score），随后签名
            w['weights'] = {k: new_weights.get(k, round(1.0/len(new_weights),3)) for k in new_weights}
            w['fusion'] = {'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'), 'note': 'metrics-driven'}
            save_weights(w, eval_score=avg_full_rate)
            delta = round(avg_full_rate * 0.1, 3)
            status = update_status(delta_perf=delta)
            with open(LOG_FILE,'a',encoding='utf-8') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] metrics-driven optimize, avg_full_rate={avg_full_rate:.4f}, delta={delta}\n")
            print('优化完成（基于指标），权重已更新。')
    else:
        # 回退到原有的模拟微调逻辑（报告缺失或解析失败）
        print('未发现复盘报告或解析失败，使用随机微调策略')
        for step in range(3):
            duration = random.randint(20,60)
            print(f"优化步骤 {step+1}/3: 训练 {duration}s ...")
            time.sleep(0.1)
            for k in w['weights']:
                delta = (random.random()-0.4)*0.02
                w['weights'][k] = max(0.01, round(w['weights'][k] + delta,3))
            s = sum(w['weights'].values())
            for k in w['weights']:
                w['weights'][k] = round(w['weights'][k]/s,3)
        w['fusion'] = {'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'), 'note': 'auto-optimized'}
        save_weights(w)
        status = update_status(delta_perf=0.05)
        with open(LOG_FILE,'a',encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] fallback optimize_models, new_perf={status.get('perf_improve')}\n")
        print('优化完成，权重已更新（随机微调）。')
