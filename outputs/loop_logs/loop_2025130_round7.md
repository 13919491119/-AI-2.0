# 自主循环 Round 7 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=32 full_hits=0 red_dist={2: 255, 0: 268, 1: 412, 3: 58, 4: 7}
  - xiaoliuren: total=1000 blue_hits=39 full_hits=0 red_dist={0: 299, 1: 420, 3: 48, 2: 231, 4: 2}
  - qimen: total=1000 blue_hits=73 full_hits=0 red_dist={1: 438, 2: 228, 3: 68, 0: 261, 4: 5}
  - ziwei: total=1000 blue_hits=50 full_hits=0 red_dist={1: 474, 0: 288, 2: 208, 3: 28, 4: 2}
  - ai_fusion: total=1000 blue_hits=41 full_hits=0 red_dist={2: 229, 1: 429, 0: 293, 3: 46, 4: 3}
- Top10 命中: red_dist={0: 3, 1: 6, 2: 1} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模