"""
双色球推理大师集成模块
提供与现有系统的集成接口
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from ssq_reasoning_master import SSQReasoningMaster


class SSQReasoningMasterIntegration:
    """双色球推理大师集成类"""
    
    def __init__(self):
        self.master = SSQReasoningMaster()
        self.integration_log = 'ssq_reasoning_master_integration.log'
    
    def predict_next_issue(self, issue_number: Optional[str] = None) -> Dict:
        """
        预测下一期双色球
        
        Args:
            issue_number: 期号，如 '2025001'
            
        Returns:
            预测结果字典
        """
        result = self.master.multi_dimensional_reasoning(issue_number)
        
        # 记录到日志
        self._log_prediction(result)
        
        return result
    
    def get_simple_prediction(self) -> Tuple[List[int], int]:
        """
        获取简单预测结果（只返回红球和蓝球）
        
        Returns:
            (红球列表, 蓝球)
        """
        result = self.master.multi_dimensional_reasoning()
        fusion = result['fusion']
        return fusion['red'], fusion['blue']
    
    def review_prediction(self, prediction_result: Dict, 
                         actual_reds: List[int], actual_blue: int) -> Dict:
        """
        复盘预测结果
        
        Args:
            prediction_result: 之前的预测结果
            actual_reds: 实际红球
            actual_blue: 实际蓝球
            
        Returns:
            复盘统计信息
        """
        actual = (actual_reds, actual_blue)
        self.master.self_review(prediction_result, actual)
        
        # 计算命中情况
        fusion = prediction_result['fusion']
        red_hits = len(set(fusion['red']) & set(actual_reds))
        blue_hit = 1 if fusion['blue'] == actual_blue else 0
        
        return {
            'red_hits': red_hits,
            'blue_hit': blue_hit,
            'total_score': red_hits + blue_hit * 2
        }
    
    def get_status(self) -> Dict:
        """
        获取系统状态
        
        Returns:
            状态信息字典
        """
        state = self.master.autonomous_state
        perf = state.get('performance_history', [])
        
        status = {
            'training_cycles': state.get('training_cycles', 0),
            'review_cycles': state.get('review_cycles', 0),
            'learning_cycles': state.get('learning_cycles', 0),
            'repair_cycles': state.get('repair_cycles', 0),
            'dimension_weights': self.master.ai.model_weights['dimension_weights']
        }
        
        if perf:
            status['average_red_hits'] = sum(p['red_hits'] for p in perf) / len(perf)
            status['average_blue_hit_rate'] = sum(p['blue_hit'] for p in perf) / len(perf)
            status['average_score'] = sum(p['total_score'] for p in perf) / len(perf)
        
        return status
    
    def run_autonomous_cycle(self, iterations: int = 1) -> Dict:
        """
        运行自主循环
        
        Args:
            iterations: 循环次数
            
        Returns:
            运行结果摘要
        """
        initial_state = self.get_status()
        
        self.master.autonomous_loop(iterations=iterations)
        
        final_state = self.get_status()
        
        return {
            'iterations': iterations,
            'initial_state': initial_state,
            'final_state': final_state
        }
    
    def _log_prediction(self, result: Dict):
        """记录预测到日志"""
        try:
            log_entry = {
                'timestamp': result.get('timestamp'),
                'issue': result.get('issue'),
                'red': result['fusion']['red'],
                'blue': result['fusion']['blue'],
                'confidence': result['fusion'].get('confidence', 0)
            }
            
            with open(self.integration_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[集成日志] 记录失败: {e}")
    
    def get_detailed_analysis(self) -> str:
        """
        获取详细分析报告（文本格式）
        
        Returns:
            分析报告文本
        """
        result = self.master.multi_dimensional_reasoning()
        
        report = []
        report.append("=" * 60)
        report.append("双色球推理大师 - 详细分析报告")
        report.append("=" * 60)
        report.append("")
        
        # 各维度预测
        report.append("【各维度预测】")
        report.append("-" * 60)
        
        for dim_name, dim_data in result['predictions'].items():
            dim_cn = {
                'iching': '周易',
                'statistics': '统计学',
                'quantum': '量子力学',
                'ai': 'AI人工智能'
            }.get(dim_name, dim_name)
            
            red = dim_data.get('red', [])
            blue = dim_data.get('blue', 0)
            
            report.append(f"\n{dim_cn}维度:")
            report.append(f"  红球: {red}")
            report.append(f"  蓝球: {blue}")
            
            # 特殊分析信息
            if dim_name == 'iching' and 'analysis' in dim_data:
                report.append(f"  五行分布: {dim_data['analysis']}")
            elif dim_name == 'statistics':
                if 'hot_numbers' in dim_data:
                    report.append(f"  热号: {dim_data['hot_numbers'][:8]}")
                if 'cold_numbers' in dim_data:
                    report.append(f"  冷号: {dim_data['cold_numbers'][:8]}")
        
        # 融合结果
        fusion = result['fusion']
        report.append("")
        report.append("【最终融合预测】")
        report.append("-" * 60)
        report.append(f"红球: {fusion['red']}")
        report.append(f"蓝球: {fusion['blue']}")
        report.append(f"置信度: {fusion.get('confidence', 0):.2%}")
        
        # 权重信息
        report.append("")
        report.append("【维度权重】")
        report.append("-" * 60)
        for dim, weight in fusion.get('weights', {}).items():
            report.append(f"{dim}: {weight:.3f}")
        
        # 系统状态
        status = self.get_status()
        report.append("")
        report.append("【系统状态】")
        report.append("-" * 60)
        report.append(f"训练次数: {status.get('training_cycles', 0)}")
        report.append(f"复盘次数: {status.get('review_cycles', 0)}")
        report.append(f"学习次数: {status.get('learning_cycles', 0)}")
        
        if 'average_red_hits' in status:
            report.append(f"平均红球命中: {status['average_red_hits']:.2f}/6")
            report.append(f"蓝球命中率: {status['average_blue_hit_rate']:.2%}")
        
        report.append("")
        report.append("=" * 60)
        
        return '\n'.join(report)


# 全局实例（单例模式）
_global_integration = None


def get_reasoning_master_integration() -> SSQReasoningMasterIntegration:
    """获取全局集成实例"""
    global _global_integration
    if _global_integration is None:
        _global_integration = SSQReasoningMasterIntegration()
    return _global_integration


# 便捷函数
def predict_ssq(issue_number: Optional[str] = None) -> Dict:
    """便捷预测函数"""
    integration = get_reasoning_master_integration()
    return integration.predict_next_issue(issue_number)


def get_simple_ssq_prediction() -> Tuple[List[int], int]:
    """便捷获取简单预测结果"""
    integration = get_reasoning_master_integration()
    return integration.get_simple_prediction()


def review_ssq_prediction(prediction_result: Dict, 
                         actual_reds: List[int], 
                         actual_blue: int) -> Dict:
    """便捷复盘函数"""
    integration = get_reasoning_master_integration()
    return integration.review_prediction(prediction_result, actual_reds, actual_blue)


def get_ssq_status() -> Dict:
    """便捷获取状态函数"""
    integration = get_reasoning_master_integration()
    return integration.get_status()


def run_ssq_autonomous_cycle(iterations: int = 1) -> Dict:
    """便捷运行自主循环"""
    integration = get_reasoning_master_integration()
    return integration.run_autonomous_cycle(iterations)


def get_ssq_analysis_report() -> str:
    """便捷获取分析报告"""
    integration = get_reasoning_master_integration()
    return integration.get_detailed_analysis()


# 命令行接口
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'predict':
            # 预测
            result = predict_ssq()
            print(f"\n预测红球: {result['fusion']['red']}")
            print(f"预测蓝球: {result['fusion']['blue']}")
            print(f"置信度: {result['fusion']['confidence']:.2%}")
            
        elif command == 'status':
            # 状态
            status = get_ssq_status()
            print("\n系统状态:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            
        elif command == 'report':
            # 报告
            report = get_ssq_analysis_report()
            print(report)
            
        elif command == 'auto':
            # 自主循环
            iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            result = run_ssq_autonomous_cycle(iterations)
            print(f"\n完成 {result['iterations']} 轮自主循环")
            
        else:
            print(f"未知命令: {command}")
            print("\n用法:")
            print("  python ssq_reasoning_master_integration.py predict   # 预测")
            print("  python ssq_reasoning_master_integration.py status    # 状态")
            print("  python ssq_reasoning_master_integration.py report    # 报告")
            print("  python ssq_reasoning_master_integration.py auto [N]  # 自主循环")
    else:
        # 默认：显示报告
        report = get_ssq_analysis_report()
        print(report)
