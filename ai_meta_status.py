#!/usr/bin/env python3
"""简单状态检查脚本：
  - 输出 ai_meta_system 与 autonomous_run 的 PID、ready/started 标记和进程是否存活
  - 返回 0（全部正常）或 2（任一异常）便于 systemd/监控集成
"""
import os
import sys
import json

ROOT = os.path.abspath(os.path.dirname(__file__))
AI_PID = os.path.join(ROOT, 'ai_meta_system.pid')
AUTO_PID = os.path.join(ROOT, 'autonomous_run.pid')
AI_STARTED = os.path.join(ROOT, 'ai_meta_system.started')
AUTO_READY = os.path.join(ROOT, 'autonomous_run.ready')

def read_pid(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return int((f.read() or '').strip())
    except Exception:
        return None

def is_running(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def read_ts(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return None

def main():
    status = get_status()
    ok = status['ai_meta_system']['running'] and status['autonomous_run']['running']
    print(json.dumps(status, indent=2, ensure_ascii=False))
    sys.exit(0 if ok else 2)


def get_status():
    """Return the status dict without exiting; useful for HTTP endpoints."""
    ai_pid = read_pid(AI_PID)
    auto_pid = read_pid(AUTO_PID)
    ai_started = read_ts(AI_STARTED)
    auto_ready = read_ts(AUTO_READY)

    status = {
        'ai_meta_system': {
            'pid_file': AI_PID,
            'pid': ai_pid,
            'running': is_running(ai_pid),
            'started_ts': ai_started,
        },
        'autonomous_run': {
            'pid_file': AUTO_PID,
            'pid': auto_pid,
            'running': is_running(auto_pid),
            'ready_ts': auto_ready,
        }
    }
    return status

if __name__ == '__main__':
    main()
