#!/usr/bin/env python3
"""Generate simple visualizations and an HTML summary for latest SSQ replay metrics and weight snapshots.

Writes output to `reports/visualization/` (creates directory if needed).
The script will attempt to use matplotlib if available; otherwise it will produce an HTML table-only summary.
"""
import json
import os
import glob
from datetime import datetime

OUT_DIR = os.path.join('reports', 'visualization')
os.makedirs(OUT_DIR, exist_ok=True)

def find_latest_weights_snapshot():
    pattern = os.path.join('reports', 'weights_history', '*.json')
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def try_matplotlib():
    try:
        import matplotlib.pyplot as plt
        return plt
    except Exception:
        return None

def render_charts(summary, weights_snapshot):
    plt = try_matplotlib()
    charts = []
    if plt:
        try:
            # model rates chart
            models = list(summary['models'].keys())
            red_rates = [summary['models'][m].get('red_rate',0) for m in models]
            blue_rates = [summary['models'][m].get('blue_rate',0) for m in models]
            fig, ax = plt.subplots(figsize=(8,4))
            x = range(len(models))
            ax.bar([i-0.2 for i in x], red_rates, width=0.4, label='red_rate')
            ax.bar([i+0.2 for i in x], blue_rates, width=0.4, label='blue_rate')
            ax.set_xticks(list(x))
            ax.set_xticklabels(models, rotation=45)
            ax.set_ylabel('rate')
            ax.set_title('Model red/blue hit rates')
            ax.legend()
            img1 = os.path.join(OUT_DIR, 'model_rates.png')
            fig.tight_layout()
            fig.savefig(img1)
            charts.append(img1)
        except Exception:
            pass
        try:
            # weights chart
            w = weights_snapshot.get('weights') if weights_snapshot else None
            if w and isinstance(w, dict):
                keys = list(w.keys())
                vals = [float(w[k]) for k in keys]
                fig, ax = plt.subplots(figsize=(8,4))
                ax.bar(keys, vals)
                ax.set_ylabel('weight')
                ax.set_title('Fusion weights')
                img2 = os.path.join(OUT_DIR, 'fusion_weights.png')
                fig.tight_layout()
                fig.savefig(img2)
                charts.append(img2)
        except Exception:
            pass
    return charts

def _load_autorl_best():
    p = os.path.join('reports', 'autorl_runs', 'best.json')
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def generate_html(summary, weights_snapshot, charts):
    html = ['<html><head><meta charset="utf-8"><title>SSQ Replay Summary</title></head><body>']
    html.append(f'<h1>SSQ Replay Summary - generated {datetime.utcnow().isoformat()}Z</h1>')
    if charts:
        for c in charts:
            html.append(f'<div><img src="{os.path.basename(c)}" style="max-width:100%;height:auto"/></div>')
    # AutoRL best snapshot section
    autorl_best = _load_autorl_best()
    if autorl_best:
        html.append('<h2>AutoRL Best Snapshot</h2>')
        try:
            best = autorl_best.get('snapshot') or autorl_best
            # Try to pick key fields
            key = autorl_best.get('key', 'avg_mean_reward')
            cur = autorl_best.get(key)
            html.append('<p>Key metric: %s = %s</p>' % (key, cur))
        except Exception:
            pass
        html.append('<pre>')
        html.append(json.dumps(autorl_best, ensure_ascii=False, indent=2))
        html.append('</pre>')
    html.append('<h2>Summary JSON</h2>')
    html.append('<pre>')
    html.append(json.dumps(summary, ensure_ascii=False, indent=2))
    html.append('</pre>')
    html.append('<h2>Latest Weights Snapshot</h2>')
    html.append('<pre>')
    html.append(json.dumps(weights_snapshot, ensure_ascii=False, indent=2))
    html.append('</pre>')
    html.append('</body></html>')
    out = os.path.join(OUT_DIR, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    # copy images to out dir already in same dir
    print('Wrote', out)

def main():
    summary_path = os.path.join('reports', 'ssq_batch_replay_summary.json')
    if not os.path.exists(summary_path):
        print('No summary JSON found at', summary_path)
        return
    summary = load_json(summary_path)
    weights_file = find_latest_weights_snapshot()
    weights_snapshot = load_json(weights_file) if weights_file else {}
    charts = render_charts(summary, weights_snapshot)
    generate_html(summary, weights_snapshot, charts)
    # also write a copy of AutoRL best snapshot if exists for frontend consumption
    autorl_best = _load_autorl_best()
    if autorl_best:
        out_best = os.path.join(OUT_DIR, 'autorl_best_snapshot.json')
        try:
            with open(out_best, 'w', encoding='utf-8') as f:
                json.dump(autorl_best, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

if __name__ == '__main__':
    main()
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
