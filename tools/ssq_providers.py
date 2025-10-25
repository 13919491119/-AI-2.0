#!/usr/bin/env python3
"""
双色球开奖抓取提供者集合。
返回统一结构：{
  'period': '2025117',
  'date': '2025-10-12',   # YYYY-MM-DD（北京时间）
  'week': '日',            # 可选
  'reds': [1,7,12,18,23,30],
  'blue': 6
}

提供者优先级：
  1) cwl_gov (中国福彩网官方接口)
  2) file（本地 data/latest_ssq.json，用于内网/联调）
  3) mock（离线回退）

使用环境变量控制：
  SSQ_PROVIDER: auto|cwl|file|mock （默认 auto）
  LATEST_FILE: data/latest_ssq.json （默认）
"""
from __future__ import annotations

import os, json, random
from datetime import datetime
from typing import Dict, Any, List


def _normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    period = str(payload['period']).strip()
    reds = [int(x) for x in payload['reds']]
    blue = int(payload['blue'])
    date = payload.get('date')
    week = payload.get('week')
    return {
        'period': period,
        'date': date,
        'week': week,
        'reds': reds,
        'blue': blue,
    }


def provider_cwl() -> Dict[str, Any]:
    """中国福彩网官方接口。
    参考： https://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice?name=ssq&issueCount=1&pageNo=1
    返回 JSON 包含 result 列表，取第一条。
    """
    import requests  # type: ignore
    url = "https://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice"
    params = {'name': 'ssq', 'issueCount': '1', 'pageNo': '1'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; XuanJiBot/1.0)'
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    obj = r.json()
    # 兼容不同键名
    arr: List[Dict[str, Any]] = obj.get('result') or obj.get('list') or []
    if not arr:
        raise RuntimeError('cwl.gov empty result')
    it = arr[0]
    period = str(it.get('code') or it.get('period'))
    date = str(it.get('date') or it.get('openTime') or '')
    week = it.get('week')
    # red 通常是 "01,07,12,18,23,30"，blue 是 "06" 或数值
    red_s = it.get('red') or it.get('redBall')
    blue_s = it.get('blue') or it.get('blueBall')
    if isinstance(red_s, str):
        reds = [int(x) for x in red_s.replace(' ', '').split(',') if x]
    else:
        reds = list(map(int, red_s))  # type: ignore
    blue = int(blue_s)
    if len(reds) != 6 or not (1 <= blue <= 16):
        raise RuntimeError('cwl.gov invalid balls')
    return _normalize({'period': period, 'date': date, 'week': week, 'reds': reds, 'blue': blue})


def provider_file(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    if not (obj and obj.get('period') and obj.get('reds') and obj.get('blue')):
        raise ValueError('invalid latest_ssq.json')
    return _normalize(obj)


def provider_mock() -> Dict[str, Any]:
    today = datetime.now().strftime('%Y-%m-%d')
    period = datetime.now().strftime('%Y%j')
    reds = sorted(random.sample(range(1, 34), 6))
    blue = random.randint(1, 16)
    return _normalize({'period': period, 'date': today, 'week': None, 'reds': reds, 'blue': blue})


def fetch_latest() -> Dict[str, Any]:
    mode = os.getenv('SSQ_PROVIDER', 'auto').strip().lower()
    latest_file = os.getenv('LATEST_FILE') or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'latest_ssq.json')
    last_err: Exception | None = None
    for name in ([mode] if mode in ('cwl', 'file', 'mock') else ['cwl', 'file', 'mock']):
        try:
            if name == 'cwl':
                return provider_cwl()
            if name == 'file':
                return provider_file(latest_file)
            if name == 'mock':
                return provider_mock()
        except Exception as e:
            last_err = e
            continue
    # 全部失败时抛出最后一个错误
    if last_err:
        raise last_err
    raise RuntimeError('no provider available')
