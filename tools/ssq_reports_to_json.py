"""
批量将/reports/双色球文件所有期号数据追加到ssq_history_data.json，自动去重、标准化。
"""
import json
from pathlib import Path

REPORT_PATH = Path("reports/双色球")
JSON_PATH = Path("ssq_history_data.json")

def parse_report_line(line):
    parts = line.strip().split('\t')
    if len(parts) < 5 or not parts[0].isdigit():
        return None
    period = parts[0]
    date = parts[1]
    reds = [int(x) for x in parts[3].split(',')]
    blue = int(parts[4])
    full_code = f"{' '.join(f'{x:02d}' for x in reds)} + {blue:02d}"
    return {
        "period": period,
        "date": date,
        "red_balls": reds,
        "blue_ball": blue,
        "full_code": full_code
    }

def main():
    # 读取已有json
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    existing_periods = {d['period'] for d in data}
    # 读取报告文件
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_items = []
    for line in lines:
        item = parse_report_line(line)
        if item and item['period'] not in existing_periods:
            new_items.append(item)
    if new_items:
        data.extend(new_items)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已追加 {len(new_items)} 条新数据到 {JSON_PATH}")
    else:
        print("无新增数据，无需更新。")

if __name__ == "__main__":
    main()
