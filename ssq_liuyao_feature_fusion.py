"""
六爻推演与开奖特征融合建模脚本
- 自动为每期历史开奖生成六爻卦象特征（简化版：以期号/日期映射）
- 构建融合特征数据集，输出为 CSV
- 可用于后续相关性建模与AI训练
"""
import csv
from datetime import datetime
from bazi_liuyao_auto import liuyao_auto

SSQ_CSV = 'ssq_history.csv'
OUTPUT_CSV = 'ssq_liuyao_features.csv'

# 以期号映射六爻卦象（简化：每期生成固定卦象，实际可扩展为日期/时间推演）
def get_liuyao_for_issue(issue_idx):
    # 可用更复杂算法替换
    base = issue_idx * 7 + 2025
    yao = [(base >> i) % 2 for i in range(6)]
    return yao

def main():
    with open(SSQ_CSV, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['期号'] + [f'红{i}' for i in range(1,7)] + ['蓝'] + [f'六爻{i}' for i in range(1,7)]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, row in enumerate(rows):
            yao = get_liuyao_for_issue(idx)
            out_row = {**row}
            for i in range(6):
                out_row[f'六爻{i+1}'] = yao[i]
            writer.writerow(out_row)
    print(f'融合特征数据集已生成: {OUTPUT_CSV}')

if __name__ == '__main__':
    main()
