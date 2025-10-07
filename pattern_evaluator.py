"""
pattern_evaluator.py
- 多维度模式评价算法模块
- 支持创新性、实用性、历史命中率、用户反馈等多维评分
- 可配置权重
"""
import random

def evaluate_pattern(pattern, weights=None):
    """
    多维度综合评分
    pattern: dict, 必须包含 description，可选 history_hit/user_feedback 字段
    weights: dict, 各维度权重
    返回: 综合得分（0-1）
    """
    if weights is None:
        weights = {
            'innovation': 0.4,
            'practical': 0.2,
            'history_hit': 0.2,
            'user_feedback': 0.2
        }
    # 创新性: NLP/LLM自动打分（此处模拟）
    innovation = random.uniform(0.6, 1.0) if '创新' in pattern.get('description', '') else random.uniform(0.3, 0.8)
    # 实用性: 关键字或规则（可扩展）
    practical = 1.0 if '热号' in pattern.get('description', '') else 0.7
    # 历史命中率: 0-1
    history_hit = float(pattern.get('history_hit', 0.5))
    # 用户反馈: 0-1
    user_feedback = float(pattern.get('user_feedback', 0.5))
    score = (
        innovation * weights['innovation'] +
        practical * weights['practical'] +
        history_hit * weights['history_hit'] +
        user_feedback * weights['user_feedback']
    )
    return round(score, 3)
