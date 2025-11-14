# 自主循环 Round 1 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=37 full_hits=0 red_dist={1: 463, 2: 244, 0: 233, 3: 52, 4: 8}
  - xiaoliuren: total=1000 blue_hits=29 full_hits=0 red_dist={0: 288, 1: 428, 2: 232, 3: 48, 4: 3, 5: 1}
  - qimen: total=1000 blue_hits=68 full_hits=0 red_dist={1: 465, 3: 55, 2: 226, 0: 251, 4: 3}
  - ziwei: total=1000 blue_hits=40 full_hits=0 red_dist={2: 211, 0: 302, 1: 448, 3: 39}
  - ai_fusion: total=1000 blue_hits=42 full_hits=0 red_dist={0: 268, 1: 441, 2: 246, 3: 41, 4: 3, 5: 1}
- Top10 命中: red_dist={1: 4, 2: 3, 0: 3} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模