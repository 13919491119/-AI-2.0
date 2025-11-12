# 自主循环 Round 1 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=26 full_hits=0 red_dist={1: 429, 0: 270, 2: 240, 3: 57, 4: 4}
  - xiaoliuren: total=1000 blue_hits=34 full_hits=0 red_dist={2: 210, 0: 271, 1: 466, 3: 49, 4: 4}
  - qimen: total=1000 blue_hits=74 full_hits=0 red_dist={0: 239, 2: 265, 1: 417, 3: 71, 4: 8}
  - ziwei: total=1000 blue_hits=32 full_hits=0 red_dist={1: 428, 2: 226, 0: 316, 3: 29, 4: 1}
  - ai_fusion: total=1000 blue_hits=53 full_hits=0 red_dist={1: 423, 2: 244, 3: 37, 0: 292, 4: 4}
- Top10 命中: red_dist={0: 5, 1: 4, 2: 1} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模