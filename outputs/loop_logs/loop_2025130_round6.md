# 自主循环 Round 6 - 期 2025130

## 生成与选择
- 生成样本数/方法: 1000
- Top10 文件: top10_ssq_2025130.json
- 调优 Top10: tuned_top10_2025130.jsonl
- 最佳权重: {'xiaoliuyao': 0.0, 'xiaoliuren': 0.0, 'qimen': 1.0, 'ziwei': 0.0} (score=11.8)

## 单期回测摘要
- 真实开奖: 红 [10, 12, 13, 15, 20, 26] 蓝 6
- 方法表现:
  - xiaoliuyao: total=1000 blue_hits=35 full_hits=0 red_dist={1: 427, 2: 235, 0: 270, 3: 57, 4: 11}
  - xiaoliuren: total=1000 blue_hits=27 full_hits=0 red_dist={0: 269, 2: 226, 1: 463, 3: 38, 4: 4}
  - qimen: total=1000 blue_hits=76 full_hits=0 red_dist={2: 230, 0: 272, 3: 66, 1: 425, 4: 7}
  - ziwei: total=1000 blue_hits=22 full_hits=0 red_dist={1: 465, 0: 306, 2: 190, 3: 38, 4: 1}
  - ai_fusion: total=1000 blue_hits=47 full_hits=0 red_dist={1: 441, 0: 273, 2: 230, 3: 53, 4: 3}
- Top10 命中: red_dist={1: 6, 0: 3, 2: 1} blue_hits=0

## 元学习注记
- 本轮通过权重调优强化对高覆盖方法的偏好 (若最佳权重集中于某单一方法，说明该方法近期稳定性更高)
- 后续可加入: 强化学习 (多臂老虎机) 动态调整、蓝球独立模型、条件概率建模