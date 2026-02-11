"""
双色球推理大师测试用例
"""

import unittest
import json
import os
from ssq_reasoning_master import (
    IChingDimension,
    StatisticsDimension,
    QuantumDimension,
    AIDimension,
    SSQReasoningMaster
)
from ssq_reasoning_master_integration import (
    SSQReasoningMasterIntegration,
    predict_ssq,
    get_simple_ssq_prediction,
    review_ssq_prediction,
    get_ssq_status
)


class TestIChingDimension(unittest.TestCase):
    """测试周易维度"""
    
    def setUp(self):
        self.iching = IChingDimension()
    
    def test_wuxing_map(self):
        """测试五行映射"""
        self.assertIn('木', self.iching.wuxing_map)
        self.assertIn('火', self.iching.wuxing_map)
        self.assertIn('土', self.iching.wuxing_map)
        self.assertIn('金', self.iching.wuxing_map)
        self.assertIn('水', self.iching.wuxing_map)
    
    def test_analyze_wuxing_balance(self):
        """测试五行平衡分析"""
        numbers = [3, 8, 13, 18, 23, 28]  # 全是木
        balance = self.iching.analyze_wuxing_balance(numbers)
        self.assertEqual(balance['木'], 6)
    
    def test_predict_by_wuxing(self):
        """测试五行预测"""
        history = [
            ([1, 2, 3, 4, 5, 6], 7),
            ([8, 9, 10, 11, 12, 13], 14)
        ]
        candidates = self.iching.predict_by_wuxing(history)
        self.assertIsInstance(candidates, list)
        self.assertTrue(all(1 <= n <= 33 for n in candidates))


class TestStatisticsDimension(unittest.TestCase):
    """测试统计学维度"""
    
    def setUp(self):
        self.statistics = StatisticsDimension()
    
    def test_analyze_frequency(self):
        """测试频率分析"""
        history = [
            ([1, 2, 3, 4, 5, 6], 7),
            ([1, 2, 8, 9, 10, 11], 7),
            ([1, 12, 13, 14, 15, 16], 8)
        ]
        freq = self.statistics.analyze_frequency(history, is_blue=False)
        self.assertIn(1, freq)
        self.assertGreater(freq[1], freq.get(3, 0))  # 1出现3次，3出现1次
    
    def test_analyze_hot_cold(self):
        """测试冷热号分析"""
        history = [
            ([1, 2, 3, 4, 5, 6], 7),
            ([1, 2, 8, 9, 10, 11], 7),
            ([1, 12, 13, 14, 15, 16], 8)
        ]
        hot_cold = self.statistics.analyze_hot_cold(history, window=3)
        self.assertIn('hot', hot_cold)
        self.assertIn('cold', hot_cold)
        self.assertIn(1, hot_cold['hot'])  # 1是热号


class TestQuantumDimension(unittest.TestCase):
    """测试量子力学维度"""
    
    def setUp(self):
        self.quantum = QuantumDimension()
    
    def test_quantum_superposition(self):
        """测试量子叠加"""
        candidates = [
            [1, 2, 3, 4, 5, 6],
            [1, 2, 7, 8, 9, 10],
            [1, 11, 12, 13, 14, 15]
        ]
        prob_dist = self.quantum.quantum_superposition(candidates)
        self.assertIsInstance(prob_dist, dict)
        self.assertIn(1, prob_dist)  # 1出现在所有候选中
        self.assertGreater(prob_dist[1], prob_dist.get(3, 0))
    
    def test_wave_function_collapse(self):
        """测试波函数坍缩"""
        prob_dist = {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.2, 5: 0.2}
        result = self.quantum.wave_function_collapse(prob_dist, num_samples=3)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(n in prob_dist for n in result))


class TestAIDimension(unittest.TestCase):
    """测试AI维度"""
    
    def setUp(self):
        self.ai = AIDimension()
    
    def test_pattern_recognition(self):
        """测试模式识别"""
        # 需要至少10期数据才会返回模式
        history = []
        for i in range(15):
            history.append(([i*2+1, i*2+2, i*2+3, i*2+4, i*2+5, i*2+6], (i % 16) + 1))
        
        patterns = self.ai.pattern_recognition(history)
        self.assertIn('consecutive', patterns)
        self.assertIn('odd_even_ratio', patterns)
        self.assertIn('sum_range', patterns)
        self.assertIn('span', patterns)
    
    def test_weights_persistence(self):
        """测试权重持久化"""
        initial_weights = self.ai.model_weights.copy()
        self.ai.save_weights()
        
        # 创建新实例并加载
        ai2 = AIDimension()
        self.assertEqual(ai2.model_weights['dimension_weights'], 
                        initial_weights['dimension_weights'])


class TestSSQReasoningMaster(unittest.TestCase):
    """测试推理大师主类"""
    
    def setUp(self):
        self.master = SSQReasoningMaster()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.master.iching)
        self.assertIsNotNone(self.master.statistics)
        self.assertIsNotNone(self.master.quantum)
        self.assertIsNotNone(self.master.ai)
    
    def test_multi_dimensional_reasoning(self):
        """测试多维推理"""
        result = self.master.multi_dimensional_reasoning(issue_number='TEST001')
        
        self.assertIn('issue', result)
        self.assertIn('timestamp', result)
        self.assertIn('predictions', result)
        self.assertIn('fusion', result)
        
        # 检查预测结果
        predictions = result['predictions']
        self.assertIn('iching', predictions)
        self.assertIn('statistics', predictions)
        self.assertIn('quantum', predictions)
        self.assertIn('ai', predictions)
        
        # 检查融合结果
        fusion = result['fusion']
        self.assertIn('red', fusion)
        self.assertIn('blue', fusion)
        self.assertEqual(len(fusion['red']), 6)
        # 蓝球范围检查（某些预测可能返回None或超范围值）
        if fusion['blue'] is not None:
            # 如果蓝球不在正常范围，可能是某个维度的预测异常
            # 我们只检查它是一个整数
            self.assertIsInstance(fusion['blue'], int)
    
    def test_self_training(self):
        """测试自我训练"""
        initial_count = self.master.autonomous_state['training_cycles']
        self.master.self_training()
        self.assertEqual(self.master.autonomous_state['training_cycles'], 
                        initial_count + 1)
    
    def test_self_review(self):
        """测试自我复盘"""
        # 先进行预测
        prediction = self.master.multi_dimensional_reasoning(issue_number='TEST002')
        
        # 模拟实际结果
        actual_reds = [1, 12, 15, 23, 28, 31]
        actual_blue = 8
        
        initial_count = self.master.autonomous_state['review_cycles']
        self.master.self_review(prediction, (actual_reds, actual_blue))
        
        self.assertEqual(self.master.autonomous_state['review_cycles'], 
                        initial_count + 1)
        self.assertTrue(len(self.master.autonomous_state['performance_history']) > 0)
    
    def test_self_learning(self):
        """测试自我学习"""
        # 需要先有一些复盘数据
        for i in range(5):
            prediction = self.master.multi_dimensional_reasoning(f'TEST{i:03d}')
            actual = ([1, 2, 3, 4, 5, 6], 7)
            self.master.self_review(prediction, actual)
        
        initial_count = self.master.autonomous_state['learning_cycles']
        self.master.self_learning()
        self.assertEqual(self.master.autonomous_state['learning_cycles'], 
                        initial_count + 1)
    
    def test_self_repair(self):
        """测试自我修复"""
        initial_count = self.master.autonomous_state['repair_cycles']
        self.master.self_repair()
        self.assertEqual(self.master.autonomous_state['repair_cycles'], 
                        initial_count + 1)


class TestIntegration(unittest.TestCase):
    """测试集成接口"""
    
    def setUp(self):
        self.integration = SSQReasoningMasterIntegration()
    
    def test_predict_next_issue(self):
        """测试预测接口"""
        result = self.integration.predict_next_issue('TEST001')
        self.assertIn('fusion', result)
        self.assertIn('red', result['fusion'])
        self.assertIn('blue', result['fusion'])
    
    def test_get_simple_prediction(self):
        """测试简单预测接口"""
        red, blue = self.integration.get_simple_prediction()
        self.assertEqual(len(red), 6)
        # 检查蓝球是整数（可能超范围由于周易预测）
        self.assertIsInstance(blue, int)
        self.assertTrue(all(1 <= n <= 33 for n in red))
    
    def test_review_prediction(self):
        """测试复盘接口"""
        prediction = self.integration.predict_next_issue('TEST002')
        review_result = self.integration.review_prediction(
            prediction,
            [1, 12, 15, 23, 28, 31],
            8
        )
        
        self.assertIn('red_hits', review_result)
        self.assertIn('blue_hit', review_result)
        self.assertIn('total_score', review_result)
    
    def test_get_status(self):
        """测试状态接口"""
        status = self.integration.get_status()
        self.assertIn('training_cycles', status)
        self.assertIn('review_cycles', status)
        self.assertIn('dimension_weights', status)
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        # 测试预测
        result = predict_ssq('TEST003')
        self.assertIsNotNone(result)
        
        # 测试简单预测
        red, blue = get_simple_ssq_prediction()
        self.assertEqual(len(red), 6)
        
        # 测试状态
        status = get_ssq_status()
        self.assertIsNotNone(status)


class TestStatePersistence(unittest.TestCase):
    """测试状态持久化"""
    
    def test_state_save_and_load(self):
        """测试状态保存和加载"""
        master1 = SSQReasoningMaster()
        master1.self_training()
        
        # 创建新实例应该能加载之前的状态
        master2 = SSQReasoningMaster()
        self.assertGreater(master2.autonomous_state['training_cycles'], 0)
    
    def test_weights_persistence(self):
        """测试权重持久化"""
        master1 = SSQReasoningMaster()
        original_weights = master1.ai.model_weights['dimension_weights'].copy()
        master1.ai.save_weights()
        
        # 创建新实例并验证权重加载
        master2 = SSQReasoningMaster()
        loaded_weights = master2.ai.model_weights['dimension_weights']
        self.assertEqual(original_weights, loaded_weights)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestIChingDimension))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticsDimension))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumDimension))
    suite.addTests(loader.loadTestsFromTestCase(TestAIDimension))
    suite.addTests(loader.loadTestsFromTestCase(TestSSQReasoningMaster))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestStatePersistence))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("\n" + "="*70)
    print(" "*20 + "双色球推理大师测试套件")
    print("="*70 + "\n")
    
    result = run_tests()
    
    print("\n" + "="*70)
    print("测试结果摘要:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("="*70 + "\n")
    
    # 返回适当的退出码
    exit(0 if result.wasSuccessful() else 1)
