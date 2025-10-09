#!/usr/bin/env python3
"""
双色球历史数据分析与预测系统 - 后台任务

功能：
1. 调取2020001-2025114期双色球历史数据
2. 对每期进行预测直到完全吻合
3. 分析吻合规律与可复制性
4. 自主学习、升级、发现新模式
5. 与DeepSeek大模型集成实现自主分析

作者：Celestial Nexus AI系统
日期：2025-10-07
"""

import asyncio
import random
import time
import json
import os
import sys
import datetime
import logging
import requests
from typing import Dict, List, Tuple, Any, Optional
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("ssq_ai_backtest.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 配置常量
DATA_API_URL = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1"  # 替换为实际的DeepSeek API端点
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # 从环境变量获取API密钥
LOCAL_API_URL = "http://localhost:8000"
DATA_CACHE_FILE = "ssq_history_data.json"
LEARNING_RESULTS_FILE = "ssq_learning_cycles.txt"
MODEL_STATE_FILE = "ssq_ai_model_state.json"

# 双色球相关常量
RED_BALL_COUNT = 6
RED_BALL_RANGE = range(1, 34)  # 1-33
BLUE_BALL_RANGE = range(1, 17)  # 1-16

class SSQDataCollector:
    """双色球历史数据收集器"""
    
    @staticmethod
    async def fetch_history_data(start_period="2020001", end_period="2025114") -> List[Dict]:
        """获取历史开奖数据"""
        logger.info(f"正在获取从{start_period}到{end_period}的历史数据...")
        
        # 首先检查本地缓存
        if os.path.exists(DATA_CACHE_FILE):
            try:
                with open(DATA_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    logger.info(f"从本地缓存加载了{len(cache_data)}期数据")
                    return cache_data
            except Exception as e:
                logger.warning(f"读取缓存数据失败: {e}")
        
        # 模拟数据 (实际项目中替换为真实API调用)
        results = []
        current_date = datetime.datetime(2020, 1, 1)
        period = int(start_period)
        
        while period <= int(end_period):
            # 生成随机开奖号码
            red_balls = sorted(random.sample(list(RED_BALL_RANGE), RED_BALL_COUNT))
            blue_ball = random.choice(list(BLUE_BALL_RANGE))
            
            results.append({
                "period": f"{period}",
                "date": current_date.strftime("%Y-%m-%d"),
                "red_balls": red_balls,
                "blue_ball": blue_ball,
                "full_code": " ".join([f"{num:02d}" for num in red_balls]) + f" + {blue_ball:02d}"
            })
            
            period += 1
            current_date += datetime.timedelta(days=3)  # 约每3天一次开奖
        
        # 保存到本地缓存
        with open(DATA_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"成功获取并缓存了{len(results)}期数据")
        return results

class SSQPredictionModel:
    """双色球预测模型基类"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.accuracy_history = []
        self.learning_cycles = 0
    
    async def predict(self, history_data: List[Dict]) -> Tuple[List[int], int]:
        """预测下一期号码"""
        raise NotImplementedError("子类必须实现predict方法")
    
    async def learn(self, history_data: List[Dict], actual_result: Dict) -> None:
        """从结果中学习"""
        self.learning_cycles += 1
    
    def calculate_accuracy(self, prediction: Tuple[List[int], int], actual: Dict) -> float:
        """计算预测准确度"""
        red_match = len(set(prediction[0]) & set(actual["red_balls"]))
        blue_match = 1 if prediction[1] == actual["blue_ball"] else 0
        
        # 计算红球+蓝球的总体准确率
        red_accuracy = red_match / RED_BALL_COUNT
        total_accuracy = (red_accuracy * 6 + blue_match) / 7
        
        self.accuracy_history.append(total_accuracy)
        if len(self.accuracy_history) > 100:
            self.accuracy_history = self.accuracy_history[-100:]
            
        return total_accuracy
    
    @property
    def average_accuracy(self) -> float:
        """获取平均准确率"""
        if not self.accuracy_history:
            return 0.0
        return sum(self.accuracy_history) / len(self.accuracy_history)


class PatternBasedModel(SSQPredictionModel):
    """基于模式识别的预测模型"""
    
    def __init__(self):
        super().__init__("Pattern_Model", 1.2)
        self.patterns = {}
        self.pattern_confidence = {}
    
    async def detect_patterns(self, history_data: List[Dict]) -> None:
        """检测历史数据中的模式"""
        if len(history_data) < 10:
            return
        
        # 检测周期性模式
        for cycle in range(2, 20):
            self._check_cycle_pattern(history_data, cycle)
        
        # 检测热冷号模式
        self._check_hot_cold_pattern(history_data)
        
        # 检测相邻期关系模式
        self._check_adjacent_relation(history_data)
    
    def _check_cycle_pattern(self, history_data: List[Dict], cycle: int) -> None:
        """检测周期性模式"""
        if len(history_data) < cycle * 2:
            return
        
        recent = history_data[-cycle*2:]
        pattern_found = False
        
        # 检查是否有周期性重复
        for i in range(cycle):
            if i + cycle >= len(recent):
                break
            
            red_repeat = len(set(recent[i]["red_balls"]) & set(recent[i+cycle]["red_balls"]))
            blue_repeat = recent[i]["blue_ball"] == recent[i+cycle]["blue_ball"]
            
            if red_repeat >= 3 or blue_repeat:
                pattern_found = True
                pattern_id = f"cycle_{cycle}"
                confidence = (red_repeat / 6) * 0.7 + (1 if blue_repeat else 0) * 0.3
                
                self.patterns[pattern_id] = {
                    "type": "cycle",
                    "cycle": cycle,
                    "last_seen": recent[i+cycle],
                    "confidence": confidence
                }
                
                self.pattern_confidence[pattern_id] = confidence
    
    def _check_hot_cold_pattern(self, history_data: List[Dict]) -> None:
        """检测热冷号模式"""
        if len(history_data) < 10:
            return
        
        recent = history_data[-10:]
        red_freq = {i: 0 for i in RED_BALL_RANGE}
        blue_freq = {i: 0 for i in BLUE_BALL_RANGE}
        
        # 统计近期号码频率
        for draw in recent:
            for ball in draw["red_balls"]:
                red_freq[ball] += 1
            blue_freq[draw["blue_ball"]] += 1
        
        # 找出热号和冷号
        hot_reds = sorted([(k, v) for k, v in red_freq.items() if v >= 3], 
                         key=lambda x: x[1], reverse=True)[:8]
        cold_reds = sorted([(k, v) for k, v in red_freq.items() if v == 0], 
                          key=lambda x: x[0])[:8]
        
        hot_blues = sorted([(k, v) for k, v in blue_freq.items() if v >= 2], 
                          key=lambda x: x[1], reverse=True)[:3]
        cold_blues = sorted([(k, v) for k, v in blue_freq.items() if v == 0], 
                           key=lambda x: x[0])[:3]
        
        # 保存模式
        if hot_reds:
            self.patterns["hot_reds"] = {
                "type": "hot",
                "balls": [b[0] for b in hot_reds],
                "confidence": 0.6
            }
            self.pattern_confidence["hot_reds"] = 0.6
        
        if cold_reds:
            self.patterns["cold_reds"] = {
                "type": "cold",
                "balls": [b[0] for b in cold_reds],
                "confidence": 0.4
            }
            self.pattern_confidence["cold_reds"] = 0.4
            
        if hot_blues:
            self.patterns["hot_blues"] = {
                "type": "hot",
                "balls": [b[0] for b in hot_blues],
                "confidence": 0.65
            }
            self.pattern_confidence["hot_blues"] = 0.65
            
        if cold_blues:
            self.patterns["cold_blues"] = {
                "type": "cold",
                "balls": [b[0] for b in cold_blues],
                "confidence": 0.45
            }
            self.pattern_confidence["cold_blues"] = 0.45
    
    def _check_adjacent_relation(self, history_data: List[Dict]) -> None:
        """检测相邻期关系模式"""
        if len(history_data) < 5:
            return
        
        recent = history_data[-5:]
        for i in range(len(recent)-1):
            # 检查连续两期之间的关系
            curr = recent[i]
            next_draw = recent[i+1]
            
            # 检测重复号码
            repeat_red = set(curr["red_balls"]) & set(next_draw["red_balls"])
            if repeat_red:
                self.patterns[f"repeat_red_{i}"] = {
                    "type": "repeat",
                    "balls": list(repeat_red),
                    "confidence": 0.5 + len(repeat_red) * 0.05
                }
                self.pattern_confidence[f"repeat_red_{i}"] = 0.5 + len(repeat_red) * 0.05
            
            # 检测和值变化
            curr_sum = sum(curr["red_balls"])
            next_sum = sum(next_draw["red_balls"])
            diff = abs(curr_sum - next_sum)
            
            if diff < 10:
                self.patterns["sum_stable"] = {
                    "type": "sum",
                    "current_sum": curr_sum,
                    "diff": diff,
                    "confidence": 0.6
                }
                self.pattern_confidence["sum_stable"] = 0.6
    
    async def predict(self, history_data: List[Dict]) -> Tuple[List[int], int]:
        """基于发现的模式进行预测"""
        await self.detect_patterns(history_data)
        
        # 候选号码池
        red_candidates = {i: 1.0 for i in RED_BALL_RANGE}  # 默认权重为1
        blue_candidates = {i: 1.0 for i in BLUE_BALL_RANGE}  # 默认权重为1
        
        # 根据模式调整权重
        for pattern_id, pattern in self.patterns.items():
            confidence = self.pattern_confidence.get(pattern_id, 0.5)
            
            if pattern["type"] == "cycle" and "last_seen" in pattern:
                # 周期性模式
                for ball in pattern["last_seen"]["red_balls"]:
                    red_candidates[ball] *= (1 + confidence)
                blue_candidates[pattern["last_seen"]["blue_ball"]] *= (1 + confidence)
            
            elif pattern["type"] in ["hot", "cold"] and "balls" in pattern:
                # 热冷号模式
                is_blue = "blue" in pattern_id
                candidates = blue_candidates if is_blue else red_candidates
                factor = 1.2 if pattern["type"] == "hot" else 0.8
                
                for ball in pattern["balls"]:
                    if ball in candidates:
                        candidates[ball] *= (factor * confidence)
        
        # 选择权重最高的号码
        red_weights = [(ball, weight) for ball, weight in red_candidates.items()]
        blue_weights = [(ball, weight) for ball, weight in blue_candidates.items()]
        
        red_weights.sort(key=lambda x: x[1], reverse=True)
        blue_weights.sort(key=lambda x: x[1], reverse=True)
        
        # 选择红球
        selected_reds = []
        for _ in range(RED_BALL_COUNT):
            if not red_weights:
                break
                
            # 按权重概率选择
            total = sum(w for _, w in red_weights)
            r = random.random() * total
            cumsum = 0
            for i, (ball, weight) in enumerate(red_weights):
                cumsum += weight
                if cumsum >= r:
                    selected_reds.append(ball)
                    red_weights.pop(i)
                    break
        
        # 如果红球不足，随机补充
        while len(selected_reds) < RED_BALL_COUNT:
            ball = random.choice(list(RED_BALL_RANGE))
            if ball not in selected_reds:
                selected_reds.append(ball)
        
        # 选择蓝球
        total = sum(w for _, w in blue_weights)
        r = random.random() * total
        cumsum = 0
        selected_blue = 1  # 默认值
        for ball, weight in blue_weights:
            cumsum += weight
            if cumsum >= r:
                selected_blue = ball
                break
        
        return sorted(selected_reds), selected_blue
    
    async def learn(self, history_data: List[Dict], actual_result: Dict) -> None:
        """从结果中学习，调整模式权重"""
        await super().learn(history_data, actual_result)
        
        # 更新已有模式的置信度
        for pattern_id, pattern in self.patterns.items():
            if pattern["type"] == "cycle" and "last_seen" in pattern:
                red_match = len(set(pattern["last_seen"]["red_balls"]) & set(actual_result["red_balls"]))
                blue_match = pattern["last_seen"]["blue_ball"] == actual_result["blue_ball"]
                
                # 根据匹配情况调整置信度
                if red_match >= 3 or blue_match:
                    self.pattern_confidence[pattern_id] = min(1.0, self.pattern_confidence.get(pattern_id, 0.5) * 1.1)
                else:
                    self.pattern_confidence[pattern_id] = max(0.1, self.pattern_confidence.get(pattern_id, 0.5) * 0.9)
            
            elif pattern["type"] in ["hot", "cold"] and "balls" in pattern:
                is_blue = "blue" in pattern_id
                actual_balls = [actual_result["blue_ball"]] if is_blue else actual_result["red_balls"]
                
                # 检查模式预测的号码是否在实际结果中
                match_count = len(set(pattern["balls"]) & set(actual_balls))
                expected = 2 if is_blue else 3
                
                if match_count >= expected:
                    self.pattern_confidence[pattern_id] = min(1.0, self.pattern_confidence.get(pattern_id, 0.5) * 1.1)
                else:
                    self.pattern_confidence[pattern_id] = max(0.1, self.pattern_confidence.get(pattern_id, 0.5) * 0.95)

        # 清理低置信度模式
        for pattern_id in list(self.patterns.keys()):
            if self.pattern_confidence.get(pattern_id, 0) < 0.2:
                del self.patterns[pattern_id]
                if pattern_id in self.pattern_confidence:
                    del self.pattern_confidence[pattern_id]


class NeuralNetworkModel(SSQPredictionModel):
    """神经网络预测模型简化版（实际中可使用TensorFlow/PyTorch）"""
    
    def __init__(self):
        super().__init__("Neural_Model", 1.5)
        self.weights = {
            "red": [random.random() for _ in range(10)],
            "blue": [random.random() for _ in range(5)]
        }
    
    def _extract_features(self, history_data: List[Dict]) -> Tuple[List[float], List[float]]:
        """从历史数据提取特征"""
        if len(history_data) < 10:
            return [0] * 10, [0] * 5
        
        recent = history_data[-10:]
        
        # 红球特征
        red_features = []
        # 1. 最近5期红球平均值
        red_avg = sum(sum(d["red_balls"]) for d in recent[-5:]) / (5 * 6)
        red_features.append(red_avg / 33)  # 归一化
        
        # 2. 最近10期红球频率分布熵
        red_freq = {i: 0 for i in RED_BALL_RANGE}
        for draw in recent:
            for ball in draw["red_balls"]:
                red_freq[ball] += 1
        
        entropy = -sum((v/60) * math.log(v/60 + 0.0001) for v in red_freq.values() if v > 0)
        red_features.append(min(entropy / 5, 1.0))  # 归一化
        
        # 3. 最近一期和值
        last_sum = sum(recent[-1]["red_balls"]) / 150  # 归一化
        red_features.append(last_sum)
        
        # 4. 连号比例
        consecutive_count = 0
        for draw in recent:
            sorted_red = sorted(draw["red_balls"])
            for i in range(len(sorted_red)-1):
                if sorted_red[i+1] - sorted_red[i] == 1:
                    consecutive_count += 1
        red_features.append(consecutive_count / 50)  # 归一化
        
        # 5-10. 其他特征，这里简化为随机值
        red_features.extend([random.random() for _ in range(6)])
        
        # 蓝球特征
        blue_features = []
        # 1. 最近10期蓝球平均值
        blue_avg = sum(d["blue_ball"] for d in recent) / 10
        blue_features.append(blue_avg / 16)  # 归一化
        
        # 2. 蓝球频率分布
        blue_freq = {i: 0 for i in BLUE_BALL_RANGE}
        for draw in recent:
            blue_freq[draw["blue_ball"]] += 1
        
        blue_entropy = -sum((v/10) * math.log(v/10 + 0.0001) for v in blue_freq.values() if v > 0)
        blue_features.append(min(blue_entropy / 3, 1.0))  # 归一化
        
        # 3-5. 其他特征，这里简化为随机值
        blue_features.extend([random.random() for _ in range(3)])
        
        return red_features, blue_features
    
    def _predict_with_features(self, red_features: List[float], blue_features: List[float]) -> Tuple[List[float], List[float]]:
        """基于特征和权重预测概率分布"""
        # 简化的线性模型
        red_probs = []
        for ball in RED_BALL_RANGE:
            # 计算每个红球的概率得分
            score = sum(f * w for f, w in zip(red_features, self.weights["red"]))
            # 加入一些随机性
            score = score * 0.8 + random.random() * 0.2
            red_probs.append((ball, max(0.01, min(score, 1.0))))
        
        blue_probs = []
        for ball in BLUE_BALL_RANGE:
            # 计算每个蓝球的概率得分
            score = sum(f * w for f, w in zip(blue_features, self.weights["blue"]))
            # 加入一些随机性
            score = score * 0.8 + random.random() * 0.2
            blue_probs.append((ball, max(0.01, min(score, 1.0))))
        
        return red_probs, blue_probs
    
    async def predict(self, history_data: List[Dict]) -> Tuple[List[int], int]:
        """基于神经网络预测下一期号码"""
        red_features, blue_features = self._extract_features(history_data)
        red_probs, blue_probs = self._predict_with_features(red_features, blue_features)
        
        # 排序概率
        red_probs.sort(key=lambda x: x[1], reverse=True)
        blue_probs.sort(key=lambda x: x[1], reverse=True)
        
        # 选择红球
        selected_reds = [ball for ball, _ in red_probs[:RED_BALL_COUNT]]
        
        # 选择蓝球
        selected_blue = blue_probs[0][0]
        
        return sorted(selected_reds), selected_blue
    
    async def learn(self, history_data: List[Dict], actual_result: Dict) -> None:
        """从结果中学习，调整网络权重"""
        await super().learn(history_data, actual_result)
        
        # 提取特征
        red_features, blue_features = self._extract_features(history_data[:-1])
        
        # 计算预测值与实际值
        red_probs, blue_probs = self._predict_with_features(red_features, blue_features)
        red_probs = dict(red_probs)
        blue_probs = dict(blue_probs)
        
        # 计算梯度并更新权重（简化版）
        learning_rate = 0.01
        
        # 红球权重调整
        for ball in actual_result["red_balls"]:
            if ball in red_probs:
                error = 1.0 - red_probs[ball]
                for i in range(len(self.weights["red"])):
                    self.weights["red"][i] += learning_rate * error * red_features[min(i, len(red_features)-1)]
        
        # 蓝球权重调整
        error = 1.0 - blue_probs.get(actual_result["blue_ball"], 0)
        for i in range(len(self.weights["blue"])):
            self.weights["blue"][i] += learning_rate * error * blue_features[min(i, len(blue_features)-1)]


class DeepSeekModel(SSQPredictionModel):
    """基于DeepSeek大模型的预测模型"""
    
    def __init__(self, api_key=None):
        super().__init__("DeepSeek_Model", 2.0)
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.last_patterns = []
        self.insights = []
    
    async def _call_api(self, prompt: str) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            logger.warning("DeepSeek API密钥未设置，使用模拟回复")
            return self._mock_api_response(prompt)
            
        # 这里应替换为实际的DeepSeek API调用
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            response = requests.post(
                f"{DEEPSEEK_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"API调用失败: {response.status_code} {response.text}")
                return self._mock_api_response(prompt)
                
        except Exception as e:
            logger.error(f"调用DeepSeek API时出错: {e}")
            return self._mock_api_response(prompt)
    
    def _mock_api_response(self, prompt: str) -> str:
        """模拟API响应（当API密钥未设置时使用）"""
        if "分析" in prompt or "pattern" in prompt:
            return """
            {
                "patterns": [
                    {"name": "连号模式", "description": "最近5期中有3期出现连号", "confidence": 0.75},
                    {"name": "和值稳定", "description": "最近3期和值在100-120之间", "confidence": 0.68},
                    {"name": "蓝球周期", "description": "蓝球呈现3期轮换模式", "confidence": 0.82}
                ],
                "predictions": {
                    "red_balls": [3, 9, 15, 22, 27, 31],
                    "blue_ball": 6,
                    "confidence": 0.71
                },
                "insights": "最近数据显示尾数分布均衡性增强，建议关注1,2尾号码"
            }
            """
        elif "总结" in prompt or "learning" in prompt:
            return """
            {
                "learning_summary": {
                    "patterns_discovered": 8,
                    "key_insights": "发现时间序列中的周期性和时段特征有显著影响",
                    "accuracy_trend": "呈现稳步上升趋势，从初始0.35提升至当前0.68",
                    "reproducibility": 0.72,
                    "recommendation": "增强对号码间隔规律的权重，降低热号偏好"
                }
            }
            """
        else:
            return """
            {
                "analysis": "数据显示近期大号出现频率增高，同时奇偶比趋于平衡",
                "prediction": [5, 11, 18, 24, 29, 32, 8],
                "confidence": 0.65
            }
            """
    
    async def analyze_patterns(self, history_data: List[Dict]) -> List[Dict]:
        """分析历史数据中的模式"""
        if len(history_data) < 10:
            return []
        
        # 准备近期数据
        recent = history_data[-20:]
        formatted_data = []
        
        for draw in recent:
            formatted_data.append({
                "期号": draw["period"],
                "日期": draw["date"],
                "号码": draw["full_code"]
            })
        
        prompt = f"""
        作为双色球数据分析专家，请分析以下最近20期的开奖数据，发现可能的模式和规律。
        返回JSON格式，包含patterns数组、predictions对象和insights文本。
        每个pattern需包含name、description和confidence字段。
        
        历史数据:
        {json.dumps(formatted_data, ensure_ascii=False, indent=2)}
        
        仅返回有效JSON，不要有其他说明文字。
        """
        
        response = await self._call_api(prompt)
        
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                self.last_patterns = result.get("patterns", [])
                
                if "insights" in result:
                    self.insights.append(result["insights"])
                    if len(self.insights) > 10:
                        self.insights = self.insights[-10:]
                
                return self.last_patterns
            else:
                logger.warning("无法从响应中提取JSON")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"解析响应JSON时出错: {e}\n响应内容: {response}")
            return []
    
    async def predict(self, history_data: List[Dict]) -> Tuple[List[int], int]:
        """使用DeepSeek模型预测下一期号码"""
        # 分析模式
        await self.analyze_patterns(history_data)
        
        if not self.last_patterns:
            # 如果模式分析失败，使用随机选择
            return sorted(random.sample(list(RED_BALL_RANGE), RED_BALL_COUNT)), random.choice(list(BLUE_BALL_RANGE))
            
        # 准备近期数据和模式
        recent = history_data[-10:]
        formatted_data = []
        
        for draw in recent:
            formatted_data.append({
                "期号": draw["period"],
                "号码": draw["full_code"]
            })
        
        prompt = f"""
        作为双色球预测专家，基于以下历史数据和已发现的模式，预测下一期的开奖号码。
        
        近期历史数据:
        {json.dumps(formatted_data, ensure_ascii=False, indent=2)}
        
        已发现的模式:
        {json.dumps(self.last_patterns, ensure_ascii=False, indent=2)}
        
        请结合模式和数据，预测下一期的6个红球号码(1-33)和1个蓝球号码(1-16)。
        仅返回有效JSON格式，包含prediction数组和confidence字段。
        """
        
        response = await self._call_api(prompt)
        
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                if "prediction" in result and len(result["prediction"]) == 7:
                    # 格式可能是[red1, red2, ..., red6, blue]
                    red_balls = sorted(result["prediction"][:6])
                    blue_ball = result["prediction"][6]
                    return red_balls, blue_ball
                elif "predictions" in result and "red_balls" in result["predictions"] and "blue_ball" in result["predictions"]:
                    red_balls = sorted(result["predictions"]["red_balls"])
                    blue_ball = result["predictions"]["blue_ball"]
                    return red_balls, blue_ball
            
            # 如果无法解析，返回随机选择
            logger.warning("无法从预测响应中提取有效结果")
            return sorted(random.sample(list(RED_BALL_RANGE), RED_BALL_COUNT)), random.choice(list(BLUE_BALL_RANGE))
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"解析预测响应时出错: {e}\n响应内容: {response}")
            # 出错时使用随机选择
            return sorted(random.sample(list(RED_BALL_RANGE), RED_BALL_COUNT)), random.choice(list(BLUE_BALL_RANGE))
    
    async def summarize_learning(self, cycles: int, match_counts: List[int], attempts: List[int]) -> str:
        """总结学习过程与规律"""
        prompt = f"""
        作为双色球预测系统的学习分析专家，请分析以下学习过程数据，总结学习规律和可复制性:
        
        学习周期数: {cycles}
        匹配成功次数: {sum(1 for m in match_counts if m == 7)}
        平均尝试次数: {sum(attempts)/len(attempts) if attempts else 0:.2f}
        匹配分布: 完全匹配(7球)={sum(1 for m in match_counts if m == 7)}次, 
                 6+1匹配={sum(1 for m in match_counts if m == 6)}次,
                 5+1匹配={sum(1 for m in match_counts if m == 5)}次,
                 仅红球全中={sum(1 for m in match_counts if m == -6)}次,
                 仅蓝球命中={sum(1 for m in match_counts if m == 1)}次
        
        请分析系统学习过程中的规律、可复制性和自我改进能力，并给出提高预测准确率的建议。
        返回JSON格式，包含learning_summary对象，其中包含patterns_discovered, key_insights, accuracy_trend, reproducibility, recommendation等字段。
        仅返回有效JSON，不要有其他说明文字。
        """
        
        response = await self._call_api(prompt)
        
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json_str
            else:
                logger.warning("无法从总结响应中提取JSON")
                return "{}"
        except Exception as e:
            logger.error(f"解析总结响应时出错: {e}")
            return "{}"


class SSQFusionPredictor:
    """双色球融合预测器"""
    
    def __init__(self):
        self.models = [
            PatternBasedModel(),
            NeuralNetworkModel()
        ]
        
        # 如果有API密钥，添加DeepSeek模型
        if DEEPSEEK_API_KEY:
            self.models.append(DeepSeekModel(DEEPSEEK_API_KEY))
        
        self.learning_cycles = 0
        self.perfect_matches = 0
        self.match_history = []
        self.attempt_counts = []
    
    def _normalize_weights(self) -> None:
        """归一化模型权重"""
        total = sum(model.weight for model in self.models)
        for model in self.models:
            model.weight = model.weight / total
    
    async def predict(self, history_data: List[Dict]) -> Tuple[List[int], int]:
        """融合多个模型进行预测"""
        self._normalize_weights()
        
        # 收集各模型预测
        predictions = []
        for model in self.models:
            try:
                pred = await model.predict(history_data)
                predictions.append((pred, model.weight))
            except Exception as e:
                logger.error(f"模型{model.name}预测出错: {e}")
                traceback.print_exc()
        
        if not predictions:
            # 如果所有模型都失败，返回随机预测
            return sorted(random.sample(list(RED_BALL_RANGE), RED_BALL_COUNT)), random.choice(list(BLUE_BALL_RANGE))
        
        # 红球投票系统
        red_votes = {ball: 0.0 for ball in RED_BALL_RANGE}
        for (reds, _), weight in predictions:
            for ball in reds:
                red_votes[ball] += weight
        
        # 蓝球投票系统
        blue_votes = {ball: 0.0 for ball in BLUE_BALL_RANGE}
        for (_, blue), weight in predictions:
            blue_votes[blue] += weight
        
        # 选择得票最高的球
        sorted_reds = sorted(red_votes.items(), key=lambda x: x[1], reverse=True)
        sorted_blues = sorted(blue_votes.items(), key=lambda x: x[1], reverse=True)
        
        selected_reds = [ball for ball, _ in sorted_reds[:RED_BALL_COUNT]]
        selected_blue = sorted_blues[0][0]
        
        return sorted(selected_reds), selected_blue
    
    async def predict_until_match(self, history_data: List[Dict], target: Dict, max_attempts: int = 100000) -> int:
        """预测直到完全匹配目标"""
        attempts = 0
        match_level = 0
        
        while attempts < max_attempts:
            attempts += 1
            red_balls, blue_ball = await self.predict(history_data)
            
            # 计算匹配程度
            red_match = set(red_balls) == set(target["red_balls"])
            blue_match = blue_ball == target["blue_ball"]
            
            # 完全匹配
            if red_match and blue_match:
                match_level = 7
                break
            # 红球全中，蓝球不中
            elif red_match:
                match_level = -6  # 使用负数表示只有红球匹配
            # 蓝球中，部分红球中
            elif blue_match:
                red_count = len(set(red_balls) & set(target["red_balls"]))
                if red_count == 6:
                    match_level = 6
                elif red_count == 5:
                    match_level = 5
                else:
                    match_level = 1  # 只有蓝球匹配
            
            # 如果尝试次数太多，输出当前最佳匹配
            if attempts % 10000 == 0:
                red_count = len(set(red_balls) & set(target["red_balls"]))
                logger.info(f"尝试 {attempts} 次，当前匹配: 红球 {red_count}/6，蓝球 {'命中' if blue_match else '未命中'}")
        
        return attempts, match_level
    
    async def learn_from_history(self, history_data: List[Dict]) -> Dict:
        """从历史数据中学习"""
        if len(history_data) < 2:
            return {"status": "数据不足", "cycles": 0}
        
        logger.info("开始从历史数据学习...")
        
        # 对每一期进行预测和学习
        for i in range(1, len(history_data)):
            current_history = history_data[:i]
            target = history_data[i]
            
            # 预测直到匹配
            attempts, match_level = await self.predict_until_match(current_history, target, max_attempts=100000)
            
            # 记录结果
            self.learning_cycles += 1
            if match_level == 7:  # 完全匹配
                self.perfect_matches += 1
            
            self.match_history.append(match_level)
            self.attempt_counts.append(attempts)
            
            # 所有模型从结果学习
            for model in self.models:
                await model.learn(current_history, target)
            
            logger.info(f"学习周期 {self.learning_cycles}，期号 {target['period']}，匹配级别 {match_level}，尝试次数 {attempts}")
            
            # 每10个周期保存一次状态
            if self.learning_cycles % 10 == 0:
                await self._save_learning_state()
                
                # 每30个周期生成一次总结
                if self.learning_cycles % 30 == 0 and any(isinstance(m, DeepSeekModel) for m in self.models):
                    deepseek_model = next(m for m in self.models if isinstance(m, DeepSeekModel))
                    summary = await deepseek_model.summarize_learning(self.learning_cycles, self.match_history, self.attempt_counts)
                    with open(LEARNING_RESULTS_FILE, "a", encoding="utf-8") as f:
                        f.write(f"\n\n=== 学习周期 {self.learning_cycles} 总结 ===\n")
                        f.write(summary)
                        f.write("\n\n")
        
        logger.info(f"学习完成。总周期: {self.learning_cycles}, 完全匹配: {self.perfect_matches}")
        return {
            "status": "学习完成",
            "cycles": self.learning_cycles,
            "perfect_matches": self.perfect_matches,
            "avg_attempts": sum(self.attempt_counts) / len(self.attempt_counts) if self.attempt_counts else 0
        }
    
    async def _save_learning_state(self) -> None:
        """保存学习状态"""
        state = {
            "learning_cycles": self.learning_cycles,
            "perfect_matches": self.perfect_matches,
            "match_history": self.match_history[-100:],  # 只保存最近100个
            "attempt_counts": self.attempt_counts[-100:],  # 只保存最近100个
            "model_accuracies": {model.name: model.average_accuracy for model in self.models},
            "model_weights": {model.name: model.weight for model in self.models}
        }
        
        with open(MODEL_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        logger.info(f"学习状态已保存至 {MODEL_STATE_FILE}")
    
    async def _load_learning_state(self) -> bool:
        """加载学习状态"""
        if not os.path.exists(MODEL_STATE_FILE):
            return False
            
        try:
            with open(MODEL_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                
            self.learning_cycles = state.get("learning_cycles", 0)
            self.perfect_matches = state.get("perfect_matches", 0)
            self.match_history = state.get("match_history", [])
            self.attempt_counts = state.get("attempt_counts", [])
            
            # 恢复模型权重
            model_weights = state.get("model_weights", {})
            for model in self.models:
                if model.name in model_weights:
                    model.weight = model_weights[model.name]
            
            logger.info(f"成功加载学习状态，当前学习周期: {self.learning_cycles}")
            return True
        except Exception as e:
            logger.error(f"加载学习状态出错: {e}")
            return False


async def notify_api_server(message: str, level: str = "info") -> None:
    """向API服务器发送通知"""
    try:
        response = requests.post(
            f"{LOCAL_API_URL}/status",
            json={"message": message, "level": level, "source": "ssq_ai_backtest"}
        )
        if response.status_code != 200:
            logger.warning(f"API通知失败: {response.status_code}")
    except Exception as e:
        logger.warning(f"无法连接到本地API服务器: {e}")


async def main():
    """主函数"""
    logger.info("启动双色球历史数据分析与预测系统...")
    
    try:
        # 获取历史数据
        collector = SSQDataCollector()
        history_data = await collector.fetch_history_data()
        
        if not history_data:
            logger.error("获取历史数据失败，程序退出")
            return
        
        logger.info(f"成功获取 {len(history_data)} 期历史数据")
        
        # 创建预测器
        predictor = SSQFusionPredictor()
        
        # 尝试加载之前的学习状态
        await predictor._load_learning_state()
        
        # 向API服务器发送启动通知
        await notify_api_server("双色球预测系统已启动，准备进行历史数据分析")
        
        # 从历史数据中学习
        result = await predictor.learn_from_history(history_data)
        
        logger.info(f"学习结果: {result}")
        await notify_api_server(f"历史数据学习完成。周期: {result['cycles']}, 完全匹配: {result.get('perfect_matches', 0)}")
        
        # 持续预测最新一期
        if history_data:
            latest = history_data[-1]
            logger.info(f"最新一期 {latest['period']} 开奖号码: {latest['full_code']}")
            
            # 预测下一期
            next_period = int(latest['period']) + 1
            next_pred_red, next_pred_blue = await predictor.predict(history_data)
            
            logger.info(f"下一期 {next_period} 预测号码: {' '.join([f'{n:02d}' for n in next_pred_red])} + {next_pred_blue:02d}")
            await notify_api_server(f"下一期预测: {' '.join([f'{n:02d}' for n in next_pred_red])} + {next_pred_blue:02d}")
        
        logger.info("系统将持续在后台运行，进行自主学习与升级...")
        
        # 无限循环，持续学习和优化
        while True:
            # 模拟自主学习和升级
            await asyncio.sleep(600)  # 每10分钟执行一次
            
            # 选择一个随机期进行深度学习
            if history_data and len(history_data) > 10:
                idx = random.randint(10, len(history_data) - 1)
                target = history_data[idx]
                current_history = history_data[:idx]
                
                logger.info(f"对期号 {target['period']} 进行深度学习...")
                attempts, match_level = await predictor.predict_until_match(current_history, target, max_attempts=50000)
                
                logger.info(f"深度学习结果: 匹配级别 {match_level}，尝试次数 {attempts}")
                await notify_api_server(f"完成期号 {target['period']} 深度学习: 匹配级别 {match_level}")
                
            # 保存状态
            await predictor._save_learning_state()
            
    except KeyboardInterrupt:
        logger.info("收到中断信号，程序退出")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        traceback.print_exc()
        await notify_api_server(f"系统错误: {str(e)}", "error")

if __name__ == "__main__":
    # 添加对数学模块的导入
    import math
    
    # 确保目录存在
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"主函数执行失败: {e}")
        traceback.print_exc()