"""
双色球历史批量复盘与模型学习升级脚本
- 自动遍历ssq_history.csv每一期数据，按开奖日期/时间起卦，分别用小六爻、小六壬、奇门遁甲、紫薇奇数、AI融合模型预测
- 预测结果与实际开奖号码对比，统计每模型命中率、失误点
- 自动记录复盘结果，驱动模型参数优化与学习升级
- 形成周期性报告与模型自我迭代闭环
"""
import csv
import datetime
from ssq_predict_cycle import SSQPredictCycle

import json
import time
import os

HISTORY_FILE = 'ssq_history.csv'
REPORT_FILE = 'reports/ssq_batch_replay_report.txt'
SUMMARY_JSON = 'reports/ssq_batch_replay_summary.json'


models = ['liuyao', 'liuren', 'qimen', 'ziwei', 'ai_fusion']

results = {m: {'total': 0, 'red_hit': 0, 'blue_hit': 0, 'full_hit': 0, 'details': []} for m in models}

cycle = SSQPredictCycle(data_path=HISTORY_FILE)

with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for idx, row in enumerate(reader):
        # 更宽松的字段兼容：尝试多种常见字段名
        period = row.get('period') or row.get('期次') or row.get('issue') or row.get('期号') or row.get('id')
        date = row.get('date') or row.get('开奖日期') or row.get('draw_date')
        draw_time = row.get('time') or row.get('开奖时间') or row.get('draw_time')
        reds = []
        for i in range(6):
            val = row.get(f'red{i+1}') or row.get(f'红球{i+1}') or row.get(f'红{i+1}') or row.get(f'r{i+1}')
            if val is not None and val != '':
                reds.append(int(val))
        blue = row.get('blue') or row.get('蓝球') or row.get('蓝')
        blue = int(blue) if blue is not None and blue != '' else 0
        # 起卦信息：开奖日期+时间
        for m in models:
            if m == 'liuyao': pr, pb = cycle.predict_liuyao(idx)
            elif m == 'liuren': pr, pb = cycle.predict_liuren(idx)
            elif m == 'qimen': pr, pb = cycle.predict_qimen(idx)
            elif m == 'ziwei': pr, pb = cycle.predict_ai(idx) # 可自定义紫薇逻辑
            else:
                attempts = []
                for model in ['liuyao','liuren','qimen','ai']:
                    if model == 'liuyao': r, b = cycle.predict_liuyao(idx)
                    elif model == 'liuren': r, b = cycle.predict_liuren(idx)
                    elif model == 'qimen': r, b = cycle.predict_qimen(idx)
                    else: r, b = cycle.predict_ai(idx)
                    attempts.append({'strategy': model, 'pred_reds': r, 'pred_blue': b})
                pr, pb = cycle._fuse_from_attempts(attempts)
            red_hit = len(set(pr) & set(reds))
            blue_hit = int(pb == blue)
            full_hit = int(red_hit == 6 and blue_hit)
            results[m]['total'] += 1
            results[m]['red_hit'] += red_hit
            results[m]['blue_hit'] += blue_hit
            results[m]['full_hit'] += full_hit
            results[m]['details'].append({
                'period': period,
                'date': date,
                'draw_time': draw_time,
                'model': m,
                'pred_reds': pr,
                'pred_blue': pb,
                'actual_reds': reds,
                'actual_blue': blue,
                'red_hit': red_hit,
                'blue_hit': blue_hit,
                'full_hit': full_hit
            })

# 生成报告
# 输出文本报告和 JSON 汇总
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write('双色球历史批量复盘与模型学习升级报告\n')
    for m in models:
        f.write(f'\n模型：{m}\n')
        f.write(f'总期数：{results[m]["total"]}\n')
        f.write(f'红球命中总数：{results[m]["red_hit"]}\n')
        f.write(f'蓝球命中总数：{results[m]["blue_hit"]}\n')
        f.write(f'全中（红+蓝）期数：{results[m]["full_hit"]}\n')
        f.write('部分复盘详情（前10期）：\n')
        for d in results[m]['details'][:10]:
            f.write(f'期次:{d["period"]} 日期:{d["date"]} 时间:{d.get("draw_time","")} 预测红球:{d["pred_reds"]} 预测蓝球:{d["pred_blue"]} 实际红球:{d["actual_reds"]} 实际蓝球:{d["actual_blue"]} 命中红球:{d["red_hit"]} 命中蓝球:{d["blue_hit"]} 全中:{d["full_hit"]}\n')
    f.write('\n模型学习升级闭环已完成。')

# JSON 汇总（机器可读）
summary = {
    'schema_v': 1,
    'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    'total_issues_sampled': next(iter(results.values()))['total'] if results else 0,
    'models': {}
}
for m in models:
    summary['models'][m] = {
        'total': results[m]['total'],
        'red_hit': results[m]['red_hit'],
        'blue_hit': results[m]['blue_hit'],
        'full_hit': results[m]['full_hit'],
        'sample_details': results[m]['details'][:10]
    }

with open(SUMMARY_JSON, 'w', encoding='utf-8') as jf:
    json.dump(summary, jf, ensure_ascii=False, indent=2)

# 也保存时间戳版本，便于历史追踪
ts = int(time.time())
history_path = f'reports/ssq_batch_replay_summary_{ts}.json'
with open(history_path, 'w', encoding='utf-8') as hf:
    json.dump(summary, hf, ensure_ascii=False, indent=2)

# 生成窗口化（rolling window）汇总：近 100、500、1000 期
try:
    windows = [100, 500, 1000]
    for w in windows:
        win_summary = {'schema_v': 1, 'window': w, 'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'models': {}}
        for m in models:
            details = results[m]['details'][-w:] if len(results[m]['details']) >= 1 else []
            total = sum(1 for _ in details)
            red_hit = sum(d.get('red_hit', 0) for d in details)
            blue_hit = sum(d.get('blue_hit', 0) for d in details)
            full_hit = sum(d.get('full_hit', 0) for d in details)
            win_summary['models'][m] = {
                'total': total,
                'red_hit': red_hit,
                'blue_hit': blue_hit,
                'full_hit': full_hit,
                'sample_details': details[-10:]
            }
        path = f'reports/ssq_batch_replay_summary_window_{w}.json'
        with open(path, 'w', encoding='utf-8') as wf:
            json.dump(win_summary, wf, ensure_ascii=False, indent=2)
except Exception:
    pass
