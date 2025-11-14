"""ai_meta_system 状态查询工具

用法:
  python -m ai_meta_system.status

输出 JSON，包含:
  - ai_meta_system_pid
  - autonomous_run_pid
  - ai_meta_system_started (timestamp or null)
  - autonomous_run_ready (timestamp or null)
  - ai_meta_system_running (bool)
  - autonomous_run_running (bool)
"""
import json
import os
import time
import sys
import psutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AI_PID_FILE = os.path.join(ROOT, 'ai_meta_system.pid')
AR_PID_FILE = os.path.join(os.path.dirname(__file__), '..', 'autonomous_run.pid')
AI_STARTED_FILE = os.path.join(ROOT, 'ai_meta_system.started')
AR_READY_FILE = os.path.join(os.path.dirname(__file__), '..', 'autonomous_run.ready')


def _read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip() or None
    except Exception:
        return None


def _is_pid_running(pid_str):
    try:
        pid = int(pid_str)
    except Exception:
        return False
    return psutil.pid_exists(pid)


def get_status():
    ai_pid = _read_file(AI_PID_FILE)
    ar_pid = _read_file(AR_PID_FILE)
    ai_started = _read_file(AI_STARTED_FILE)
    ar_ready = _read_file(AR_READY_FILE)

    status = {
        'ai_meta_system_pid': ai_pid,
        'autonomous_run_pid': ar_pid,
        'ai_meta_system_started': float(ai_started) if ai_started else None,
        'autonomous_run_ready': float(ar_ready) if ar_ready else None,
        'ai_meta_system_running': _is_pid_running(ai_pid) if ai_pid else False,
        'autonomous_run_running': _is_pid_running(ar_pid) if ar_pid else False,
        'timestamp': time.time(),
    }
    return status


if __name__ == '__main__':
    st = get_status()
    print(json.dumps(st, indent=2, ensure_ascii=False))
    if not st['ai_meta_system_running'] or not st['autonomous_run_running']:
        sys.exit(2)
    sys.exit(0)
