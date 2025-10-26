"""
八字起名模块（增强版，轻量无外部依赖）
- 输入：姓氏、八字字符串（如："辛酉年 丁未月 壬午日 戊午时"）、性别、风格、是否单名、数量
- 处理：解析四柱，统计五行强弱；基于“缺/弱五行优先”，叠加性别与风格偏好，按规则组合单名/双名；按得分排序
- 输出：候选名字列表，附解释（弱项补益、性别/风格取向）与用字五行

说明：
- 不做历法换算（转换请用 bazi_chart 模块的 solar2bazi/lunar2bazi）；
- 词库来源：data/element_chars.json 或根目录 element_chars.json；若均不存在则使用内建小字库。
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple, Optional

# 天干地支五行映射（常用版本，简化）
GAN_WUXING = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
    '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'
}
ZHI_WUXING = {
    '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
    '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'
}

WUXING_ORDER = ['金','木','水','火','土']

def load_element_chars() -> Dict[str, List[str]]:
    """加载五行取名常用字库（优先 data/element_chars.json，其次根目录 element_chars.json）。"""
    candidates = [
        os.path.join(os.getcwd(), 'data', 'element_chars.json'),
        os.path.join(os.getcwd(), 'element_chars.json'),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 仅取前若干，避免极端长列表影响排序/输出（可按需调整）
                    return {k: list(v) for k, v in data.items()}
            except Exception:
                continue
    # 兜底小字库
    return {
        '金': ['铭','锋','钧','鑫','铠','锐','钊','钟','镇','铎','鋆','铖'],
        '木': ['林','柏','柯','楠','栋','槐','桂','森','荣','桐','榕','槿'],
        '水': ['涵','清','润','泽','淇','洋','淳','渊','浩','涟','淞','沐'],
        '火': ['炎','煜','熙','瑜','炜','熠','烁','烽','焕','炫','炯','煊'],
        '土': ['坤','坡','城','垚','垣','堃','培','坦','墉','垦','堰','埕']
    }

def parse_bazi(bazi_text: str) -> Tuple[List[str], List[str]]:
    """解析八字字符串为天干列表与地支列表。输入示例："辛酉年 丁未月 壬午日 戊午时""" 
    text = bazi_text.replace('年',' ').replace('月',' ').replace('日',' ').replace('时',' ')
    parts = [p.strip() for p in text.split() if p.strip()]
    # 期望四柱，每柱两字：天干+地支
    gan: List[str] = []
    zhi: List[str] = []
    for p in parts:
        if len(p) >= 2:
            gan.append(p[0])
            zhi.append(p[1])
    # 截断到4柱
    return gan[:4], zhi[:4]

def count_wuxing(gan: List[str], zhi: List[str]) -> Dict[str, int]:
    counts = {w: 0 for w in WUXING_ORDER}
    for g in gan:
        w = GAN_WUXING.get(g)
        if w:
            counts[w] += 1
    for z in zhi:
        w = ZHI_WUXING.get(z)
        if w:
            counts[w] += 1
    return counts

def _gender_pref_sequence(gender: str) -> List[str]:
    g = (gender or 'neutral').lower()
    if g == 'male':
        return ['火','金','木','水','土']
    if g == 'female':
        return ['水','木','土','金','火']
    return WUXING_ORDER

def _style_pref_sequence(style: str) -> List[str]:
    s = (style or 'neutral').lower()
    # 风格-五行偏好（经验性、可按需调整）：
    # - classic：木/水/土更为含蓄传统
    # - elegant：水/木偏柔与雅
    # - modern：金/火偏锐与光
    if s == 'classic':
        return ['木','水','土','金','火']
    if s == 'elegant':
        return ['水','木','土','金','火']
    if s == 'modern':
        return ['金','火','木','水','土']
    return WUXING_ORDER

def _score_combo(c1: str, c2: Optional[str], primary: str, secondary: str, gender_seq: List[str], style_seq: List[str], lib_map: Dict[str, List[str]]) -> float:
    # 给定名组合的得分：弱项覆盖 + 性别风格偏好 + 基础频度
    def char_element(ch: str) -> Optional[str]:
        for e, chars in lib_map.items():
            if ch in chars:
                return e
        return None
    def elem_score(elem: Optional[str]) -> float:
        if not elem:
            return 0.0
        sc = 0.0
        if elem == primary:
            sc += 2.0
        if elem == secondary:
            sc += 1.0
        # 性别/风格序列越靠前分越高
        try:
            gi = gender_seq.index(elem)
            sc += (len(WUXING_ORDER) - gi) * 0.15
        except ValueError:
            pass
        try:
            si = style_seq.index(elem)
            sc += (len(WUXING_ORDER) - si) * 0.2
        except ValueError:
            pass
        return sc
    e1 = char_element(c1)
    e2 = char_element(c2) if c2 else None
    base = elem_score(e1) + (elem_score(e2) if c2 else 0.0)
    # 鼓励主弱+次弱的搭配
    if e1 == primary and (e2 == secondary if c2 else True):
        base += 0.4
    # 若双名，两字尽量不同元素以平衡（除非 primary 特别弱）
    if c2 and e1 and e2 and e1 != e2:
        base += 0.2
    return base

def pick_names(
    surname: str,
    counts: Dict[str, int],
    gender: str = 'neutral',
    count: int = 10,
    *,
    style: str = 'neutral',
    single: bool = False,
) -> List[Dict[str, str]]:
    """根据五行强弱、性别与风格偏好给出名字。
    - single=True 产出单字名；False 产出双字名。
    - 排序依据：弱项覆盖优先，叠加性别与风格序列权重。
    """
    lib = load_element_chars()
    # 找弱项（计数小者优先）
    weak_sorted = sorted(WUXING_ORDER, key=lambda w: counts.get(w, 0))
    primary = weak_sorted[0]
    secondary = weak_sorted[1]

    gender_seq = _gender_pref_sequence(gender)
    style_seq = _style_pref_sequence(style)

    # 候选池
    pool_primary = list(lib.get(primary, []))
    pool_secondary = list(lib.get(secondary, []))
    # 扩展：按性别与风格序列组织其它池
    extra_pools: List[str] = []
    for w in gender_seq:
        if w not in (primary, secondary):
            extra_pools.extend(lib.get(w, []))
    # 扩展风格（追加，保持去重）
    for w in style_seq:
        for ch in lib.get(w, []):
            if ch not in extra_pools and ch not in pool_primary and ch not in pool_secondary:
                extra_pools.append(ch)

    results: List[Dict[str, str]] = []
    used = set()

    def push_name(c1: str, c2: Optional[str]):
        if not c1:
            return
        if c1 == surname or (c2 and c2 == surname) or (c2 and c1 == c2):
            return
        name = f"{surname}{c1}{'' if single else (c2 or '')}"
        if name in used:
            return
        score = _score_combo(c1, None if single else c2, primary, secondary, gender_seq, style_seq, lib)
        explain = (
            f"弱项补益：主‘{primary}’{(' + 次‘'+secondary+'’') if not single else ''}；"
            f"风格：{style or 'neutral'}；性别：{gender or 'neutral'}"
        )
        used.add(name)
        results.append({
            'name': name,
            'explain': explain,
            'primary': primary,
            'secondary': secondary,
            'score': f"{score:.3f}",
        })

    # 生成候选
    if single:
        # 单字名：按主弱池为主，辅以偏好池补充
        for ch in pool_primary + pool_secondary + extra_pools:
            push_name(ch, None)
            if len(results) >= count * 3:
                break
    else:
        # 双字名：优先主弱+次弱，其次主弱+偏好
        pairs: List[Tuple[str, str]] = []
        for c1 in pool_primary:
            for c2 in (pool_secondary if pool_secondary else extra_pools):
                pairs.append((c1, c2))
        if not pool_secondary:
            # 主弱 + 偏好，补充更多组合
            for c1 in pool_primary[:20]:
                for c2 in extra_pools[:30]:
                    pairs.append((c1, c2))
        # 去重并截断
        seen = set()
        trimmed: List[Tuple[str, str]] = []
        for a,b in pairs:
            if (a,b) in seen or (b,a) in seen:
                continue
            seen.add((a,b))
            trimmed.append((a,b))
            if len(trimmed) >= 500:
                break
        for a,b in trimmed:
            push_name(a, b)

    # 排序取前N
    def score_key(x: Dict[str,str]) -> float:
        try:
            return float(x.get('score','0'))
        except Exception:
            return 0.0
    results.sort(key=score_key, reverse=True)
    # 去掉内部评分字段
    for r in results:
        r.pop('score', None)
    return results[:max(1, min(100, count))]

def generate_names(
    surname: str,
    bazi_text: str,
    gender: str = 'neutral',
    count: int = 10,
    *,
    style: str = 'neutral',
    single: bool = False,
) -> Dict[str, object]:
    gan, zhi = parse_bazi(bazi_text)
    counts = count_wuxing(gan, zhi)
    names = pick_names(surname, counts, gender=gender, count=count, style=style, single=single)
    return {
        'surname': surname,
        'bazi': {'gan': gan, 'zhi': zhi},
        'wuxing_counts': counts,
        'params': {'gender': gender, 'style': style, 'single': single, 'count': count},
        'candidates': names
    }

if __name__ == '__main__':
    demo = generate_names('李', '辛酉年 丁未月 壬午日 戊午时', gender='male', style='modern', single=False, count=8)
    print(json.dumps(demo, ensure_ascii=False, indent=2))
