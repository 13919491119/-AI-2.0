#!/usr/bin/env python3
"""
系统自治运行检测脚本

检测项：
1. 守护状态文件存在且解析成功
2. 核心任务 (autonomous_run, deep_learning_cycle, yi_books_collect, batch_predict_persons) 全部 running
3. 心跳文件最近更新时间未超时（依各自阈值）
4. 关键结果文件存在并非空：deep_learning_cycle_results.jsonl, person_predict_results.jsonl
5. 日志文件存在（用于追踪）

输出：
- JSON 格式评估摘要（stdout）
- 退出码：0 全部通过；1 有警告；2 有严重失败
"""
import os, json, time, sys

ROOT = os.path.abspath(os.path.dirname(__file__))
STATUS_FILE = os.path.join(ROOT, 'reports', 'ai_guard_status.json')
HEART_DIR = os.path.join(ROOT, 'heartbeats')
RESULT_FILES = [
    os.path.join(ROOT, 'deep_learning_cycle_results.jsonl'),
    os.path.join(ROOT, 'person_predict_results.jsonl'),
]
LOG_DIR = os.path.join(ROOT, 'logs')

# 心跳超时阈值定义（秒）
HEART_TIMEOUTS = {
    'autonomous_run': 180,
    'deep_learning_cycle': 300,
    'yi_books_collect': 7200,
    'batch_predict_persons': 300,
}

def load_status():
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def load_heartbeat(name: str):
    path = os.path.join(HEART_DIR, f'{name}.json')
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        return None
    return None

def main():
    summary = {
        'timestamp': time.time(),
        'status_file_exists': os.path.exists(STATUS_FILE),
        'status': None,
        'tasks': {},
        'result_files': {},
        'log_dir_exists': os.path.isdir(LOG_DIR),
        'overall': 'unknown',
        'warnings': [],
        'errors': []
    }
    status = load_status()
    summary['status'] = status
    if not status:
        summary['errors'].append('STATUS_FILE_MISSING_OR_INVALID')
    # 任务运行与心跳检查
    now = time.time()
    for task in HEART_TIMEOUTS.keys():
        tinfo = {
            'running': False,
            'heartbeat_age_sec': None,
            'heartbeat_ok': None,
        }
        if status and task in status:
            tinfo['running'] = bool(status[task].get('running'))
            if not tinfo['running']:
                summary['errors'].append(f'TASK_NOT_RUNNING:{task}')
        hb = load_heartbeat(task)
        if hb:
            ts = float(hb.get('time_end') or hb.get('timestamp') or hb.get('ts') or 0)
            if ts > 0:
                age = now - ts
                tinfo['heartbeat_age_sec'] = round(age, 2)
                timeout = HEART_TIMEOUTS[task]
                tinfo['heartbeat_ok'] = age <= timeout
                if not tinfo['heartbeat_ok']:
                    summary['warnings'].append(f'HEARTBEAT_TIMEOUT:{task}:{int(age)}s')
            else:
                summary['warnings'].append(f'HEARTBEAT_TS_INVALID:{task}')
        else:
            summary['warnings'].append(f'HEARTBEAT_MISSING:{task}')
        summary['tasks'][task] = tinfo
    # 结果文件检查
    for rf in RESULT_FILES:
        info = {'exists': os.path.exists(rf), 'non_empty': False, 'lines': 0}
        if info['exists']:
            try:
                size = os.path.getsize(rf)
                info['non_empty'] = size > 0
                with open(rf, 'r', encoding='utf-8') as f:
                    cnt = sum(1 for _ in f)
                info['lines'] = cnt
                if cnt == 0:
                    summary['warnings'].append(f'RESULT_EMPTY:{os.path.basename(rf)}')
            except Exception:
                summary['warnings'].append(f'RESULT_READ_FAIL:{os.path.basename(rf)}')
        else:
            summary['warnings'].append(f'RESULT_MISSING:{os.path.basename(rf)}')
        summary['result_files'][os.path.basename(rf)] = info

    # overall 判定
    if summary['errors']:
        summary['overall'] = 'fail'
        exit_code = 2
    elif summary['warnings']:
        summary['overall'] = 'warn'
        exit_code = 1
    else:
        summary['overall'] = 'pass'
        exit_code = 0

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
