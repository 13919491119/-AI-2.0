#!/usr/bin/env python3
"""
监控 patterns_knowledge.json 的变更并立即触发一次快速调优。
- 轮询方式（默认每 10 秒），可通过环境变量配置：
  - PATTERN_TUNE_POLL_INTERVAL（秒，默认 10）
  - PATTERN_TUNE_COOLDOWN（秒，默认 600）：两次触发之间的最小间隔
  - PATTERN_TUNE_STABILITY（秒，默认 3）：检测到变化后等待文件稳定的时间
  - PATTERN_TUNE_WINDOW（默认 2000）、PATTERN_TUNE_EMA（默认 0.6）、PATTERN_TUNE_TRAIN_AI（1/0）
- 调优命令：python ssq_auto_tuner.py --data ssq_history.csv --train-ai --window <W> --ema <A>
- 日志：标准输出；supervisor 重定向到 logs/supervisor/xuanji_tune_on_change.*.log
"""
from __future__ import annotations
import os, sys, time, json, hashlib, subprocess, importlib
from typing import Optional

ROOT = "/workspaces/-AI-2.0"
WATCH_FILE = os.path.join(ROOT, "patterns_knowledge.json")

# 载入 .env（若有）或简单解析
def _load_env(path: str):
    try:
        dotenv = importlib.import_module("dotenv")
        if hasattr(dotenv, "load_dotenv"):
            dotenv.load_dotenv(dotenv_path=path)
            return
    except Exception:
        pass
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip(); v = v.strip().strip('"').strip("'")
                        if k and (k not in os.environ):
                            os.environ[k] = v
    except Exception:
        pass

_load_env(os.path.join(ROOT, ".env"))

POLL = int(os.getenv("PATTERN_TUNE_POLL_INTERVAL", "10"))
COOLDOWN = int(os.getenv("PATTERN_TUNE_COOLDOWN", "600"))
STABILITY = int(os.getenv("PATTERN_TUNE_STABILITY", "3"))
WIN = int(os.getenv("PATTERN_TUNE_WINDOW", "200"))
EMA = float(os.getenv("PATTERN_TUNE_EMA", "0.6"))
TRAIN_AI = os.getenv("PATTERN_TUNE_TRAIN_AI", "1") in ("1", "true", "True")

PY = sys.executable or "python"

def file_hash(path: str) -> Optional[str]:
    if not os.path.exists(path):
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(64*1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def run_tuner():
    cmd = [PY, os.path.join(ROOT, "ssq_auto_tuner.py"), "--data", "ssq_history.csv", "--window", str(WIN), "--ema", str(EMA)]
    if TRAIN_AI:
        cmd.append("--train-ai")
    print(f"[watch] 触发调优: {' '.join(cmd)}", flush=True)
    p = subprocess.run(cmd, cwd=ROOT, text=True)
    print(f"[watch] 调优完成，退出码 {p.returncode}", flush=True)


def main():
    print(f"[watch] 启动 模式变更即刻调优 监视器：{WATCH_FILE}")
    last_hash = file_hash(WATCH_FILE)
    last_tune = 0.0
    if last_hash is None:
        print("[watch] 等待文件创建...")
    while True:
        try:
            cur_hash = file_hash(WATCH_FILE)
            if cur_hash is not None and cur_hash != last_hash:
                # 等待稳定
                time.sleep(STABILITY)
                stable_hash = file_hash(WATCH_FILE)
                if stable_hash != cur_hash:
                    # 写入仍在进行，跳过本轮
                    last_hash = stable_hash
                    time.sleep(POLL)
                    continue
                now = time.time()
                if now - last_tune >= COOLDOWN:
                    print(f"[watch] 检测到模式知识库更新（{last_hash} -> {cur_hash}），准备触发调优")
                    run_tuner()
                    last_tune = time.time()
                else:
                    print(f"[watch] 检测到更新但处于冷却期（剩余 {int(COOLDOWN - (now - last_tune))}s）")
                last_hash = cur_hash
        except Exception as e:
            print(f"[watch] 监视异常：{e}")
        time.sleep(POLL)

if __name__ == "__main__":
    main()
