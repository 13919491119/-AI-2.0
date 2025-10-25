"""
小六壬掌诀与历史开奖分布统计脚本
- 统计每期小六壬掌诀（大安、留连、速喜、赤口、小吉、空亡）出现频率及其与中奖号码的关联
- 生成掌诀-中奖概率映射表（JSON）
- 可集成到选号逻辑中动态调整权重
"""
import csv
import json
from collections import Counter, defaultdict
from core_enums import LiurenPalm

SSQ_CSV = 'ssq_history.csv'
OUTPUT_JSON = 'liuren_palm_win_prob.json'

# 小六壬掌诀推导（按期号映射）
def get_liuren_palm(issue_idx):
    palms = [LiurenPalm.DAAN, LiurenPalm.LIULIAN, LiurenPalm.SUXI, LiurenPalm.CHIKOU, LiurenPalm.XIAOJI, LiurenPalm.KONGWANG]
    return palms[issue_idx % 6]

def main():
    palm_stats = Counter()
    palm_win_stats = defaultdict(lambda: Counter())
    with open(SSQ_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            palm = get_liuren_palm(idx)
            palm_stats[palm.value] += 1
            # 统计红球命中分布
            reds = [int(row[f'红{i}']) for i in range(1, 7)]
            for r in reds:
                palm_win_stats[palm.value][r] += 1
    # 计算每个掌诀下各红球的中奖概率
    palm_prob = {}
    for palm, win_counter in palm_win_stats.items():
        total = palm_stats[palm]
        prob_map = {str(num): cnt / total for num, cnt in win_counter.items()}
        palm_prob[palm] = prob_map
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(palm_prob, f, ensure_ascii=False, indent=2)
    print(f'掌诀-中奖概率映射表已生成: {OUTPUT_JSON}')

if __name__ == '__main__':
    main()
