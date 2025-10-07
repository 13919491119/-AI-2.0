"""
双色球历史数据采集与管理模块
- 支持本地CSV加载、网络API采集、冷热号分析等
"""
import csv
import random

class SSQDataManager:
    def __init__(self, csv_path=None):
        self.history = []
        self.csv_path = csv_path or 'ssq_history.csv'
        self._load_or_init_history()

    def _load_or_init_history(self):
        import os
        if os.path.exists(self.csv_path):
            self.load_csv(self.csv_path)
        else:
            # 首次创建空文件
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['期号','红1','红2','红3','红4','红5','红6','蓝'])

    def load_csv(self, csv_path):
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # 跳过表头
            for row in reader:
                if len(row) >= 8:
                    reds = [int(x) for x in row[1:7]]
                    blue = int(row[7])
                    self.history.append((reds, blue))

    def fetch_online(self):
        # 占位：可扩展为网络API采集真实数据
        # 这里只做模拟，每次采集都追加并持久化
        import os
        start_idx = len(self.history) + 1
        new_rows = []
        for i in range(100):
            reds = random.sample(range(1,34), 6)
            blue = random.randint(1,16)
            self.history.append((reds, blue))
            new_rows.append([start_idx + i] + reds + [blue])
        # 追加写入csv
        with open(self.csv_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for row in new_rows:
                writer.writerow(row)

    def get_hot_cold(self):
        # 统计红球冷热号
        count = {n:0 for n in range(1,34)}
        for reds, _ in self.history:
            for n in reds:
                count[n] += 1
        hot = sorted(count, key=lambda x: -count[x])[:6]
        cold = sorted(count, key=lambda x: count[x])[:6]
        return hot, cold

    def get_history(self):
        return self.history
