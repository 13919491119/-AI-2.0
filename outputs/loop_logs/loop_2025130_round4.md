# 自主循环 Round 4 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=33 full_hits=0 red_dist={0: 281, 2: 228, 1: 440, 3: 44, 4: 7}
  - xiaoliuren: total=1000 blue_hits=30 full_hits=0 red_dist={1: 432, 0: 288, 3: 64, 2: 210, 4: 6}
  - qimen: total=1000 blue_hits=65 full_hits=0 red_dist={0: 252, 2: 227, 1: 448, 3: 70, 4: 3}
  - ziwei: total=1000 blue_hits=27 full_hits=0 red_dist={3: 30, 2: 222, 1: 444, 0: 301, 4: 3}
  - ai_fusion: total=1000 blue_hits=45 full_hits=0 red_dist={2: 229, 3: 56, 0: 278, 1: 430, 4: 7}
- Top10 命中: red_dist={0: 7, 1: 2, 2: 1} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模