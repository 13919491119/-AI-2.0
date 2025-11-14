# 自主循环 Round 3 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=39 full_hits=0 red_dist={1: 440, 2: 237, 3: 51, 0: 268, 4: 4}
  - xiaoliuren: total=1000 blue_hits=21 full_hits=0 red_dist={2: 221, 1: 434, 0: 278, 3: 60, 4: 7}
  - qimen: total=1000 blue_hits=58 full_hits=0 red_dist={0: 258, 2: 246, 1: 429, 3: 58, 4: 9}
  - ziwei: total=1000 blue_hits=37 full_hits=0 red_dist={0: 281, 1: 474, 2: 209, 3: 34, 4: 2}
  - ai_fusion: total=1000 blue_hits=40 full_hits=0 red_dist={0: 310, 1: 433, 2: 195, 3: 56, 4: 6}
- Top10 命中: red_dist={2: 2, 1: 5, 0: 3} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模