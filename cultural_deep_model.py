"""
深度学习文化模型（轻量版）
- 目标：学习从多文化视角与周期特征到红/蓝号码分布的映射
- 实现：使用 scikit-learn 的多输出 MLPRegressor 进行回归，输出可解释为概率分数

注意：为保证鲁棒性与轻量，本模型在历史数据不足时会回退到简单的文化打分或随机输出。
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import os
import math
import random

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.multioutput import MultiOutputRegressor
from joblib import dump, load

from cultural_predictor import CulturalPredictor


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


class CulturalDeepModel:
    def __init__(self):
        # 两个多输出回归器：红(33维)、蓝(16维)
        base = MLPRegressor(hidden_layer_sizes=(64,), activation='relu', solver='adam',
                            learning_rate='adaptive', max_iter=200, random_state=42, early_stopping=True)
        self.red_model = MultiOutputRegressor(base)
        base2 = MLPRegressor(hidden_layer_sizes=(64,), activation='relu', solver='adam',
                             learning_rate='adaptive', max_iter=200, random_state=43, early_stopping=True)
        self.blue_model = MultiOutputRegressor(base2)
        self._fitted = False
        self._mu = None
        self._std = None
        # 训练期间的“衰减冷热”状态，用于在线推理复用
        self._hot_red_last: Optional[List[float]] = None
        self._hot_blue_last: Optional[List[float]] = None

    def _features_for_issue(self, issue_idx: int, hot_red: Optional[np.ndarray] = None, hot_blue: Optional[np.ndarray] = None) -> np.ndarray:
        """构造一条样本的特征向量。
        - 多文化视角（六爻/六壬/奇门）的红/蓝分组（五行）总分
        - 周期性编码：issue_idx 在若干周期下的 sin/cos
        """
        profiles = [
            ('liuyao', {'hour': 1.6, 'day': 1.2}),
            ('liuren', {'month': 1.5, 'day': 1.3}),
            ('qimen', {'season': 1.5, 'day': 1.2}),
        ]
        feats: List[float] = []
        # 聚合五行分组分数
        for _name, bias in profiles:
            rs, bs = CulturalPredictor().scores(bias=bias)
            # 红分 1..33 -> 五行组的总分粗聚合
            groups = {
                'wood': sum(rs.get(i, 0.0) for i in [1, 6, 11, 16, 21, 26, 31]),
                'fire': sum(rs.get(i, 0.0) for i in [2, 7, 12, 17, 22, 27, 32]),
                'earth': sum(rs.get(i, 0.0) for i in [3, 8, 13, 18, 23, 28, 33]),
                'metal': sum(rs.get(i, 0.0) for i in [4, 9, 14, 19, 24, 29]),
                'water': sum(rs.get(i, 0.0) for i in [5, 10, 15, 20, 25, 30]),
            }
            b_groups = {
                'wood': sum(bs.get(i, 0.0) for i in [1, 6, 11, 16]),
                'fire': sum(bs.get(i, 0.0) for i in [2, 7, 12]),
                'earth': sum(bs.get(i, 0.0) for i in [3, 8, 13]),
                'metal': sum(bs.get(i, 0.0) for i in [4, 9, 14]),
                'water': sum(bs.get(i, 0.0) for i in [5, 10, 15]),
            }
            feats.extend([
                groups['wood'], groups['fire'], groups['earth'], groups['metal'], groups['water'],
                b_groups['wood'], b_groups['fire'], b_groups['earth'], b_groups['metal'], b_groups['water'],
            ])
        # 周期性编码：模拟多尺度节律（周/月/季度/年等）
        periods = [5, 7, 9, 10, 12, 27, 54]
        for p in periods:
            angle = 2.0 * math.pi * (issue_idx % p) / float(p)
            feats.append(math.sin(angle))
            feats.append(math.cos(angle))
        # 结构性特征（来自历史上一期）：连号长度、最大间距、奇偶比例
        try:
            if issue_idx > 0:
                prev_reds, prev_blue = self._history[issue_idx - 1]  # type: ignore[attr-defined]
                pr = sorted(prev_reds)
                # 连号长度
                run = 1
                best = 1
                for i in range(1, len(pr)):
                    if pr[i] == pr[i-1] + 1:
                        run += 1
                        best = max(best, run)
                    else:
                        run = 1
                feats.append(float(best))
                # 最大间距
                gaps = [pr[i] - pr[i-1] for i in range(1, len(pr))]
                feats.append(float(max(gaps) if gaps else 0))
                # 奇偶比例
                odds = sum(1 for x in pr if x % 2 == 1)
                feats.append(float(odds) / 6.0)
            else:
                feats.extend([0.0, 0.0, 0.0])
        except Exception:
            feats.extend([0.0, 0.0, 0.0])
        # 补充衰减冷热概率特征（红33、蓝16）
        if hot_red is not None and hot_blue is not None:
            feats.extend(hot_red.tolist())
            feats.extend(hot_blue.tolist())
        else:
            # 若无提供，使用训练末状态（预测时）
            if isinstance(self._hot_red_last, list) and isinstance(self._hot_blue_last, list):
                feats.extend(self._hot_red_last)
                feats.extend(self._hot_blue_last)
            else:
                feats.extend([0.0] * 33)
                feats.extend([0.0] * 16)
        return np.asarray(feats, dtype=float)

    def _build_dataset(self, history: List[Tuple[List[int], int]]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        X: List[np.ndarray] = []
        Y_red: List[np.ndarray] = []  # 33维0/1
        Y_blue: List[np.ndarray] = []  # 16维0/1
        # 使用指数衰减的冷热统计作为时变特征
        decay = float(os.getenv('SSQ_CULDL_DECAY', '0.995')) if 'SSQ_CULDL_DECAY' in os.environ else 0.995
        hot_r = np.zeros((33,), dtype=float)
        hot_b = np.zeros((16,), dtype=float)
    # 存下历史供结构性特征使用
        self._history = history  # type: ignore[attr-defined]
        for idx, (reds, blue) in enumerate(history):
            # 归一化衰减概率（作为当前样本的冷热特征）
            hr = hot_r / max(1e-9, hot_r.sum()) if hot_r.sum() > 0 else hot_r
            hb = hot_b / max(1e-9, hot_b.sum()) if hot_b.sum() > 0 else hot_b
            x = self._features_for_issue(idx, hr, hb)
            y_r = np.zeros((33,), dtype=float)
            for r in set(reds):
                if 1 <= r <= 33:
                    y_r[r-1] = 1.0
            y_b = np.zeros((16,), dtype=float)
            if 1 <= int(blue) <= 16:
                y_b[int(blue)-1] = 1.0
            X.append(x)
            Y_red.append(y_r)
            Y_blue.append(y_b)
            # 更新衰减冷热计数（先衰减再叠加当前）
            if decay < 1.0:
                hot_r *= decay
                hot_b *= decay
            for r in reds:
                if 1 <= r <= 33:
                    hot_r[r-1] += 1.0
            if 1 <= int(blue) <= 16:
                hot_b[int(blue)-1] += 1.0
        if not X:
            return np.zeros((0, 10)), np.zeros((0, 33)), np.zeros((0, 16))
        Xn = np.vstack(X)
        Yr = np.vstack(Y_red)
        Yb = np.vstack(Y_blue)
        # 保存训练末状态（用于在线预测）
        hr_last = hot_r / max(1e-9, hot_r.sum()) if hot_r.sum() > 0 else hot_r
        hb_last = hot_b / max(1e-9, hot_b.sum()) if hot_b.sum() > 0 else hot_b
        self._hot_red_last = hr_last.tolist()
        self._hot_blue_last = hb_last.tolist()
        return Xn, Yr, Yb

    def fit(self, history: List[Tuple[List[int], int]]) -> bool:
        try:
            X, Yr, Yb = self._build_dataset(history)
            # 数据太少就放弃训练
            if X.shape[0] < 50:
                self._fitted = False
                return False
            # 简单标准化
            mu = X.mean(axis=0)
            std = X.std(axis=0)
            std[std < 1e-6] = 1.0
            Xs = (X - mu) / std
            self._mu = mu
            self._std = std
            self.red_model.fit(Xs, Yr)
            self.blue_model.fit(Xs, Yb)
            self._fitted = True
            return True
        except Exception:
            self._fitted = False
            return False

    def save(self, path: str) -> bool:
        try:
            payload = {
                'mu': self._mu,
                'std': self._std,
                'red': self.red_model,
                'blue': self.blue_model,
                'fitted': self._fitted,
                'hot_red_last': self._hot_red_last,
                'hot_blue_last': self._hot_blue_last,
            }
            dump(payload, path)
            return True
        except Exception:
            return False

    @staticmethod
    def load(path: str) -> Optional['CulturalDeepModel']:
        try:
            obj = load(path)
            mdl = CulturalDeepModel()
            mdl._mu = obj.get('mu')
            mdl._std = obj.get('std')
            mdl.red_model = obj.get('red')
            mdl.blue_model = obj.get('blue')
            mdl._fitted = bool(obj.get('fitted', False))
            mdl._hot_red_last = obj.get('hot_red_last')
            mdl._hot_blue_last = obj.get('hot_blue_last')
            return mdl
        except Exception:
            return None

    def predict_distributions(self, issue_idx: int) -> Tuple[List[float], List[float]]:
        """返回红33维与蓝16维的概率分布（和为1）。若未训练成功则基于文化分数退化。"""
        x = self._features_for_issue(issue_idx)
        if getattr(self, '_fitted', False):
            try:
                xs = (x - self._mu) / self._std
                red_raw = np.asarray(self.red_model.predict(xs.reshape(1, -1))[0])
                blue_raw = np.asarray(self.blue_model.predict(xs.reshape(1, -1))[0])
                red_p = _sigmoid(red_raw)
                blue_p = _sigmoid(blue_raw)
                red_p = red_p / max(1e-9, red_p.sum())
                blue_p = blue_p / max(1e-9, blue_p.sum())
                return red_p.tolist(), blue_p.tolist()
            except Exception:
                pass
        # 退化：使用文化评分归一化
        rs, bs = CulturalPredictor().scores(bias={'hour': 1.6, 'day': 1.2})
        red_arr = np.array([max(0.0, float(rs.get(i, 0.0))) for i in range(1,34)], dtype=float)
        blue_arr = np.array([max(0.0, float(bs.get(i, 0.0))) for i in range(1,17)], dtype=float)
        red_sum = red_arr.sum() or 1.0
        blue_sum = blue_arr.sum() or 1.0
        return (red_arr / red_sum).tolist(), (blue_arr / blue_sum).tolist()

    def predict_numbers(self, issue_idx: int, k_reds: int = 6) -> Tuple[List[int], int]:
        red_p, blue_p = self.predict_distributions(issue_idx)
        # 无放回按概率抽样红球
        reds: List[int] = []
        pool = list(range(1,34))
        probs = red_p[:]
        for _ in range(max(1, min(6, k_reds))):
            if not pool:
                break
            # 归一化
            s = sum(probs) or 1.0
            norm = [p/s for p in probs]
            choice = random.choices(pool, weights=norm, k=1)[0]
            idx = pool.index(choice)
            pool.pop(idx)
            probs.pop(idx)
            reds.append(choice)
        # 蓝球一次抽样
        s = sum(blue_p) or 1.0
        blue = random.choices(list(range(1,17)), weights=[p/s for p in blue_p], k=1)[0]
        return sorted(reds), int(blue)
