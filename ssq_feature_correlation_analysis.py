"""
历史模式复盘与反馈模块
- 自动分析融合特征数据集（ssq_liuyao_features.csv）
- 统计六爻特征与红球/蓝球中奖相关性
- 输出相关性报告与建议，便于动态调整算法权重
"""
import csv
from collections import Counter, defaultdict

FEATURE_CSV = 'ssq_liuyao_features.csv'
REPORT_TXT = 'ssq_feature_correlation_report.txt'

# 统计六爻特征与红球命中相关性
def analyze_feature_correlation():
    with open(FEATURE_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    yao_stats = [defaultdict(int) for _ in range(6)]
    red_stats = [defaultdict(int) for _ in range(6)]
    for row in rows:
        reds = [int(row[f'红{i}']) for i in range(1,7)]
        for i in range(6):
            yao_val = int(row[f'六爻{i+1}'])
            yao_stats[i][yao_val] += 1
            red_stats[i][yao_val] += sum(1 for r in reds if r % 2 == yao_val)
    # 相关性分析：统计每个六爻位的阴阳与红球奇偶分布的命中率
    report_lines = []
    for i in range(6):
        total = sum(yao_stats[i].values())
        line = f'六爻{i+1}：'
        for val in [0,1]:
            hit = red_stats[i][val]
            count = yao_stats[i][val]
            rate = hit / count if count else 0.0
            line += f' 阴阳{val} 命中率={rate:.3f} ({hit}/{count})'
        report_lines.append(line)
    with open(REPORT_TXT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f'相关性报告已生成: {REPORT_TXT}')

if __name__ == '__main__':
    analyze_feature_correlation()
