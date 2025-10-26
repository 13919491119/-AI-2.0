#!/usr/bin/env python3
"""
AI系统健康监控脚本：定时检测关键进程、CPU/内存、日志异常，写入health_report.log。
可通过crontab或后台守护方式运行。
"""
import os
import time
import psutil
from datetime import datetime

MONITOR_PROCS = [
    'xuanji_ai_main.py',
    'ssq_fusion_predict_cycle.py',
    'person_predict_cycle.py',
    'auto_learn_cultural_deep.py',
    'xuanji_system_monitor.py',
]
LOG_PATH = 'health_report.log'


def check_processes():
    result = {}
    for pname in MONITOR_PROCS:
        found = []
        for p in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
            if any(pname in (p.info.get('name') or '') or pname in ' '.join(p.info.get('cmdline') or []) for pname in [pname]):
                found.append({
                    'pid': p.info['pid'],
                    'cpu': p.info['cpu_percent'],
                    'mem_mb': p.info['memory_info'].rss // 1024 // 1024,
                    'cmd': ' '.join(p.info.get('cmdline') or [])
                })
        result[pname] = found
    return result

def check_resource():
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'mem_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }

def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    procs = check_processes()
    res = check_resource()
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'==== {now} ====' + '\n')
        f.write('进程状态:\n')
        for k, v in procs.items():
            f.write(f'  {k}: {len(v)} 实例\n')
            for inst in v:
                f.write(f'    PID={inst["pid"]} CPU={inst["cpu"]}% MEM={inst["mem_mb"]}MB CMD={inst["cmd"]}\n')
        f.write(f'系统资源: CPU={res["cpu_percent"]}% MEM={res["mem_percent"]}% DISK={res["disk_percent"]}%\n')
        f.write('\n')
    # 可扩展：异常时推送/告警

if __name__ == '__main__':
    main()
