# 自主循环 Round 2 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=27 full_hits=0 red_dist={1: 431, 2: 230, 0: 285, 3: 50, 4: 4}
  - xiaoliuren: total=1000 blue_hits=36 full_hits=0 red_dist={1: 456, 2: 230, 0: 274, 3: 36, 4: 4}
  - qimen: total=1000 blue_hits=52 full_hits=0 red_dist={2: 251, 0: 238, 1: 444, 3: 65, 4: 2}
  - ziwei: total=1000 blue_hits=28 full_hits=0 red_dist={1: 455, 0: 299, 2: 211, 3: 35}
  - ai_fusion: total=1000 blue_hits=45 full_hits=0 red_dist={1: 430, 0: 276, 2: 240, 3: 52, 4: 2}
- Top10 命中: red_dist={1: 5, 2: 3, 0: 2} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模