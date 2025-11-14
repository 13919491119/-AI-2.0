#!/usr/bin/env python3
"""
轻量状态脚本：读取 pid/ready/started/heartbeat 文件并返回 JSON，可用于 health checks 或 systemd
用法：
    python tools/ai_meta_status.py           # 打印 JSON
    python tools/ai_meta_status.py --check   # 健康检查，若不健康以非零退出
"""
import json
import argparse
import os
import time
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
AI_PID = os.path.join(ROOT, 'ai_meta_system.pid')
AUTON_PID = os.path.join(ROOT, 'autonomous_run.pid')
AI_STARTED = os.path.join(ROOT, 'ai_meta_system.started')
AUTON_READY = os.path.join(ROOT, 'autonomous_run.ready')
HEARTBEAT = os.path.join(ROOT, 'autonomous_heartbeat.json')


def _read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return None


def _is_pid_running(pid_str):
    try:
        pid = int(pid_str)
    except Exception:
        return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='健康检查：不健康时退出码非零')
    args = ap.parse_args()
    out = {}
    out['ai_meta_system_pid'] = _read_file(AI_PID)
    out['autonomous_run_pid'] = _read_file(AUTON_PID)
    out['ai_meta_system_started'] = _read_file(AI_STARTED)
    out['autonomous_run_ready'] = _read_file(AUTON_READY)
    hb_raw = _read_file(HEARTBEAT)
    if hb_raw:
        try:
            out['heartbeat'] = json.loads(hb_raw)
        except Exception:
            out['heartbeat_raw'] = hb_raw
    else:
        out['heartbeat'] = None

    out['ai_meta_system_running'] = _is_pid_running(out.get('ai_meta_system_pid') or '')
    out['autonomous_run_running'] = _is_pid_running(out.get('autonomous_run_pid') or '')
    out['checked_at'] = time.time()

    print(json.dumps(out, indent=2, ensure_ascii=False))

    if args.check:
        ok = bool(out.get('ai_meta_system_running') or out.get('autonomous_run_running'))
        hb = out.get('heartbeat') or {}
        try:
            ts = float(hb.get('ts') or hb.get('last_completed') or 0.0)
            if ts:
                ok = ok and ((time.time() - ts) < 180)
            else:
                ok = False
        except Exception:
            ok = False
        if not ok:
            return 1
        return 0


if __name__ == '__main__':
    main()
