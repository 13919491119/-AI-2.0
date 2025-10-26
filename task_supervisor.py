"""
AI任务守护进程：自动监控所有核心任务，异常时自动重启，无需人工干预。
"""
import os
import time
import subprocess
import psutil

tasks = [
    {"name": "ssq_cycle_runner.py", "cmd": "python3 ssq_cycle_runner.py"},
    {"name": "ssq_auto_tuner.py", "cmd": "python3 ssq_auto_tuner.py"},
    {"name": "bazi_naming_cycle.py", "cmd": "python3 bazi_naming_cycle.py"},
    {"name": "autonomous_run.py", "cmd": "python3 autonomous_run.py"},
]

def is_running(script_name):
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if any(script_name in str(x) for x in p.info['cmdline']):
                return True
        except Exception:
            continue
    return False

def start_task(cmd):
    subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    while True:
        for task in tasks:
            if not is_running(task["name"]):
                print(f"[守护] 检测到 {task['name']} 未运行，自动重启...")
                start_task(task["cmd"])
        time.sleep(15)

if __name__ == "__main__":
    main()
