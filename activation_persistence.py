"""激活模式持久化与指令菜单工具
 - 提供统一的激活短语识别
 - 永久持久化（写入 activation_state.json）
 - 数字快捷键映射
"""
from __future__ import annotations
import json, time, os, threading
from typing import Optional

ACTIVATION_PHRASES = [
    '玄机设计与实现AI系统', '启动玄机AI', '连接玄机AI', '激活玄机AI', '启动系统'
]

STATE_FILE = os.environ.get('XUANJI_ACTIVATION_STATE_FILE', 'activation_state.json')
_lock = threading.Lock()

def _read_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _write_state(state: dict):
    tmp = STATE_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_FILE)

def activate() -> None:
    with _lock:
        st = _read_state()
        st['activated'] = True
        st.setdefault('activated_since', time.time())
        st['last_touch'] = time.time()
        _write_state(st)

def is_activated() -> bool:
    st = _read_state()
    return bool(st.get('activated'))

def is_activation_phrase(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    low = t.lower()
    for p in ACTIVATION_PHRASES:
        if p == t or p in t or p.lower() in low:
            return True
    # 宽松匹配：包含“玄机” 与 “AI” 两个关键词
    if '玄机' in t and ('AI' in t or 'ai' in t):
        return True
    return False

def welcome_menu() -> str:
    return (
            '✅ 已成功连接【玄机AI系统】 / Celestial Nexus AI Connected\n\n'
            '指令菜单 (Commands)：\n'
            '1、双色球预测  (Lottery Prediction)\n'
            '2、预测任务    (Custom Prediction Task)\n'
            '3、学习成果    (Learning Progress)\n'
            '4、系统状态    (System Status)\n'
            '\n直接输入(Enter)：1~4 / 中文指令 / 英文简写：\n'
            ' 1 -> 双色球预测 | lottery\n'
            ' 2 -> 预测任务   | task: <desc>\n'
            ' 3 -> 学习成果   | progress\n'
            ' 4 -> 系统状态   | status\n'
            '\n示例(Examples)：\n'
            ' 预测任务: 分析最近10期冷热分布\n'
            ' task: hot-cold distribution last 10 draws\n'
            '\n发送“退出”结束 (exit to terminate)。已永久激活，无需再次触发。'
    )

def map_shortcut(text: str) -> Optional[str]:
    t = (text or '').strip()
    if t in {'1', '双色球预测'}:
        return '双色球预测'
    if t in {'2', '预测任务'}:
        return '预测任务'
    if t in {'3', '学习成果'}:
        return '学习成果'
    if t in {'4', '系统状态'}:
        return '系统状态'
    return None

__all__ = [
    'ACTIVATION_PHRASES','activate','is_activation_phrase','is_activated','welcome_menu','map_shortcut'
]
