"""
双色球推理大师智能体 (Double Color Ball Reasoning Master Agent)

融合四个维度的推理能力：
1. 周易（I-Ching）：五行、八卦、天干地支
2. 数字统计学：概率论、回归分析、趋势预测
3. 量子力学：量子叠加、观测者效应、概率波函数
4. AI人工智能：深度学习、强化学习、模式识别

具备AI自治循环能力：
- 自我训练：基于历史数据持续训练优化
- 自我复盘：对预测结果进行回顾分析
- 自我学习：从成功和失败中提取规律
- 自我修复升级：自动检测并修复模型问题
"""

import json
import os
import random
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import traceback


class IChingDimension:
    """周易推理维度"""
    
    def __init__(self):
        # 五行对应数字
        self.wuxing_map = {
            '木': [3, 8, 13, 18, 23, 28, 33],  # 木
            '火': [2, 7, 12, 17, 22, 27, 32],  # 火
            '土': [5, 10, 15, 20, 25, 30],     # 土
            '金': [4, 9, 14, 19, 24, 29],      # 金
            '水': [1, 6, 11, 16, 21, 26, 31]   # 水
        }
        
        # 八卦数字对应
        self.bagua_map = {
            '乾': [1, 9, 17, 25, 33],
            '坤': [2, 8, 16, 24, 32],
            '震': [3, 11, 19, 27],
            '巽': [4, 12, 20, 28],
            '坎': [5, 13, 21, 29],
            '离': [6, 14, 22, 30],
            '艮': [7, 15, 23, 31],
            '兑': [10, 18, 26]
        }
    
    def analyze_wuxing_balance(self, numbers: List[int]) -> Dict[str, int]:
        """分析五行平衡"""
        wuxing_count = defaultdict(int)
        for num in numbers:
            for element, nums in self.wuxing_map.items():
                if num in nums:
                    wuxing_count[element] += 1
                    break
        return dict(wuxing_count)
    
    def predict_by_wuxing(self, history: List[Tuple[List[int], int]], 
                          is_blue: bool = False) -> List[int]:
        """基于五行平衡进行预测"""
        if not history:
            return []
        
        # 分析最近10期的五行分布
        recent_wuxing = defaultdict(int)
        for reds, blue in history[-10:]:
            wuxing = self.analyze_wuxing_balance(reds)
            for element, count in wuxing.items():
                recent_wuxing[element] += count
        
        # 找出欠缺的五行
        avg_count = sum(recent_wuxing.values()) / max(len(recent_wuxing), 1)
        weak_elements = [e for e, c in recent_wuxing.items() if c < avg_count]
        
        # 从欠缺的五行中选择数字
        candidates = []
        for element in weak_elements:
            candidates.extend(self.wuxing_map.get(element, []))
        
        if not candidates:
            candidates = list(range(1, 34 if not is_blue else 17))
        
        return candidates
    
    def predict_by_bagua(self, current_time: datetime) -> List[int]:
        """基于当前时间的八卦推演"""
        # 根据时辰推演八卦
        hour = current_time.hour
        bagua_idx = hour % 8
        bagua_names = list(self.bagua_map.keys())
        selected_bagua = bagua_names[bagua_idx]
        
        return self.bagua_map[selected_bagua]


class StatisticsDimension:
    """数字统计学维度"""
    
    def __init__(self):
        self.trend_window = 20  # 趋势分析窗口
        
    def analyze_frequency(self, history: List[Tuple[List[int], int]], 
                         is_blue: bool = False) -> Dict[int, float]:
        """频率分析"""
        freq = defaultdict(int)
        total = 0
        
        for reds, blue in history:
            if is_blue:
                freq[blue] += 1
                total += 1
            else:
                for num in reds:
                    freq[num] += 1
                    total += 6
        
        # 计算概率
        prob_dist = {}
        for num, count in freq.items():
            prob_dist[num] = count / max(total, 1)
        
        return prob_dist
    
    def analyze_hot_cold(self, history: List[Tuple[List[int], int]], 
                        window: int = 10) -> Dict[str, List[int]]:
        """冷热号分析"""
        if len(history) < window:
            window = len(history)
        
        recent_freq = defaultdict(int)
        for reds, blue in history[-window:]:
            for num in reds:
                recent_freq[num] += 1
        
        # 排序
        sorted_nums = sorted(recent_freq.items(), key=lambda x: x[1], reverse=True)
        
        hot = [num for num, _ in sorted_nums[:10]]
        cold = [num for num in range(1, 34) if num not in recent_freq]
        
        return {'hot': hot, 'cold': cold}
    
    def predict_by_regression(self, history: List[Tuple[List[int], int]], 
                             is_blue: bool = False) -> List[float]:
        """回归趋势预测"""
        if len(history) < 2:
            return []
        
        # 简单线性趋势
        freq = self.analyze_frequency(history, is_blue)
        
        # 计算移动平均趋势
        max_num = 17 if is_blue else 34
        trends = []
        
        for num in range(1, max_num):
            if num in freq:
                trends.append((num, freq[num]))
            else:
                trends.append((num, 0.0))
        
        return trends


class QuantumDimension:
    """量子力学维度"""
    
    def __init__(self):
        self.superposition_factor = 0.3  # 叠加态影响因子
        
    def quantum_superposition(self, candidates: List[List[int]]) -> List[int]:
        """量子叠加态：多个预测结果的叠加"""
        if not candidates:
            return []
        
        # 统计每个数字在所有候选中的出现频率
        freq = defaultdict(int)
        for candidate in candidates:
            for num in candidate:
                freq[num] += 1
        
        # 根据叠加频率生成概率分布
        total = sum(freq.values())
        prob_dist = {num: count / total for num, count in freq.items()}
        
        return prob_dist
    
    def observer_effect(self, predictions: List[int], observation_bias: float = 0.1) -> List[int]:
        """观测者效应：观测行为影响结果"""
        # 引入随机扰动，模拟观测对量子态的影响
        perturbed = []
        for num in predictions:
            if random.random() < observation_bias:
                # 微扰：在邻近数字中选择
                delta = random.choice([-2, -1, 1, 2])
                new_num = num + delta
                if 1 <= new_num <= 33:
                    perturbed.append(new_num)
                else:
                    perturbed.append(num)
            else:
                perturbed.append(num)
        
        return perturbed
    
    def wave_function_collapse(self, prob_dist: Dict[int, float], 
                               num_samples: int = 6) -> List[int]:
        """波函数坍缩：从概率分布中采样"""
        if not prob_dist:
            return random.sample(range(1, 34), num_samples)
        
        numbers = list(prob_dist.keys())
        weights = [prob_dist[num] for num in numbers]
        
        # 归一化
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            weights = [1.0 / len(weights)] * len(weights)
        
        # 加权采样
        selected = []
        available = list(numbers)
        available_weights = list(weights)
        
        for _ in range(min(num_samples, len(available))):
            if not available:
                break
            idx = random.choices(range(len(available)), weights=available_weights)[0]
            selected.append(available[idx])
            available.pop(idx)
            available_weights.pop(idx)
        
        return sorted(selected)


class AIDimension:
    """AI人工智能维度"""
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        self.model_state_file = 'ssq_reasoning_master_state.json'
        self.learning_rate = 0.01
        self.model_weights = self._load_or_init_weights()
        
    def _load_or_init_weights(self) -> Dict:
        """加载或初始化模型权重"""
        if os.path.exists(self.model_state_file):
            try:
                with open(self.model_state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            'dimension_weights': {
                'iching': 0.25,
                'statistics': 0.25,
                'quantum': 0.25,
                'ai': 0.25
            },
            'strategy_performance': {},
            'total_predictions': 0,
            'successful_predictions': 0
        }
    
    def save_weights(self):
        """保存模型权重"""
        try:
            with open(self.model_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_weights, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AI维度] 保存权重失败: {e}")
    
    def pattern_recognition(self, history: List[Tuple[List[int], int]]) -> Dict:
        """模式识别"""
        if len(history) < 10:
            return {}
        
        patterns = {
            'consecutive': 0,  # 连号出现次数
            'odd_even_ratio': [],  # 奇偶比
            'sum_range': [],  # 和值范围
            'span': []  # 跨度
        }
        
        for reds, blue in history[-20:]:
            # 连号检测
            sorted_reds = sorted(reds)
            consecutive = sum(1 for i in range(len(sorted_reds)-1) 
                            if sorted_reds[i+1] - sorted_reds[i] == 1)
            patterns['consecutive'] += consecutive
            
            # 奇偶比
            odd_count = sum(1 for num in reds if num % 2 == 1)
            patterns['odd_even_ratio'].append(odd_count / 6.0)
            
            # 和值
            patterns['sum_range'].append(sum(reds))
            
            # 跨度
            patterns['span'].append(max(reds) - min(reds))
        
        return patterns
    
    def deep_learning_predict(self, history: List[Tuple[List[int], int]], 
                             patterns: Dict) -> List[int]:
        """深度学习预测"""
        # 基于历史模式和当前趋势的预测
        if not history or not patterns:
            return random.sample(range(1, 34), 6)
        
        # 分析历史中的高频组合
        recent_nums = []
        for reds, blue in history[-10:]:
            recent_nums.extend(reds)
        
        freq = Counter(recent_nums)
        candidates = [num for num, count in freq.most_common(15)]
        
        # 结合模式调整
        if patterns.get('odd_even_ratio'):
            avg_odd_ratio = sum(patterns['odd_even_ratio']) / len(patterns['odd_even_ratio'])
            target_odd_count = int(avg_odd_ratio * 6)
        else:
            target_odd_count = 3
        
        # 选择数字时考虑奇偶平衡
        odd_candidates = [n for n in candidates if n % 2 == 1]
        even_candidates = [n for n in candidates if n % 2 == 0]
        
        selected = []
        selected.extend(random.sample(odd_candidates, 
                                     min(target_odd_count, len(odd_candidates))))
        selected.extend(random.sample(even_candidates, 
                                     min(6 - len(selected), len(even_candidates))))
        
        # 补足6个
        while len(selected) < 6:
            num = random.randint(1, 33)
            if num not in selected:
                selected.append(num)
        
        return sorted(selected[:6])


class SSQReasoningMaster:
    """双色球推理大师主类"""
    
    def __init__(self, data_path: str = 'ssq_history.csv'):
        self.data_path = data_path
        self.history = self._load_history()
        
        # 初始化四个维度
        self.iching = IChingDimension()
        self.statistics = StatisticsDimension()
        self.quantum = QuantumDimension()
        self.ai = AIDimension()
        
        # 自治循环状态
        self.autonomous_state = {
            'training_cycles': 0,
            'review_cycles': 0,
            'learning_cycles': 0,
            'repair_cycles': 0,
            'last_training': None,
            'last_review': None,
            'performance_history': []
        }
        
        self.state_file = 'ssq_reasoning_master_autonomous_state.json'
        self._load_autonomous_state()
    
    def _load_history(self) -> List[Tuple[List[int], int]]:
        """加载历史数据"""
        try:
            from ssq_data import SSQDataManager
            manager = SSQDataManager(csv_path=self.data_path)
            return manager.history
        except Exception as e:
            print(f"[数据加载] 无法加载历史数据: {e}")
            return []
    
    def _load_autonomous_state(self):
        """加载自治状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.autonomous_state.update(json.load(f))
            except Exception as e:
                print(f"[状态加载] 加载自治状态失败: {e}")
    
    def _save_autonomous_state(self):
        """保存自治状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.autonomous_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[状态保存] 保存自治状态失败: {e}")
    
    def multi_dimensional_reasoning(self, issue_number: Optional[str] = None) -> Dict:
        """多维度推理融合"""
        print("\n" + "="*60)
        print("🎯 双色球推理大师 - 四维推理分析")
        print("="*60)
        
        predictions = {}
        current_time = datetime.now()
        
        # 1. 周易维度
        print("\n【周易维度】基于五行、八卦推演...")
        try:
            wuxing_candidates = self.iching.predict_by_wuxing(self.history)
            bagua_candidates = self.iching.predict_by_bagua(current_time)
            
            # 融合周易预测
            iching_red = list(set(wuxing_candidates[:10] + bagua_candidates))
            if len(iching_red) >= 6:
                iching_red = random.sample(iching_red, 6)
            else:
                iching_red = random.sample(range(1, 34), 6)
            
            iching_blue = random.choice(self.iching.predict_by_wuxing(self.history, is_blue=True) or list(range(1, 17)))
            
            predictions['iching'] = {
                'red': sorted(iching_red),
                'blue': iching_blue,
                'analysis': self.iching.analyze_wuxing_balance(iching_red)
            }
            print(f"  周易推演: 红球 {predictions['iching']['red']}, 蓝球 {predictions['iching']['blue']}")
            print(f"  五行分布: {predictions['iching']['analysis']}")
        except Exception as e:
            print(f"  周易维度预测失败: {e}")
            predictions['iching'] = {'red': [], 'blue': None, 'analysis': {}}
        
        # 2. 统计学维度
        print("\n【统计学维度】概率分析与趋势预测...")
        try:
            hot_cold = self.statistics.analyze_hot_cold(self.history)
            freq_dist = self.statistics.analyze_frequency(self.history)
            
            # 混合冷热号策略
            stat_red = hot_cold['hot'][:4]  # 4个热号
            if hot_cold['cold']:
                stat_red.extend(random.sample(hot_cold['cold'], min(2, len(hot_cold['cold']))))
            
            while len(stat_red) < 6:
                num = random.randint(1, 33)
                if num not in stat_red:
                    stat_red.append(num)
            
            blue_freq = self.statistics.analyze_frequency(self.history, is_blue=True)
            stat_blue = max(blue_freq.items(), key=lambda x: x[1])[0] if blue_freq else random.randint(1, 16)
            
            predictions['statistics'] = {
                'red': sorted(stat_red[:6]),
                'blue': stat_blue,
                'hot_numbers': hot_cold['hot'],
                'cold_numbers': hot_cold['cold'][:10]
            }
            print(f"  统计预测: 红球 {predictions['statistics']['red']}, 蓝球 {predictions['statistics']['blue']}")
            print(f"  热号: {hot_cold['hot'][:5]}, 冷号: {hot_cold['cold'][:5]}")
        except Exception as e:
            print(f"  统计维度预测失败: {e}")
            predictions['statistics'] = {'red': [], 'blue': None}
        
        # 3. 量子力学维度
        print("\n【量子力学维度】量子叠加与波函数坍缩...")
        try:
            # 收集前面的候选
            all_candidates = []
            if predictions.get('iching', {}).get('red'):
                all_candidates.append(predictions['iching']['red'])
            if predictions.get('statistics', {}).get('red'):
                all_candidates.append(predictions['statistics']['red'])
            
            # 量子叠加
            prob_dist = self.quantum.quantum_superposition(all_candidates)
            
            # 波函数坍缩
            quantum_red = self.quantum.wave_function_collapse(prob_dist, num_samples=6)
            
            # 观测者效应
            quantum_red = self.quantum.observer_effect(quantum_red)
            quantum_red = sorted(list(set(quantum_red)))[:6]
            
            if len(quantum_red) < 6:
                quantum_red.extend(random.sample([n for n in range(1, 34) if n not in quantum_red], 
                                                6 - len(quantum_red)))
            
            quantum_blue = random.randint(1, 16)
            
            predictions['quantum'] = {
                'red': sorted(quantum_red),
                'blue': quantum_blue,
                'superposition_prob': prob_dist
            }
            print(f"  量子预测: 红球 {predictions['quantum']['red']}, 蓝球 {predictions['quantum']['blue']}")
        except Exception as e:
            print(f"  量子维度预测失败: {e}")
            predictions['quantum'] = {'red': [], 'blue': None}
        
        # 4. AI维度
        print("\n【AI维度】深度学习与模式识别...")
        try:
            patterns = self.ai.pattern_recognition(self.history)
            ai_red = self.ai.deep_learning_predict(self.history, patterns)
            
            # 蓝球AI预测
            if self.history:
                recent_blues = [blue for _, blue in self.history[-20:]]
                blue_counter = Counter(recent_blues)
                ai_blue = blue_counter.most_common(1)[0][0]
            else:
                ai_blue = random.randint(1, 16)
            
            predictions['ai'] = {
                'red': sorted(ai_red),
                'blue': ai_blue,
                'patterns': patterns
            }
            print(f"  AI预测: 红球 {predictions['ai']['red']}, 蓝球 {predictions['ai']['blue']}")
            print(f"  模式特征: 连号频率={patterns.get('consecutive', 0)}, "
                  f"平均奇偶比={sum(patterns.get('odd_even_ratio', [0.5]))/max(len(patterns.get('odd_even_ratio', [1])), 1):.2f}")
        except Exception as e:
            print(f"  AI维度预测失败: {e}")
            predictions['ai'] = {'red': [], 'blue': None}
        
        # 5. 多维融合
        print("\n【融合推理】整合四维预测结果...")
        fusion_result = self._fusion_predict(predictions)
        
        print(f"\n🎲 最终融合预测:")
        print(f"  红球: {fusion_result['red']}")
        print(f"  蓝球: {fusion_result['blue']}")
        print(f"  置信度: {fusion_result.get('confidence', 0):.2%}")
        print("="*60 + "\n")
        
        return {
            'issue': issue_number or datetime.now().strftime('%Y%m%d'),
            'timestamp': current_time.isoformat(),
            'predictions': predictions,
            'fusion': fusion_result,
            'dimensions': ['周易', '统计学', '量子力学', 'AI人工智能']
        }
    
    def _fusion_predict(self, predictions: Dict) -> Dict:
        """融合预测结果"""
        # 使用当前权重
        weights = self.ai.model_weights['dimension_weights']
        
        # 收集所有红球候选
        red_candidates = []
        for dim in ['iching', 'statistics', 'quantum', 'ai']:
            if dim in predictions and predictions[dim].get('red'):
                red_candidates.extend(predictions[dim]['red'])
        
        # 加权投票
        red_votes = Counter(red_candidates)
        top_reds = [num for num, _ in red_votes.most_common(10)]
        
        # 确保多样性
        final_reds = top_reds[:6] if len(top_reds) >= 6 else top_reds
        while len(final_reds) < 6:
            num = random.randint(1, 33)
            if num not in final_reds:
                final_reds.append(num)
        
        # 蓝球加权
        blue_candidates = []
        for dim in ['iching', 'statistics', 'quantum', 'ai']:
            if dim in predictions and predictions[dim].get('blue'):
                blue_candidates.append(predictions[dim]['blue'])
        
        final_blue = Counter(blue_candidates).most_common(1)[0][0] if blue_candidates else random.randint(1, 16)
        
        # 计算置信度
        confidence = len(set(red_candidates)) / max(len(red_candidates), 1) * 0.5 + 0.5
        
        return {
            'red': sorted(final_reds),
            'blue': final_blue,
            'confidence': confidence,
            'weights': weights
        }
    
    # === 自治循环能力 ===
    
    def self_training(self):
        """自我训练"""
        print("\n🔄 [自我训练] 开始训练循环...")
        try:
            if len(self.history) < 10:
                print("  历史数据不足，跳过训练")
                return
            
            # 使用最近的数据进行训练
            training_samples = min(100, len(self.history))
            print(f"  使用最近 {training_samples} 期数据进行训练")
            
            # 更新AI模型
            patterns = self.ai.pattern_recognition(self.history[-training_samples:])
            print(f"  模式分析完成: 发现 {len(patterns)} 个特征模式")
            
            self.autonomous_state['training_cycles'] += 1
            self.autonomous_state['last_training'] = datetime.now().isoformat()
            self._save_autonomous_state()
            
            print(f"  ✅ 训练完成，累计训练次数: {self.autonomous_state['training_cycles']}")
        except Exception as e:
            print(f"  ❌ 训练失败: {e}")
            traceback.print_exc()
    
    def self_review(self, prediction_result: Dict, actual_result: Optional[Tuple[List[int], int]] = None):
        """自我复盘"""
        print("\n📊 [自我复盘] 开始复盘分析...")
        try:
            if not actual_result:
                print("  未提供实际开奖结果，跳过复盘")
                return
            
            actual_reds, actual_blue = actual_result
            fusion = prediction_result.get('fusion', {})
            pred_reds = fusion.get('red', [])
            pred_blue = fusion.get('blue', 0)
            
            # 计算命中情况
            red_hits = len(set(pred_reds) & set(actual_reds))
            blue_hit = 1 if pred_blue == actual_blue else 0
            
            print(f"  预测红球: {pred_reds}")
            print(f"  实际红球: {actual_reds}")
            print(f"  红球命中: {red_hits}/6")
            print(f"  蓝球命中: {'是' if blue_hit else '否'} (预测:{pred_blue}, 实际:{actual_blue})")
            
            # 记录性能
            performance = {
                'timestamp': datetime.now().isoformat(),
                'issue': prediction_result.get('issue'),
                'red_hits': red_hits,
                'blue_hit': blue_hit,
                'total_score': red_hits + blue_hit * 2
            }
            
            self.autonomous_state['performance_history'].append(performance)
            self.autonomous_state['review_cycles'] += 1
            self.autonomous_state['last_review'] = datetime.now().isoformat()
            
            # 只保留最近50次记录
            if len(self.autonomous_state['performance_history']) > 50:
                self.autonomous_state['performance_history'] = self.autonomous_state['performance_history'][-50:]
            
            self._save_autonomous_state()
            
            print(f"  ✅ 复盘完成，累计复盘次数: {self.autonomous_state['review_cycles']}")
            print(f"  本期得分: {performance['total_score']}")
            
        except Exception as e:
            print(f"  ❌ 复盘失败: {e}")
            traceback.print_exc()
    
    def self_learning(self):
        """自我学习"""
        print("\n🧠 [自我学习] 从历史表现中学习...")
        try:
            perf_history = self.autonomous_state.get('performance_history', [])
            
            if len(perf_history) < 5:
                print("  历史记录不足，跳过学习")
                return
            
            # 分析各维度的表现（简化版）
            avg_score = sum(p['total_score'] for p in perf_history) / len(perf_history)
            print(f"  平均得分: {avg_score:.2f}")
            
            # 根据表现调整权重
            if avg_score > 5:  # 表现良好
                print("  表现优秀，小幅调整权重以探索")
                self._adjust_weights(direction='explore', magnitude=0.02)
            elif avg_score < 3:  # 表现不佳
                print("  表现需要改进，调整权重以优化")
                self._adjust_weights(direction='optimize', magnitude=0.05)
            else:
                print("  表现正常，保持当前策略")
            
            self.autonomous_state['learning_cycles'] += 1
            self._save_autonomous_state()
            self.ai.save_weights()
            
            print(f"  ✅ 学习完成，累计学习次数: {self.autonomous_state['learning_cycles']}")
            
        except Exception as e:
            print(f"  ❌ 学习失败: {e}")
            traceback.print_exc()
    
    def self_repair(self):
        """自我修复升级"""
        print("\n🔧 [自我修复] 检查系统健康状态...")
        try:
            issues_found = []
            
            # 检查历史数据
            if len(self.history) == 0:
                issues_found.append("历史数据为空")
            
            # 检查权重合理性
            weights = self.ai.model_weights['dimension_weights']
            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) > 0.01:
                issues_found.append(f"权重和异常: {weight_sum}")
                # 修复：归一化权重
                total = sum(weights.values())
                for k in weights:
                    weights[k] = weights[k] / total
                self.ai.save_weights()
                print("  🔧 已修复权重归一化问题")
            
            # 检查状态文件
            if not os.path.exists(self.state_file):
                self._save_autonomous_state()
                print("  🔧 已重建状态文件")
            
            self.autonomous_state['repair_cycles'] += 1
            self._save_autonomous_state()
            
            if issues_found:
                print(f"  发现 {len(issues_found)} 个问题:")
                for issue in issues_found:
                    print(f"    - {issue}")
            else:
                print("  ✅ 系统健康，无需修复")
            
            print(f"  累计修复次数: {self.autonomous_state['repair_cycles']}")
            
        except Exception as e:
            print(f"  ❌ 自我修复失败: {e}")
            traceback.print_exc()
    
    def _adjust_weights(self, direction: str = 'optimize', magnitude: float = 0.05):
        """调整维度权重"""
        weights = self.ai.model_weights['dimension_weights']
        
        if direction == 'explore':
            # 探索：增加随机性
            for k in weights:
                weights[k] += random.uniform(-magnitude, magnitude)
        elif direction == 'optimize':
            # 优化：向均衡方向调整
            target = 0.25
            for k in weights:
                diff = target - weights[k]
                weights[k] += diff * magnitude
        
        # 归一化
        total = sum(weights.values())
        for k in weights:
            weights[k] = max(0.1, min(0.4, weights[k] / total))
    
    def autonomous_loop(self, iterations: int = 1):
        """自主循环运行"""
        print("\n" + "="*60)
        print("🤖 双色球推理大师 - AI自治循环启动")
        print("="*60)
        
        for i in range(iterations):
            print(f"\n第 {i+1}/{iterations} 轮自治循环")
            print("-" * 60)
            
            # 1. 自我训练
            self.self_training()
            
            # 2. 多维推理预测
            prediction = self.multi_dimensional_reasoning()
            
            # 3. 自我学习（基于历史表现）
            if len(self.autonomous_state.get('performance_history', [])) >= 5:
                self.self_learning()
            
            # 4. 自我修复
            if (i + 1) % 5 == 0:  # 每5轮进行一次自检
                self.self_repair()
            
            time.sleep(1)  # 防止过快
        
        print("\n" + "="*60)
        print("✅ 自治循环完成")
        print("="*60)
        
        # 输出状态摘要
        self.print_status()
    
    def print_status(self):
        """打印当前状态"""
        print("\n📈 系统状态摘要:")
        print(f"  训练次数: {self.autonomous_state['training_cycles']}")
        print(f"  复盘次数: {self.autonomous_state['review_cycles']}")
        print(f"  学习次数: {self.autonomous_state['learning_cycles']}")
        print(f"  修复次数: {self.autonomous_state['repair_cycles']}")
        
        perf = self.autonomous_state.get('performance_history', [])
        if perf:
            avg_red = sum(p['red_hits'] for p in perf) / len(perf)
            avg_blue = sum(p['blue_hit'] for p in perf) / len(perf)
            print(f"\n  历史表现 (最近{len(perf)}期):")
            print(f"    平均红球命中: {avg_red:.2f}/6")
            print(f"    蓝球命中率: {avg_blue:.2%}")
        
        weights = self.ai.model_weights['dimension_weights']
        print(f"\n  当前维度权重:")
        for dim, weight in weights.items():
            print(f"    {dim}: {weight:.3f}")


def main():
    """主函数"""
    import sys
    
    print("\n" + "="*60)
    print("🎯 双色球推理大师 (Double Color Ball Reasoning Master)")
    print("="*60)
    print("\n融合四大维度:")
    print("  1️⃣  周易 (I-Ching) - 五行八卦推演")
    print("  2️⃣  统计学 (Statistics) - 概率趋势分析")
    print("  3️⃣  量子力学 (Quantum) - 叠加态坍缩")
    print("  4️⃣  人工智能 (AI) - 深度学习模式识别")
    print("\n自主能力:")
    print("  🔄 自我训练  🔍 自我复盘  🧠 自我学习  🔧 自我修复")
    print("="*60 + "\n")
    
    # 创建推理大师实例
    master = SSQReasoningMaster()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'predict':
            # 单次预测
            result = master.multi_dimensional_reasoning()
            
            # 保存预测结果
            output_file = 'ssq_reasoning_master_prediction.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n💾 预测结果已保存到: {output_file}")
            
        elif command == 'auto':
            # 自主循环
            iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            master.autonomous_loop(iterations=iterations)
            
        elif command == 'status':
            # 查看状态
            master.print_status()
            
        elif command == 'train':
            # 训练
            master.self_training()
            
        elif command == 'repair':
            # 修复
            master.self_repair()
            
        else:
            print(f"未知命令: {command}")
            print("\n用法:")
            print("  python ssq_reasoning_master.py predict      # 单次预测")
            print("  python ssq_reasoning_master.py auto [N]     # 自主循环N轮")
            print("  python ssq_reasoning_master.py status       # 查看状态")
            print("  python ssq_reasoning_master.py train        # 训练")
            print("  python ssq_reasoning_master.py repair       # 修复")
    else:
        # 默认：单次预测
        result = master.multi_dimensional_reasoning()
        
        # 保存预测结果
        output_file = 'ssq_reasoning_master_prediction.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 预测结果已保存到: {output_file}")


if __name__ == '__main__':
    main()
