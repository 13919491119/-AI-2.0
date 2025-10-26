import math

def analyze_group(reds, blue):
    # 六爻：奇偶均衡性
    odd = [n for n in reds if n % 2 == 1]
    even = [n for n in reds if n % 2 == 0]
    liuyao_score = 1 - abs(len(odd)-len(even))/6
    # 小六壬：跨度
    span = max(reds)-min(reds)
    xiaoliu_score = span/32
    # 奇门遁甲：红球分布分散性
    diff = [reds[i+1]-reds[i] for i in range(5)]
    qimen_score = 1 - (max(diff)-min(diff))/32
    # 综合评分
    score = round((liuyao_score + xiaoliu_score + qimen_score)/3, 3)
    # 文化分析
    analysis = f"六爻(奇偶): 奇{len(odd)} 偶{len(even)}，均衡度{liuyao_score:.2f}\n"
    analysis += f"小六壬(跨度): {span}，跨度得分{xiaoliu_score:.2f}\n"
    analysis += f"奇门遁甲(分布): {diff}，分散度得分{qimen_score:.2f}\n"
    analysis += f"综合评分: {score}"
    return score, analysis

groups = [
    ([5,10,15,20,25,30],10), ([4,9,14,19,24,29],5), ([6,11,16,21,26,31],15),
    ([3,8,13,18,23,28],8), ([7,12,17,22,27,32],12), ([1,8,14,20,26,32],9),
    ([2,9,15,23,28,33],7), ([5,11,18,24,29,33],11), ([4,10,16,22,28,31],6),
    ([3,11,17,25,29,31],14), ([3,8,13,18,23,28],8), ([5,10,15,20,25,30],10),
    ([2,7,12,17,22,27],12), ([4,9,14,19,24,29],9), ([1,6,11,16,21,26],16),
    ([7,12,17,22,27,32],7), ([3,9,15,21,27,33],3), ([6,11,16,21,26,31],11),
    ([8,13,18,23,28,33],13), ([4,10,16,22,28,31],4), ([3,8,15,21,27,32],9),
    ([2,7,14,20,26,31],5), ([4,9,16,22,28,33],11), ([1,8,18,19,22,33],14),
    ([2,3,9,12,28,32],1), ([2,3,8,18,26,30],5), ([2,3,8,18,26,30],5),
    ([1,4,6,19,27,30],7), ([4,5,10,23,24,28],14), ([2,5,18,19,28,32],13),
    ([2,4,7,8,19,31],15)
]

with open('analysis_report.txt','w',encoding='utf-8') as f:
    for idx, (reds, blue) in enumerate(groups,1):
        score, analysis = analyze_group(reds, blue)
        f.write(f"第{idx}组: 红球{reds} 蓝球:{blue}\n{analysis}\n{'-'*40}\n")
print('分析报告已生成：analysis_report.txt')
