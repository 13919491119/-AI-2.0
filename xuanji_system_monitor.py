import time
import os
import sys
import subprocess
from datetime import datetime

LOG_PATH = 'ai_system.log'
CHECK_INTERVAL = 60  # 秒
STOP_THRESHOLD = 180  # 停机阈值（秒）
MONITOR_TASKS = [
    ('ssq_fusion_predict_cycle.py', 'python3 ssq_fusion_predict_cycle.py &'),
    ('auto_learn_cultural_deep.py', 'python3 auto_learn_cultural_deep.py &'),
    ('person_predict_cycle.py', 'python3 person_predict_cycle.py &'),
    # 可扩展更多关键任务
]


def get_last_run_time():
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # 倒序查找最后一个周期时间戳
        for line in reversed(lines):
            if '[系统后台自主运营]' in line:
                # 可扩展：如日志有时间戳可进一步解析
                return datetime.now()  # 占位，实际应解析时间戳
        return None
    except Exception as e:
        print(f'[监控异常] 日志读取失败: {e}')
        return None

def is_task_running(task_name):
    try:
        result = subprocess.run(['pgrep', '-fl', task_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return any(task_name in line for line in result.stdout.splitlines())
    except Exception:
        return False

def restart_task(cmd):
    try:
        subprocess.Popen(cmd, shell=True)
        print(f'[AI守护] 已重启任务: {cmd}')
    except Exception as e:
        print(f'[AI守护] 重启失败: {cmd}, 错误: {e}')

def monitor_system():
    print('[系统监控] 启动自动监控...')
    last_alert = None
    from wechat_alert import send_wechat_alert
    from email_alert import send_email_alert
    while True:
        last_run = get_last_run_time()
        now = datetime.now()
        # 检查所有关键任务
        for task_name, start_cmd in MONITOR_TASKS:
            if not is_task_running(task_name):
                print(f'[AI守护] 检测到任务停止: {task_name}，立即重启...')
                restart_task(start_cmd)
                send_wechat_alert(f'【AI守护】任务{task_name}已自动重启')
                send_email_alert('AI守护告警', f'任务{task_name}已自动重启')
        if last_run:
            print(f'[系统监控] 最近运行周期时间: {last_run}')
        else:
            print('[系统监控] 未检测到系统运行周期，可能已停机！')
            if not last_alert or (now - last_alert).seconds > STOP_THRESHOLD:
                print('[告警] 系统可能已停止运行，请检查！')
                send_wechat_alert('【告警】AI系统可能已停止运行，请及时检查！')
                send_email_alert('AI系统告警', 'AI系统可能已停止运行，请及时检查！')
                last_alert = now
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    monitor_system()
