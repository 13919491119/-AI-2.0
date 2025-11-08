#!/usr/bin/env python3
"""
一键启动：全面自动化与AI智能体训练的守护体系

功能：
- 自愈：清理常见残留（.git/index.lock、缺失目录）
- 启动：若 ai_guard_supervisor 未运行则后台拉起
- 验证：短暂等待后读取 reports/ai_guard_status.json 输出摘要

退出码：0 启动成功且守护在线；2 启动失败或守护未在线
"""
import os
import sys
import time
import json
import subprocess

ROOT = os.path.abspath(os.path.dirname(__file__))
REPORTS = os.path.join(ROOT, 'reports')
LOGS = os.path.join(ROOT, 'logs')
HEARTBEATS = os.path.join(ROOT, 'heartbeats')
STATUS = os.path.join(REPORTS, 'ai_guard_status.json')


def _mkdirs():
    for d in (REPORTS, LOGS, HEARTBEATS):
        os.makedirs(d, exist_ok=True)


def _self_heal():
    # 清理 .git/index.lock（若无 git 进程在运行）
    try:
        lock = os.path.join(ROOT, '.git', 'index.lock')
        if os.path.exists(lock):
            code = subprocess.call(['pgrep', 'git'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if code != 0:
                os.remove(lock)
                print('[start] 已清理 .git/index.lock')
    except Exception:
        pass


def _is_guard_running() -> bool:
    try:
        out = subprocess.check_output(['pgrep', '-f', 'ai_guard_supervisor.py'])
        return bool(out.strip())
    except Exception:
        return False


def _start_guard():
    if _is_guard_running():
        print('[start] ai_guard_supervisor 已在运行')
        return True
    print('[start] 启动 ai_guard_supervisor ...')
    log_path = os.path.join(LOGS, 'ai_guard_supervisor_boot.log')
    with open(log_path, 'ab') as lf:
        subprocess.Popen('python3 ai_guard_supervisor.py', shell=True, cwd=ROOT, stdout=lf, stderr=lf)
    # 等待守护写入状态
    for _ in range(10):
        time.sleep(1.5)
        if os.path.exists(STATUS):
            return True
    return _is_guard_running()


def _read_status():
    try:
        with open(STATUS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def main():
    _mkdirs()
    _self_heal()
    ok = _start_guard()
    status = _read_status()
    if status:
        print('[start] 守护状态:')
        print(json.dumps(status, ensure_ascii=False, indent=2))
    if ok:
        print('[start] 已进入自治守护模式（后台运行中）')
        sys.exit(0)
    else:
        print('[start] 启动失败：未检测到守护运行', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
