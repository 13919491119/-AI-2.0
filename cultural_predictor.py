"""
文化预测引擎：基于公历/农历、干支四柱、节气与五行，构造对双色球红/蓝球的偏好分布。
用途：作为小六爻、小六壬、奇门遁甲的“文化信号”底座，由不同模型以不同权重使用。
"""
from __future__ import annotations

from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

try:
    from bazi_chart import solar2bazi
except Exception:
    solar2bazi = None  # type: ignore

# 五行映射
GAN_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# 红球1..33的五行分组（按 mod 5 分组近似映射）
RED_GROUPS: Dict[str, List[int]] = {
    '木': [1, 6, 11, 16, 21, 26, 31],
    '火': [2, 7, 12, 17, 22, 27, 32],
    '土': [3, 8, 13, 18, 23, 28, 33],
    '金': [4, 9, 14, 19, 24, 29],
    '水': [5, 10, 15, 20, 25, 30],
}

# 蓝球1..16的五行近似映射（同理按 mod 5 分组）
BLUE_GROUPS: Dict[str, List[int]] = {
    '木': [1, 6, 11, 16],
    '火': [2, 7, 12],
    '土': [3, 8, 13],
    '金': [4, 9, 14],
    '水': [5, 10, 15],
}

SEASON_WUXING = {
    1: '水', 2: '水', 12: '水',  # 冬
    3: '木', 4: '木',           # 春
    5: '火', 6: '火', 7: '火',   # 夏
    8: '土', 9: '金', 10: '金', 11: '金',  # 秋及长夏近似
}


def _bazi_for_datetime(dt: datetime) -> Optional[Dict[str, Any]]:
    if solar2bazi is None:
        return None
    try:
        return solar2bazi(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    except Exception:
        return None


def _pillar_wuxing(pillar: str) -> Optional[str]:
    if not pillar or not isinstance(pillar, str):
        return None
    gan = pillar[0]
    zhi = pillar[1] if len(pillar) > 1 else None
    # 以天干为主，地支为辅
    if gan in GAN_WUXING:
        return GAN_WUXING[gan]
    if zhi and zhi in ZHI_WUXING:
        return ZHI_WUXING[zhi]
    return None


class CulturalPredictor:
    def __init__(self, dt: Optional[datetime] = None):
        self.dt = dt or datetime.now()
        self.bazi = _bazi_for_datetime(self.dt)

    def scores(self, bias: Dict[str, float] | None = None) -> Tuple[Dict[int, float], Dict[int, float]]:
        """返回红/蓝球的打分（分数越高越偏好）。"""
        red_scores: Dict[int, float] = {i: 0.0 for i in range(1, 34)}
        blue_scores: Dict[int, float] = {i: 0.0 for i in range(1, 17)}
        bias = bias or {}

        # 1) 基于四柱五行打分
        pillars = []
        if self.bazi:
            pillars = [self.bazi.get('year'), self.bazi.get('month'), self.bazi.get('day'), self.bazi.get('hour')]
        # 若 bazi 不可得，用月份近似季节五行
        if not pillars:
            pillars = [''] * 4

        weights = [1.0, 1.0, 1.5, 1.2]  # 年/月/日/时权重（偏重日主、时）
        for pillar, w in zip(pillars, weights):
            wx = _pillar_wuxing(pillar)
            if wx:
                for n in RED_GROUPS.get(wx, []):
                    red_scores[n] += 1.0 * w
                for n in BLUE_GROUPS.get(wx, []):
                    blue_scores[n] += 1.0 * w

        # 2) 季节/节气加权（近似：用月份）
        wx_season = SEASON_WUXING.get(self.dt.month)
        if wx_season:
            for n in RED_GROUPS.get(wx_season, []):
                red_scores[n] += 0.6
            for n in BLUE_GROUPS.get(wx_season, []):
                blue_scores[n] += 0.6

        # 3) 可选偏置（不同文化模型的差异化权重）
        # bias 形如 {'year': 0.5, 'month': 1.0, 'day': 2.0, 'hour': 1.5, 'season': 0.8}
        # 这里简单乘上总体缩放因子
        if bias:
            factor = max(0.1, float(sum(bias.values()) / max(1, len(bias))))
            for i in red_scores:
                red_scores[i] *= factor
            for i in blue_scores:
                blue_scores[i] *= factor

        return red_scores, blue_scores
