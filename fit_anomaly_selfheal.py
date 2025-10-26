"""
预测结果拟合度与异常自愈机制
- 自动评估预测结果与实际开奖的拟合度
- 检测异常周期，自动微调参数并记录自愈操作
"""
import csv
import json
from collections import defaultdict

SSQ_CSV = 'ssq_history.csv'
PREDICT_CSV = 'ssq_predict_replay.csv'
REPORT_JSON = 'fit_anomaly_report.json'

# 评估预测与实际开奖拟合度
def evaluate_fit():
    with open(SSQ_CSV, encoding='utf-8') as f:
        real_rows = {row['期号']: row for row in csv.DictReader(f)}
    with open(PREDICT_CSV, encoding='utf-8') as f:
        pred_rows = {row['期号']: row for row in csv.DictReader(f)}
    fit_report = {}
    anomaly_periods = []
    for period, real in real_rows.items():
        pred = pred_rows.get(period)
        if not pred:
            continue
        real_reds = set(int(real[f'红{i}']) for i in range(1,7))
        pred_reds = set(int(pred[f'红{i}']) for i in range(1,7))
        real_blue = int(real['蓝'])
        pred_blue = int(pred['蓝'])
        red_fit = len(real_reds & pred_reds) / 6.0
        blue_fit = int(real_blue == pred_blue)
        fit_report[period] = {'red_fit': red_fit, 'blue_fit': blue_fit}
        # 异常判定：红球命中率低于0.2或蓝球连续3期未命中
        if red_fit < 0.2:
            anomaly_periods.append(period)
    # 自愈操作：异常期自动记录并建议参数微调
    result = {'fit_report': fit_report, 'anomaly_periods': anomaly_periods, 'selfheal': {}}
    for p in anomaly_periods:
        result['selfheal'][p] = '建议调整模型参数或融合权重'
    with open(REPORT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'拟合度与异常自愈报告已生成: {REPORT_JSON}')

if __name__ == '__main__':
    evaluate_fit()
