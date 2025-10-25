"""
健康监控与自愈机制
- 定时检测主循环、预测服务、关键进程与资源
- 异常自动重启主控脚本
- 日志输出健康状态
"""
import os
import time
import psutil

LOG_FILE = 'health_report.log'
CHECK_INTERVAL = 60  # 秒
KEY_PROCESSES = ['autonomous_run.py', 'ssq_predict_cycle.py', 'api_server.py']

# 检查关键进程是否存活
def check_processes():
    alive = {p: False for p in KEY_PROCESSES}
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        for key in KEY_PROCESSES:
            if any(key in str(x) for x in proc.info['cmdline']):
                alive[key] = True
    return alive

def restart_script(script):
    os.system(f'nohup python3 {script} &')

def log_health(status):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {status}\n")

def main():
    while True:
        alive = check_processes()
        status = f"进程状态: {alive}"
        # 检查内存、磁盘
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        status += f" | 内存: {mem.percent}% | 磁盘: {disk.percent}%"
        # 自愈机制：如有关键进程未存活则重启
        for k, v in alive.items():
            if not v:
                restart_script(k)
                status += f" | 已重启: {k}"
        log_health(status)
        print(status)
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
