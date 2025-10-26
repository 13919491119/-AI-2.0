#!/usr/bin/env python3
"""
离线训练深度文化模型并持久化，供线上推理使用。
- 输入：ssq_history.csv
- 输出：models/cultural_deep.joblib
"""
import os
import sys
from cultural_deep_model import CulturalDeepModel
from ssq_data import SSQDataManager


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else 'ssq_history.csv'
    out_path = os.getenv('SSQ_CULDL_PATH', 'models/cultural_deep.joblib')
    dm = SSQDataManager(csv_path=data_path)
    mdl = CulturalDeepModel()
    try:
        win = int(os.getenv('SSQ_CULDL_WINDOW', '5000'))
    except Exception:
        win = 5000
    hist = dm.history[-win:] if win and len(dm.history) > win else dm.history
    ok = mdl.fit(hist)
    if not ok:
        print('[train_cultural_deep] 数据不足或训练失败，已跳过保存（将在线退化为文化评分）。')
        sys.exit(0)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if mdl.save(out_path):
        print(f'[train_cultural_deep] 已保存模型 -> {out_path}')
    else:
        print('[train_cultural_deep] 保存失败。')


if __name__ == '__main__':
    main()
