"""
pattern_discovery.py
数据驱动新模式发现引擎
- 特征工程、聚类、关联规则、序列模式挖掘等自动发现全新预测模式
- 可扩展融合AI创新方法
"""
import random
from collections import defaultdict, Counter

class FeatureEngineer:
    """特征工程：生成多维特征"""
    def extract(self, data):
        features = []
        for group in data:
            reds, blue = group
            features.append({
                'sum': sum(reds),
                'max': max(reds),
                'min': min(reds),
                'span': max(reds)-min(reds),
                'even': sum(1 for n in reds if n%2==0),
                'odd': sum(1 for n in reds if n%2==1),
                'blue': blue
            })
        return features

class PatternCluster:
    """聚类分析：发现高相关组合"""
    def cluster(self, features, k=3):
        # 简化为按sum分组
        buckets = defaultdict(list)
        for f in features:
            key = f['sum']//20
            buckets[key].append(f)
        return buckets

class AssociationMiner:
    """关联规则挖掘：发现高频组合"""
    def mine(self, data, min_support=2):
        counter = Counter()
        for reds, blue in data:
            for r in reds:
                counter[r] += 1
        return [n for n, c in counter.items() if c >= min_support]

class SequencePatternMiner:
    """序列模式挖掘：发现递推/周期规律"""
    def mine(self, data):
        # 简化为蓝球周期性分析
        blues = [blue for _, blue in data]
        period = None
        for p in range(2, 10):
            if all(blues[i] == blues[i%p] for i in range(len(blues))):
                period = p
                break
        return period

class NewPatternDiscoveryEngine:
    def __init__(self):
        self.fe = FeatureEngineer()
        self.cluster = PatternCluster()
        self.assoc = AssociationMiner()
        self.seq = SequencePatternMiner()
    def discover(self, data):
        features = self.fe.extract(data)
        clusters = self.cluster.cluster(features)
        associations = self.assoc.mine(data)
        period = self.seq.mine(data)
        return {
            'clusters': clusters,
            'associations': associations,
            'period': period
        }

# 示例用法
def demo():
    # 随机生成历史数据
    data = [(set(random.sample(range(1,34),6)), random.randint(1,16)) for _ in range(100)]
    engine = NewPatternDiscoveryEngine()
    result = engine.discover(data)
    print("[新模式发现引擎] 发现结果：")
    print(f"聚类分布: { {k:len(v) for k,v in result['clusters'].items()} }")
    print(f"高频红球: {result['associations']}")
    print(f"蓝球周期: {result['period']}")

if __name__ == "__main__":
    demo()
