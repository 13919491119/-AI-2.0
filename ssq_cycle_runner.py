"""
ssq_cycle_runner.py
运行双色球历史循环评估并生成摘要报告（JSON+Markdown）。
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, Any

from typing import Any, Dict, Optional

from ssq_predict_cycle import SSQPredictCycle


def run_ssq_cycle_and_summarize(
    data_path: str = 'ssq_history.csv',
    mode: str = 'batch',
    closed_loop_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cycle = SSQPredictCycle(data_path=data_path)
    if mode == 'closed-loop':
        kwargs = closed_loop_kwargs or {}
        summary = cycle.run_closed_loop(**kwargs)
        summary.update({"mode": "closed-loop", "timestamp": datetime.now().isoformat()})
        return summary
    cycle.run_cycle()
    total = len(cycle.match_log)
    by_model: Dict[str, Dict[str, int]] = {}
    matches = 0
    for rec in cycle.match_log:
        mdl = rec['model']
        by_model.setdefault(mdl, {"count": 0, "matches": 0})
        by_model[mdl]["count"] += 1
        if rec['is_match']:
            by_model[mdl]["matches"] += 1
            matches += 1
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_predictions": total,
        "total_matches": matches,
        "by_model": by_model,
        "mode": "batch",
    }
    os.makedirs('reports', exist_ok=True)
    json_path = os.path.join('reports', 'ssq_cycle_summary.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    ts = datetime.utcnow().strftime('%Y%m%d')
    md_path = os.path.join('reports', f'ssq_cycle_{ts}.md')
    lines = [
        f"# 双色球历史循环评估摘要 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        "",
        f"- 总预测记录: {total}",
        f"- 完全匹配: {matches}",
        "",
        "## 各模型统计",
    ]
    for mdl, stats in by_model.items():
        lines.append(f"- {mdl}: 预测 {stats['count']} 次，完全匹配 {stats['matches']} 次")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        # 自动写入累计发现模式数到系统状态文件
        try:
            with open('xuanji_system_state.json', 'r', encoding='utf-8') as f:
                sys_state = json.load(f)
        except Exception:
            sys_state = {}
        sys_state['cumulative_learning_cycles'] = total
        with open('xuanji_system_state.json', 'w', encoding='utf-8') as f:
            json.dump(sys_state, f, ensure_ascii=False, indent=2)
    return summary


if __name__ == '__main__':
    run_ssq_cycle_and_summarize()
