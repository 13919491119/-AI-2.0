"""
小六壬掌诀权重集成示例
- 读取 liuren_palm_win_prob.json
- 根据当前掌诀动态调整红球权重
- 可在选号逻辑中调用
"""
import json
from core_enums import LiurenPalm

PALM_PROB_JSON = 'liuren_palm_win_prob.json'

class LiurenPalmWeight:
    def __init__(self, json_path=PALM_PROB_JSON):
        with open(json_path, encoding='utf-8') as f:
            self.palm_prob = json.load(f)

    def get_red_weights(self, palm: LiurenPalm):
        """返回当前掌诀下红球权重映射（1~33）"""
        prob_map = self.palm_prob.get(palm.value, {})
        weights = [float(prob_map.get(str(i), 0.0)) for i in range(1, 34)]
        return weights

# 示例用法
if __name__ == '__main__':
    palm = LiurenPalm.DAAN
    w = LiurenPalmWeight()
    weights = w.get_red_weights(palm)
    print(f"{palm.value} 权重: ", weights)
