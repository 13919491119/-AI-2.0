"""轻量开发守护脚本：在 dev 环境中稳定运行 ai_meta_system.main

功能：
- 启动 `python -u -m ai_meta_system.main` 为子进程
- 监控子进程状态，若退出则按指数退避重启（最多无限次）
- 将当前守护器 pid 写入 `ai_meta_system/daemon.pid`
- 将状态写入 `ai_meta_system/daemon_status.json`
- 日志写到 `ai_meta_system/daemon.log`

用法：
  python ai_meta_system/dev_daemon.py &
或：
  setsid python ai_meta_system/dev_daemon.py > ai_meta_system/daemon.log 2>&1 &
"""
import subprocess
import time
import os
import json
import signal
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DAEMON_PID = os.path.join(ROOT, 'ai_meta_system', 'daemon.pid')
STATUS_FILE = os.path.join(ROOT, 'ai_meta_system', 'daemon_status.json')
LOG_FILE = os.path.join(ROOT, 'ai_meta_system', 'daemon.log')
CMD = [sys.executable, '-u', '-m', 'ai_meta_system.main']

BACKOFF_BASE = 1.5
MAX_BACKOFF = 300

running = True
child = None


def _write_status(status: dict):
    try:
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_pid():
    try:
        with open(DAEMON_PID, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def _terminate_child():
    global child
    if child and child.poll() is None:
        try:
            child.terminate()
        except Exception:
            pass
        try:
            child.wait(timeout=5)
        except Exception:
            try:
                child.kill()
            except Exception:
                pass


def _sigint_handler(signum, frame):
    global running
    running = False
    _terminate_child()
    sys.exit(0)


signal.signal(signal.SIGINT, _sigint_handler)
signal.signal(signal.SIGTERM, _sigint_handler)


def main():
    global child
    _write_pid()
    backoff = 1.0
    while running:
        start = time.time()
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"\n--- Starting child at {time.ctime()} ---\n")
            child = subprocess.Popen(CMD)
            # write status
            _write_status({'state': 'running', 'child_pid': child.pid, 'since': time.time()})
            # wait for child to exit
            ret = child.wait()
            end = time.time()
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"Child exited with code {ret} after {end-start:.1f}s\n")
            # update status
            _write_status({'state': 'exited', 'exit_code': ret, 'last_run_seconds': end-start, 'timestamp': time.time()})
            # backoff before restart
            time.sleep(backoff)
            backoff = min(MAX_BACKOFF, backoff * BACKOFF_BASE)
        except Exception as e:
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"Daemon exception: {str(e)}\n")
            _write_status({'state': 'error', 'error': str(e), 'timestamp': time.time()})
            time.sleep(backoff)
            backoff = min(MAX_BACKOFF, backoff * BACKOFF_BASE)


if __name__ == '__main__':
    main()
