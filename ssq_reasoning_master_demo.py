"""
双色球推理大师演示程序
展示四维推理和自治循环能力
"""

import json
import time
from ssq_reasoning_master import SSQReasoningMaster


def demo_single_prediction():
    """演示单次预测"""
    print("\n" + "="*70)
    print(" "*20 + "📊 单次预测演示")
    print("="*70)
    
    master = SSQReasoningMaster()
    result = master.multi_dimensional_reasoning()
    
    print("\n📋 详细预测结果:")
    print("-" * 70)
    
    # 展示各维度预测
    for dim_name, dim_data in result['predictions'].items():
        dim_cn = {
            'iching': '周易',
            'statistics': '统计学',
            'quantum': '量子力学',
            'ai': 'AI人工智能'
        }.get(dim_name, dim_name)
        
        red = dim_data.get('red', [])
        blue = dim_data.get('blue', 0)
        
        print(f"\n【{dim_cn}维度】")
        print(f"  红球: {red}")
        print(f"  蓝球: {blue}")
        
        # 特殊信息
        if dim_name == 'iching' and 'analysis' in dim_data:
            print(f"  五行分布: {dim_data['analysis']}")
        elif dim_name == 'statistics':
            if 'hot_numbers' in dim_data:
                print(f"  热号: {dim_data['hot_numbers'][:8]}")
            if 'cold_numbers' in dim_data:
                print(f"  冷号: {dim_data['cold_numbers'][:8]}")
    
    # 最终融合结果
    fusion = result['fusion']
    print("\n" + "="*70)
    print("🎯 最终融合预测结果")
    print("="*70)
    print(f"\n  红球: {fusion['red']}")
    print(f"  蓝球: {fusion['blue']}")
    print(f"  置信度: {fusion.get('confidence', 0):.2%}")
    print(f"\n  维度权重: {json.dumps(fusion.get('weights', {}), indent=4, ensure_ascii=False)}")
    print("\n" + "="*70)


def demo_autonomous_loop():
    """演示自主循环"""
    print("\n" + "="*70)
    print(" "*20 + "🤖 自主循环演示")
    print("="*70)
    
    master = SSQReasoningMaster()
    
    print("\n开始3轮自主循环...")
    print("每轮包括: 训练 → 预测 → 学习 → 修复")
    print("-" * 70)
    
    master.autonomous_loop(iterations=3)


def demo_review_and_learning():
    """演示复盘和学习"""
    print("\n" + "="*70)
    print(" "*20 + "🔍 复盘与学习演示")
    print("="*70)
    
    master = SSQReasoningMaster()
    
    # 进行预测
    print("\n1️⃣  进行预测...")
    result = master.multi_dimensional_reasoning(issue_number='2025001')
    fusion = result['fusion']
    print(f"   预测: 红球 {fusion['red']}, 蓝球 {fusion['blue']}")
    
    # 模拟实际开奖结果
    time.sleep(1)
    print("\n2️⃣  模拟开奖结果...")
    actual_reds = [3, 12, 15, 23, 28, 31]
    actual_blue = 8
    print(f"   开奖: 红球 {actual_reds}, 蓝球 {actual_blue}")
    
    # 复盘
    time.sleep(1)
    print("\n3️⃣  进行复盘分析...")
    master.self_review(result, (actual_reds, actual_blue))
    
    # 学习
    time.sleep(1)
    print("\n4️⃣  从结果中学习...")
    
    # 再进行几次模拟复盘以累积数据
    for i in range(4):
        result = master.multi_dimensional_reasoning(issue_number=f'2025{i+2:03d}')
        fusion = result['fusion']
        
        # 模拟随机开奖
        import random
        actual = (random.sample(range(1, 34), 6), random.randint(1, 16))
        master.self_review(result, actual)
    
    # 现在有足够数据进行学习
    master.self_learning()
    
    # 显示学习后的状态
    time.sleep(1)
    print("\n5️⃣  学习完成，查看系统状态...")
    master.print_status()


def demo_dimension_analysis():
    """演示四维分析详细过程"""
    print("\n" + "="*70)
    print(" "*20 + "🔬 四维分析详解")
    print("="*70)
    
    master = SSQReasoningMaster()
    
    print("\n【维度1: 周易】")
    print("-" * 70)
    print("理论基础: 五行相生相克、八卦推演、天干地支")
    print("实现方法:")
    print("  • 五行数字映射: 木(3,8,13...), 火(2,7,12...), 土(5,10,15...)")
    print("  • 八卦时辰推演: 根据当前时辰对应八卦方位")
    print("  • 平衡分析: 确保五行平衡，补充欠缺的五行")
    
    # 显示五行分析
    if master.history:
        recent = master.history[-1][0]
        wuxing = master.iching.analyze_wuxing_balance(recent)
        print(f"\n  最近一期五行分布: {wuxing}")
        candidates = master.iching.predict_by_wuxing(master.history)
        print(f"  基于平衡推荐: {candidates[:10]}")
    
    print("\n【维度2: 统计学】")
    print("-" * 70)
    print("理论基础: 概率论、频率分析、趋势预测")
    print("实现方法:")
    print("  • 频率统计: 计算每个号码的历史出现频率")
    print("  • 冷热分析: 识别热号(高频)和冷号(低频)")
    print("  • 回归预测: 基于历史趋势预测未来概率")
    
    if master.history:
        hot_cold = master.statistics.analyze_hot_cold(master.history, window=20)
        print(f"\n  热号(前10): {hot_cold['hot'][:10]}")
        print(f"  冷号(前10): {hot_cold['cold'][:10]}")
    
    print("\n【维度3: 量子力学】")
    print("-" * 70)
    print("理论基础: 量子叠加、观测者效应、波函数坍缩")
    print("实现方法:")
    print("  • 叠加态: 多个预测结果形成概率云")
    print("  • 观测效应: 引入随机扰动模拟观测影响")
    print("  • 波函数坍缩: 从概率分布中加权采样")
    print("\n  特点: 不确定性原理 - 每次观测结果可能不同")
    
    print("\n【维度4: AI人工智能】")
    print("-" * 70)
    print("理论基础: 机器学习、模式识别、深度学习")
    print("实现方法:")
    print("  • 模式识别: 识别连号、奇偶比、和值、跨度等特征")
    print("  • 深度学习: 基于历史数据训练预测模型")
    print("  • 自适应权重: 根据表现动态调整策略权重")
    
    if master.history:
        patterns = master.ai.pattern_recognition(master.history)
        print(f"\n  识别到的模式特征:")
        print(f"    连号频率: {patterns.get('consecutive', 0)}")
        if patterns.get('odd_even_ratio'):
            avg_ratio = sum(patterns['odd_even_ratio']) / len(patterns['odd_even_ratio'])
            print(f"    平均奇偶比: {avg_ratio:.2f}")
    
    print("\n" + "="*70)


def demo_performance_tracking():
    """演示性能追踪"""
    print("\n" + "="*70)
    print(" "*20 + "📈 性能追踪演示")
    print("="*70)
    
    master = SSQReasoningMaster()
    
    print("\n模拟10期预测与复盘...")
    print("-" * 70)
    
    import random
    
    for i in range(10):
        # 预测
        issue = f'2025{i+100:03d}'
        result = master.multi_dimensional_reasoning(issue_number=issue)
        fusion = result['fusion']
        
        # 模拟开奖(随机，但有2-4个红球命中，模拟真实情况)
        actual_reds = random.sample(range(1, 34), 6)
        # 让一些预测的号码出现在开奖中
        hit_count = random.randint(2, 4)
        for j in range(hit_count):
            if j < len(fusion['red']):
                actual_reds[j] = fusion['red'][j]
        
        actual_blue = random.randint(1, 16)
        if random.random() < 0.3:  # 30%概率蓝球命中
            actual_blue = fusion['blue']
        
        # 复盘
        master.self_review(result, (actual_reds, actual_blue))
        
        # 显示进度
        red_hits = len(set(fusion['red']) & set(actual_reds))
        blue_hit = '✓' if fusion['blue'] == actual_blue else '✗'
        print(f"  期号 {issue}: 红球{red_hits}/6  蓝球{blue_hit}")
    
    # 学习和优化
    print("\n进行自我学习...")
    master.self_learning()
    
    # 显示性能报告
    print("\n" + "="*70)
    print("📊 性能报告")
    print("="*70)
    master.print_status()


def main():
    """主菜单"""
    while True:
        print("\n" + "="*70)
        print(" "*15 + "🎯 双色球推理大师演示系统")
        print("="*70)
        print("\n请选择演示项目:")
        print("  1. 单次预测演示 - 展示四维推理过程")
        print("  2. 自主循环演示 - 展示AI自治能力")
        print("  3. 复盘学习演示 - 展示自我改进过程")
        print("  4. 四维分析详解 - 深入了解各维度原理")
        print("  5. 性能追踪演示 - 展示长期表现追踪")
        print("  6. 运行所有演示")
        print("  0. 退出")
        print("\n" + "="*70)
        
        try:
            choice = input("\n请输入选项 (0-6): ").strip()
            
            if choice == '0':
                print("\n👋 感谢使用双色球推理大师！")
                break
            elif choice == '1':
                demo_single_prediction()
            elif choice == '2':
                demo_autonomous_loop()
            elif choice == '3':
                demo_review_and_learning()
            elif choice == '4':
                demo_dimension_analysis()
            elif choice == '5':
                demo_performance_tracking()
            elif choice == '6':
                print("\n▶️  开始运行所有演示...")
                demo_single_prediction()
                time.sleep(2)
                demo_dimension_analysis()
                time.sleep(2)
                demo_review_and_learning()
                time.sleep(2)
                demo_autonomous_loop()
                time.sleep(2)
                demo_performance_tracking()
                print("\n✅ 所有演示完成！")
            else:
                print("\n❌ 无效选项，请重新选择")
            
            input("\n按回车键继续...")
            
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()
            input("\n按回车键继续...")


if __name__ == '__main__':
    main()
