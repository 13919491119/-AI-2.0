import subprocess
import time
import os
import json
from datetime import datetime, timezone

def is_task_running(task_name):
    """检查包含 task_name 的进程是否存在。"""
    try:
        out = subprocess.check_output(['pgrep', '-f', task_name])
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False

def start_task(cmd, log_path=None, cwd=None):
    """启动任务，输出重定向到独立日志（可选）。"""
    print(f'AI守护进程：启动任务 {cmd}')
    env = os.environ.copy()
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'ab') as lf:
            subprocess.Popen(cmd, shell=True, stdout=lf, stderr=lf, cwd=cwd, env=env)
    else:
        subprocess.Popen(cmd, shell=True, cwd=cwd, env=env)

def _now():
    # 使用 timezone-aware UTC 时间，避免弃用警告
    return datetime.now(timezone.utc).isoformat()

def _heal_common_issues():
    """常见故障自愈：
    - 清理遗留的 git index.lock（无 git 进程时）
    - 清理无效 PID 文件（autonomous_run.pid）
    - 确保必要目录存在（logs、reports、heartbeats）
    """
    # git index.lock
    try:
        git_running = (subprocess.call(['pgrep', 'git'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0)
        lock_path = os.path.join('.git', 'index.lock')
        if not git_running and os.path.exists(lock_path):
            os.remove(lock_path)
            print('[自愈] 已清理 .git/index.lock')
    except Exception:
        pass
    # orphan pid
    try:
        pid_file = os.path.join(os.path.dirname(__file__), 'autonomous_run.pid')
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r', encoding='utf-8') as f:
                    pid = int((f.read() or '0').strip() or '0')
                if pid > 0:
                    # 检查是否存活
                    try:
                        os.kill(pid, 0)
                        # 存活则不处理
                    except Exception:
                        os.remove(pid_file)
                        print('[自愈] 移除失效 autonomous_run.pid')
            except Exception:
                pass
    except Exception:
        pass
    # ensure dirs
    for d in ('logs', 'reports', 'heartbeats'):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass

def ai_guard_loop():
    """监控多任务：异常退出自动重启，支持心跳超时自愈与重试退避。"""
    tasks = [
        {
            'name': 'autonomous_run',
            'match': 'autonomous_run.py',
            'cmd': 'python3 autonomous_run.py',
            'log': 'logs/autonomous_run.log',
            'heartbeat': 'heartbeats/autonomous_run.json',
            'heartbeat_timeout_sec': 180,
        },
        {
            'name': 'deep_learning_cycle',
            'match': 'deep_learning_cycle.py',
            'cmd': 'python3 deep_learning_cycle.py',
            'log': 'logs/deep_learning_cycle.log',
            'heartbeat': 'heartbeats/deep_learning_cycle.json',
            'heartbeat_timeout_sec': 300,
        },
        {
            'name': 'yi_books_collect',
            'match': 'yi_books_collect.py',
            'cmd': 'python3 yi_books_collect.py',
            'log': 'logs/yi_books_collect.log',
            'heartbeat': 'heartbeats/yi_books_collect.json',
            'heartbeat_timeout_sec': 7200,  # 2小时无更新判定为超时
        },
        {
            'name': 'batch_predict_persons',
            'match': 'batch_predict_persons.py',
            'cmd': 'python3 batch_predict_persons.py',
            'log': 'logs/batch_predict_persons.log',
            'heartbeat': 'heartbeats/batch_predict_persons.json',
            'heartbeat_timeout_sec': 300,  # 5分钟
        },
    ]

    backoff = {t['name']: {'fails': 0, 'last': 0.0} for t in tasks}
    status_path = 'reports/ai_guard_status.json'
    # 知识摄取定时任务配置（默认6小时）
    ingest_interval = int(os.getenv('KNOWLEDGE_INGEST_INTERVAL_SEC', str(6 * 3600)))
    ingest_stamp = 'reports/knowledge_ingest_last_run.txt'
    try:
        from heartbeat_manager import write_heartbeat as _write_hb  # 统一心跳
    except Exception:
        def _write_hb(name: str, **kwargs):
            try:
                os.makedirs('heartbeats', exist_ok=True)
                data = {'ts': time.time(), 'pid': os.getpid()}
                data.update(kwargs)
                with open(os.path.join('heartbeats', f'{name}.json'), 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception:
                pass

    while True:
        _heal_common_issues()
        # 定时触发知识摄取（一次性作业，不纳入常驻任务列表）
        try:
            now = time.time()
            last = 0.0
            if os.path.exists(ingest_stamp):
                try:
                    with open(ingest_stamp, 'r', encoding='utf-8') as f:
                        last = float((f.read() or '0').strip() or '0')
                except Exception:
                    last = 0.0
            if (now - last) >= ingest_interval or not os.path.exists(ingest_stamp):
                print('[守护] 触发知识摄取管线运行')
                start_task('python3 knowledge_ingest_pipeline.py', log_path='logs/knowledge_ingest.log')
                # 立即记录时间戳，防止重复触发；实际完成由日志确认
                os.makedirs(os.path.dirname(ingest_stamp), exist_ok=True)
                with open(ingest_stamp, 'w', encoding='utf-8') as f:
                    f.write(str(now))
                _write_hb('knowledge_ingest', event='scheduled', interval_sec=ingest_interval)
        except Exception:
            pass

        for t in tasks:
            name = t['name']
            running = is_task_running(t['match'])
            need_restart = not running
            # 心跳超时检测
            hb_path = t.get('heartbeat')
            if running and hb_path:
                try:
                    if os.path.exists(hb_path):
                        with open(hb_path, 'r', encoding='utf-8') as f:
                            hb = json.load(f)
                        ts = float(hb.get('time_end') or hb.get('timestamp') or hb.get('ts') or 0)
                        if ts > 0 and (time.time() - ts) > t.get('heartbeat_timeout_sec', 300):
                            print(f"[守护] {name} 心跳超时，触发重启")
                            # 杀掉旧进程
                            try:
                                subprocess.call(['pkill', '-f', t['match']])
                            except Exception:
                                pass
                            need_restart = True
                except Exception:
                    pass

            if need_restart:
                now = time.time()
                fails = backoff[name]['fails']
                last = backoff[name]['last']
                delay = min(300, (2 ** min(fails, 6)))  # 指数退避，最大5分钟
                if (now - last) < delay:
                    # 退避等待
                    continue
                start_task(t['cmd'], log_path=t.get('log'))
                backoff[name]['last'] = now
                # 如果刚才是失败后重启，增加失败计数；否则重置
                backoff[name]['fails'] = min(fails + (1 if not running else 0), 100)
            else:
                # 正常运行则清零失败计数
                backoff[name]['fails'] = 0

        # 写入守护状态
        try:
            os.makedirs(os.path.dirname(status_path), exist_ok=True)
            state = {t['name']:
                     {'running': is_task_running(t['match']), 'last_check': _now(), 'fails': backoff[t['name']]['fails']}
                     for t in tasks}
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        print('任务巡检完成，AI守护进程持续监控')
        time.sleep(15)

if __name__ == '__main__':
    ai_guard_loop()
