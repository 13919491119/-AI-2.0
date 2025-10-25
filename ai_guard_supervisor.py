import subprocess
import time
import os

def is_task_running(task_name):
    try:
        out = subprocess.check_output(['pgrep', '-f', task_name])
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False

def start_task(cmd):
    print(f'AI守护进程：启动任务 {cmd}')
    subprocess.Popen(cmd, shell=True)

def ai_guard_loop():
    task_cmd = 'venv/bin/python deep_learning_cycle.py'
    task_name = 'deep_learning_cycle.py'
    while True:
        if not is_task_running(task_name):
            print('检测到任务未运行，AI守护进程自动重启任务')
            start_task(task_cmd)
        else:
            print('任务正常运行，AI守护进程持续监控')
        time.sleep(15)

if __name__ == '__main__':
    ai_guard_loop()
