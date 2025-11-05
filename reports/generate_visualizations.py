"""
生成用于前端/可视化的数据文件：
- 从 reports/ssq_batch_replay_summary_window_*.json 中读取窗口化统计，生成一个合并 JSON 方便前端读取。
- 从 reports/weights_history/*.json 中读取权重快照，生成 timeseries CSV（timestamp, liuyao, liuren, qimen, ziwei, ai_fusion）。

输出目录： reports/visualizations/

可直接在前端读取 JSON/CSV 文件绘图。
"""
import os
import json
import glob
import csv
from datetime import datetime, timezone

OUT_DIR = 'reports/visualizations'
os.makedirs(OUT_DIR, exist_ok=True)

# 1) 聚合窗口化摘要文件
window_files = sorted(glob.glob('reports/ssq_batch_replay_summary_window_*.json'))
window_data = {}
for wf in window_files:
    try:
        with open(wf, 'r', encoding='utf-8') as f:
            jd = json.load(f)
        # 提取窗口大小（文件名结尾）
        base = os.path.basename(wf)
        parts = base.split('_')
        w = parts[-1].split('.')[0]
        window_data[w] = jd
    except Exception:
        continue

with open(os.path.join(OUT_DIR, 'ssq_window_metrics_merged.json'), 'w', encoding='utf-8') as f:
    json.dump({'generated_at': datetime.now(timezone.utc).isoformat(), 'windows': window_data}, f, ensure_ascii=False, indent=2)

# 2) 生成每个模型在不同窗口下的简单表格（CSV）
csv_rows = []
models = set()
for w, jd in window_data.items():
    for m, mv in jd.get('models', {}).items():
        models.add(m)
        total = mv.get('total', 0)
        red_hit = mv.get('red_hit', 0)
        blue_hit = mv.get('blue_hit', 0)
        full_hit = mv.get('full_hit', 0)
        red_rate = (red_hit / (6*total)) if total else 0.0
        blue_rate = (blue_hit / total) if total else 0.0
        full_rate = (full_hit / total) if total else 0.0
        csv_rows.append({'window': int(w), 'model': m, 'total': total, 'red_hit': red_hit, 'blue_hit': blue_hit, 'full_hit': full_hit, 'red_rate': round(red_rate,6), 'blue_rate': round(blue_rate,6), 'full_rate': round(full_rate,6)})

csv_path = os.path.join(OUT_DIR, 'ssq_window_metrics_table.csv')
with open(csv_path, 'w', encoding='utf-8', newline='') as cf:
    writer = csv.DictWriter(cf, fieldnames=['window','model','total','red_hit','blue_hit','full_hit','red_rate','blue_rate','full_rate'])
    writer.writeheader()
    for r in sorted(csv_rows, key=lambda x:(x['window'], x['model'])):
        writer.writerow(r)

# 3) 从权重快照生成时间序列 CSV
snap_files = sorted(glob.glob('reports/weights_history/*.json'))
weights_ts = []
for sf in snap_files:
    try:
        with open(sf, 'r', encoding='utf-8') as f:
            jd = json.load(f)
        gen = jd.get('generated_at') or jd.get('fusion', {}).get('last_updated')
        # 尝试解析时间戳，宽容处理
        ts = None
        try:
            ts = datetime.fromisoformat(gen.replace('Z','+00:00')) if isinstance(gen, str) else None
        except Exception:
            try:
                ts = datetime.strptime(gen, '%Y-%m-%d %H:%M:%S')
                ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = None
        if ts is None:
            # fallback to file mtime
            ts = datetime.fromtimestamp(os.path.getmtime(sf), tz=timezone.utc)
        weights = jd.get('weights', {})
        weights_ts.append({'ts': ts.isoformat(), **weights})
    except Exception:
        continue

# write weights timeseries CSV
if weights_ts:
    fieldnames = ['ts'] + sorted(list(models.union(set().union(*[set(x.keys()) for x in weights_ts]) if weights_ts else [])))
    # ensure consistent model columns ordering
    for col in ['liuyao','liuren','qimen','ziwei','ai_fusion']:
        if col not in fieldnames:
            fieldnames.append(col)
    weights_csv = os.path.join(OUT_DIR, 'ssq_weights_timeseries.csv')
    with open(weights_csv, 'w', encoding='utf-8', newline='') as wf:
        writer = csv.DictWriter(wf, fieldnames=fieldnames)
        writer.writeheader()
        for row in weights_ts:
            out = {k: row.get(k, '') for k in fieldnames}
            writer.writerow(out)

print('visualizations generated:', csv_path, 'and', weights_csv)
