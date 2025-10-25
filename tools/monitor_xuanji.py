#!/usr/bin/env python3
"""
简单监控脚本：每 60s 轮询主要日志并检查 upgrade_plan_* 文件。
输出到 logs/monitor.log，并在发现异常或新 pending plan 时打印摘要到
stdout（便于容器/后台观察）。
"""
import time
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = {
    'autonomous': ROOT / 'xuanji_autonomous.log',
    'api': ROOT / 'xuanji_api.log',
    'cultural': ROOT / 'auto_learn_cultural_deep.log',
    'predict': ROOT / 'auto_learn_predict.log',
    'optimize': ROOT / 'auto_optimize_cycle.log',
}
MONLOG = ROOT / 'logs' / 'monitor.log'
MONLOG.parent.mkdir(exist_ok=True)

seen_pending = set()


def tail_file(path, n=20):
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            size = f.tell()
            block = 1024
            data = b''
            while n > 0 and size > 0:
                if size - block > 0:
                    f.seek(size - block)
                else:
                    f.seek(0)
                data = f.read() + data
                size -= block
                n -= 1
            return data.decode('utf-8', errors='ignore').splitlines()[-20:]
    except Exception:
        return []


def check_logs():
    issues = []
    for name, p in LOGS.items():
        if p.exists():
            lines = tail_file(p, 50)
            for line_text in lines:
                if (
                    'Traceback' in line_text
                    or 'ERROR' in line_text
                    or 'Exception' in line_text
                ):
                    issues.append((name, line_text))
    return issues


def check_upgrade():
    pending = Path(ROOT / 'upgrade_plan_pending.json')
    approved = Path(ROOT / 'upgrade_plan_approved.json')
    rejected = Path(ROOT / 'upgrade_plan_rejected.json')
    found = {}
    if pending.exists():
        try:
            j = json.loads(pending.read_text(encoding='utf-8'))
        except Exception:
            j = {'raw': pending.read_text(encoding='utf-8')}
        found['pending'] = j
    if approved.exists():
        try:
            j = json.loads(approved.read_text(encoding='utf-8'))
        except Exception:
            j = {'raw': approved.read_text(encoding='utf-8')}
        found['approved'] = j
    if rejected.exists():
        try:
            j = json.loads(rejected.read_text(encoding='utf-8'))
        except Exception:
            j = {'raw': rejected.read_text(encoding='utf-8')}
        found['rejected'] = j
    return found


def write_monlog(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}\n"
    with open(MONLOG, 'a', encoding='utf-8') as f:
        f.write(line)
    print(line, end='')


def main():
    write_monlog('监控启动')
    while True:
        issues = check_logs()
        if issues:
            for name, line_text in issues:
                write_monlog(f'日志问题 {name}: {line_text[:200]}')
        ups = check_upgrade()
        if 'pending' in ups:
            pid = Path(ROOT / 'upgrade_plan_pending.json').stat().st_mtime
            if pid not in seen_pending:
                seen_pending.add(pid)
                write_monlog('发现新的 upgrade_plan_pending.json:')
                content = json.dumps(ups['pending'], ensure_ascii=False)
                write_monlog(content[:2000])
        if 'approved' in ups and 'approved' not in seen_pending:
            seen_pending.add('approved')
            write_monlog('发现 upgrade_plan_approved.json')
        if 'rejected' in ups and 'rejected' not in seen_pending:
            seen_pending.add('rejected')
            write_monlog('发现 upgrade_plan_rejected.json')
        # 简要资源统计
        try:
            import psutil
            mem = psutil.virtual_memory()
            write_monlog(f"mem_used={mem.percent}%")
        except Exception:
            pass
        time.sleep(60)


if __name__ == '__main__':
    main()
