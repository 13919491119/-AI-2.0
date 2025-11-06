import json
import os
from typing import Dict, List


AUTORL_DIR = os.path.join("reports", "autorl_runs")
BEST_FILE = os.path.join(AUTORL_DIR, "best.json")


def _ensure_dir():
    os.makedirs(AUTORL_DIR, exist_ok=True)


def gate_improvement(current: Dict[str, float], *, key: str = "avg_mean_reward", min_delta: float = 0.02) -> Dict[str, bool]:
    """
    Compare current aggregate to stored best; return decision and record if improved.
    min_delta is an absolute threshold on the metric increase.
    """
    _ensure_dir()
    prev: Dict[str, float] = {}
    if os.path.exists(BEST_FILE):
        try:
            prev = json.load(open(BEST_FILE, "r", encoding="utf-8"))
        except Exception:
            prev = {}
    prev_best = float(prev.get(key, float("-inf")))
    cur = float(current.get(key, float("-inf")))
    improved = (cur - prev_best) >= min_delta
    if improved and cur > prev_best:
        data = {"key": key, key: cur, "snapshot": current}
        with open(BEST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return {"improved": improved, "previous": prev_best, "current": cur}


def save_run_artifact(filename: str, payload: Dict):
    _ensure_dir()
    path = os.path.join(AUTORL_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path
