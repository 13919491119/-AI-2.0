"""自适应调度模块：根据最近一次循环耗时与简单启发式调整下一轮间隔。

策略（启发式）：
- 读取 status/heartbeat JSON（包含 duration_seconds 与 next_interval_sec）。
- 若耗时 < 40% 当前间隔且当前间隔 > 0，则尝试减半，但不低于 min_seconds。
- 若耗时 > 80% 当前间隔，则提升间隔为当前间隔 * 1.3，不超过 max_seconds。
- 若当前间隔 == 0（紧凑模式），基于耗时决定：
  - 耗时 < 1s 保持0
  - 1s-5s 设置为耗时 * 1.5（平衡突发）
  - >5s 设置为耗时 * 2（避免过载）
结果写入 out_path JSON：{"new_interval": X, "reason": "logic"}
失败或无足够信息则返回 None。
"""
from __future__ import annotations
import os, json, time, math
from typing import Optional, Dict, Any

DEFAULT_MIN = 0
DEFAULT_MAX = 3600

def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def compute_next_interval(status_path: str, cfg: Dict[str, Any], out_path: str) -> Optional[int]:
    data = _load_json(status_path)
    if not data:
        return None
    dur = float(data.get('duration_seconds', 0.0) or 0.0)
    current = int(data.get('next_interval_sec', cfg.get('default_seconds', 0)) or 0)

    min_seconds = int(cfg.get('min_seconds', DEFAULT_MIN))
    max_seconds = int(cfg.get('max_seconds', DEFAULT_MAX))
    default_seconds = int(cfg.get('default_seconds', 0))

    reason = 'no-change'
    new_interval = current

    if current > 0:
        if dur < 0.4 * current and current > min_seconds:
            new_interval = max(min_seconds, int(max(0, current * 0.5)))
            reason = 'halve-fast'
        elif dur > 0.8 * current:
            new_interval = min(max_seconds, int(current * 1.3 + 1))
            reason = 'increase-slow'
    else:
        # 紧凑模式基于耗时扩展
        if dur < 1.0:
            new_interval = 0
            reason = 'compact-fast'
        elif dur < 5.0:
            new_interval = min(max_seconds, max(min_seconds, int(dur * 1.5)))
            reason = 'expand-moderate'
        else:
            new_interval = min(max_seconds, max(min_seconds, int(dur * 2.0)))
            reason = 'expand-slow'

    # 约束
    new_interval = max(min_seconds, min(max_seconds, new_interval))

    # 若变化极小（差异 < 2 秒且非0），保持不变
    if current > 0 and abs(new_interval - current) < 2:
        new_interval = current
        reason = 'stable'

    result = {
        'timestamp': time.time(),
        'old_interval': current,
        'new_interval': new_interval,
        'duration_seconds': dur,
        'min_seconds': min_seconds,
        'max_seconds': max_seconds,
        'default_seconds': default_seconds,
        'reason': reason,
        'status_path': os.path.abspath(status_path),
    }
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return new_interval

__all__ = ["compute_next_interval"]
