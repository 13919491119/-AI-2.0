import csv
import random

def generate_history_csv(filename, n=1000, seed=42):
    random.seed(seed)
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['期号','红1','红2','红3','红4','红5','红6','蓝'])
        for i in range(1, n+1):
            reds = sorted(random.sample(range(1,34), 6))
            blue = random.randint(1,16)
            writer.writerow([f'{2023000+i}'] + reds + [blue])

if __name__ == '__main__':
    generate_history_csv('ssq_history.csv', n=5000)
    print('已生成5000期双色球历史数据到ssq_history.csv')
