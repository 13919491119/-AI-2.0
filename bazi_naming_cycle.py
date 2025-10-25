#!/usr/bin/env python3
"""
八字起名任务循环（轻量）：
- 读取队列文件 queue/bazi_naming.jsonl（每行一个请求）
- 字段：surname, bazi, gender=neutral, count=10, style=neutral, single=false
- 生成结果写入 results/bazi_naming/<timestamp>.json，并在日志中输出简要信息
- 若队列不存在则按间隔休眠等待

环境变量：
- BAZI_NAMING_INTERVAL_SECONDS (默认 60)

依赖：bazi_naming.generate_names
"""
import os
import sys
import json
import time
import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from bazi_naming import generate_names, load_element_chars
except Exception as e:
    print(f"[bazi_naming_cycle] 导入 bazi_naming 失败: {e}", flush=True)
    generate_names = None  # type: ignore
    load_element_chars = None  # type: ignore

try:
    from deepseek_api import DeepseekAPI  # type: ignore
except Exception:
    DeepseekAPI = None  # type: ignore

ROOT = Path(__file__).resolve().parent
QUEUE = ROOT / 'queue' / 'bazi_naming.jsonl'
OUT_DIR = ROOT / 'results' / 'bazi_naming'
LOG = ROOT / 'logs' / 'bazi_naming_cycle.log'

OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG.parent.mkdir(parents=True, exist_ok=True)


def _interval() -> int:
    try:
        v = int(os.getenv('BAZI_NAMING_INTERVAL_SECONDS', '60'))
        return max(5, min(3600, v))
    except Exception:
        return 60


def _read_one() -> Dict[str, Any] | None:
    if not QUEUE.exists():
        return None
    try:
        with open(QUEUE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines:
            return None
        first = lines[0]
        remain = lines[1:]
        # 覆盖写回剩余
        with open(QUEUE, 'w', encoding='utf-8') as f:
            f.writelines(remain)
        return json.loads(first)
    except Exception as e:
        print(f"[bazi_naming_cycle] 读取队列失败: {e}", flush=True)
        return None


def _write_result(req: Dict[str, Any], data: Dict[str, Any]) -> None:
    ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    path = OUT_DIR / f"{ts}.json"
    latest = OUT_DIR / "latest.json"
    raw_path = OUT_DIR / f"{ts}_deepseek_raw.txt"
    try:
        payload = {
            'request': req,
            'result': data,
            'timestamp': ts,
        }
        # 写主结果文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # 如果 deepseek 解析失败，落盘原始内容以便排障
        try:
            ds = (data or {}).get('deepseek') if isinstance(data, dict) else None
            if isinstance(ds, dict) and ds.get('error') == 'parse_failed' and ds.get('raw'):
                with open(raw_path, 'w', encoding='utf-8') as rf:
                    rf.write(str(ds.get('raw')))
                print(f"[bazi_naming_cycle] deepseek parse_failed, raw saved: {raw_path}", flush=True)
        except Exception as e:
            print(f"[bazi_naming_cycle] save raw failed: {e}", flush=True)
        # 同步更新 latest.json（原子替换）
        try:
            tmp = OUT_DIR / "latest.json.tmp"
            with open(tmp, 'w', encoding='utf-8') as lf:
                json.dump(payload, lf, ensure_ascii=False, indent=2)
            os.replace(tmp, latest)
        except Exception as e:
            print(f"[bazi_naming_cycle] update latest.json failed: {e}", flush=True)
        print(f"[bazi_naming_cycle] 写入结果: {path}", flush=True)
    except Exception as e:
        print(f"[bazi_naming_cycle] 写入结果失败: {e}", flush=True)


def _deepseek_enabled() -> bool:
    v = os.getenv('BAZI_NAMING_DEEPSEEK', '0').strip()
    return v in ('1', 'true', 'True', 'yes', 'on')


def _local_rank(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """基于五行偏好进行本地简易加权排序，返回前15项。
    规则：金+2.0, 水+1.5, 木+0.8, 火-0.5, 土-1.0；
          组合加成：金+水 +0.30，金+木 +0.15，水+木 +0.10
    """
    if not candidates or load_element_chars is None:
        return []
    try:
        lib = load_element_chars()
        char2elem = {ch: e for e, chs in lib.items() for ch in chs}
    except Exception:
        return []

    weights = {'金': 2.0, '水': 1.5, '木': 0.8, '火': -0.5, '土': -1.0}

    def score_name(name: str):
        given = name[1:]
        elems = [char2elem.get(ch) for ch in given]
        s = 0.0
        for e in elems:
            if e:
                s += weights.get(e, 0)
        if len(elems) == 2 and elems[0] and elems[1] and elems[0] != elems[1]:
            pair = set(elems)
            if pair.issubset({'金', '水'}):
                s += 0.30
            elif pair == {'金', '木'}:
                s += 0.15
            elif pair == {'水', '木'}:
                s += 0.10
        return round(s, 3), elems

    scored: List[Dict[str, Any]] = []
    for c in candidates:
        nm = c.get('name')
        if not nm:
            continue
        s, elems = score_name(nm)
        scored.append({'name': nm, 'score_local': s, 'elems': elems})
    scored.sort(key=lambda x: x['score_local'], reverse=True)
    return scored[:15]


def _try_deepseek(base_top: List[Dict[str, Any]], surname: str, bazi_text: str) -> Dict[str, Any]:
    """调用 DeepSeek 对 base_top 进行语义/文化精调排序，返回 {'items': [...], 'top3': [...]} 或 {'error': ...}
    安全失败：返回 error，不抛异常。
    """
    if not _deepseek_enabled():
        return {'error': 'disabled'}
    key = os.getenv('DEEPSEEK_API_KEY')
    if not key:
        return {'error': 'no_api_key'}
    if DeepseekAPI is None:
        return {'error': 'client_unavailable'}
    try:
        api = DeepseekAPI(api_key=key)
        bazi_desc = '按本地分析：日主癸水，局中土火偏旺，喜金为首、水次之，木少量为宜，忌火土过多。'
        names_block = [
            {'name': it['name'], 'elems': it.get('elems'), 'local': it.get('score_local', 0)}
            for it in base_top
        ]
        sys_prompt = (
            '你是中文起名与周易顾问。请严格按要求仅输出合法JSON，'
            '基于五行喜用、语义美感、音律与歧义规避，对候选名综合评分。'
        )
        user_prompt = {
            'context': {
                'gender': 'female',
                'surname': surname,
                'bazi': bazi_text.replace('年', ' ').replace('月', ' ').replace('日', ' ').replace('时', ' ').strip(),
                'preference': '金>水>木(少量)，避火土',
                'bazi_note': bazi_desc,
            },
            'candidates': names_block,
            'instruction': (
                '请按 0~10 打分，给出理由，返回 {"items":[{"name":"..","score":..,"reason":".."},..],'
                '"top3":["..","..",".."]}。只输出纯JSON，不要任何额外文字；若无法完成，请仅输出 {}。'
            ),
        }
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ]
        resp = api.chat(messages, model="deepseek-chat", temperature=0.35, max_tokens=1400)
        content = (
            resp.get('choices', [{}])[0].get('message', {}).get('content', '') if isinstance(resp, dict) else ''
        ).strip()
        js = None
        try:
            js = json.loads(content)
        except Exception:
            import re
            m = re.search(r'\{.*\}', content, re.S)
            if m:
                try:
                    js = json.loads(m.group(0))
                except Exception:
                    js = None
        if js and isinstance(js, dict) and 'items' in js:
            byname = {it['name']: it for it in base_top}
            refined: List[Dict[str, Any]] = []
            for it in js.get('items', []):
                nm = it.get('name')
                sc = it.get('score', 0)
                rsn = it.get('reason', '')
                if nm in byname:
                    base = byname[nm]
                    refined.append({
                        'name': nm,
                        'score_ai': sc,
                        'reason': rsn,
                        'elems': base.get('elems'),
                        'score_local': base.get('score_local'),
                    })
            refined.sort(key=lambda x: (x['score_ai'], x['score_local']), reverse=True)
            return {'items': refined[:10], 'top3': js.get('top3')}
        return {'error': 'parse_failed', 'raw': content}
    except Exception as e:
        return {'error': str(e)}


def main() -> None:
    print("[bazi_naming_cycle] 启动", flush=True)
    if generate_names is None:
        print("[bazi_naming_cycle] bazi_naming 不可用，进入空闲等待模式", flush=True)
    while True:
        req = _read_one()
        if req is None:
            time.sleep(_interval())
            continue
        try:
            surname = req.get('surname') or '张'
            bazi = req.get('bazi') or '辛酉年 丁未月 壬午日 戊午时'
            gender = req.get('gender') or 'neutral'
            count = int(req.get('count') or 10)
            style = req.get('style') or 'neutral'
            single = bool(req.get('single') or False)
            if generate_names is None:
                data = {'error': 'generate_names unavailable', 'items': []}
            else:
                data = generate_names(surname=surname, bazi_text=bazi, gender=gender, count=count, style=style, single=single)
                # 可选：本地排序摘要
                try:
                    base_top = _local_rank(data.get('candidates') or [])
                    print(f"[bazi_naming_cycle] base_top computed: {len(base_top)}", flush=True)
                    if base_top:
                        data['base_top'] = base_top
                except Exception as e:
                    print(f"[bazi_naming_cycle] base_top error: {e}", flush=True)
                # 可选：DeepSeek 精调
                try:
                    if _deepseek_enabled():
                        print("[bazi_naming_cycle] deepseek enabled", flush=True)
                        ds = _try_deepseek(data.get('base_top') or [], surname=surname, bazi_text=bazi)
                        data['deepseek'] = ds
                        print(f"[bazi_naming_cycle] deepseek status: {('ok' if 'items' in ds else ds.get('error'))}", flush=True)
                    else:
                        print("[bazi_naming_cycle] deepseek disabled", flush=True)
                except Exception as e:
                    data['deepseek'] = { 'error': str(e) }
                    print(f"[bazi_naming_cycle] deepseek error: {e}", flush=True)
            _write_result(req, data)
        except Exception as e:
            print(f"[bazi_naming_cycle] 处理失败: {e}", flush=True)
        # 小间隔，避免忙等
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("[bazi_naming_cycle] 退出", flush=True)
        sys.exit(0)
