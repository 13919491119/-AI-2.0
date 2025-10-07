# 玄机AI 3.0 投资组合配置自动生成脚本
# 由分析报告 analysis_report.txt 自动生成

investment_portfolios = {
    "🎯 重点投资组合": {
        "groups": [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 18, 19],
        "allocation": "50%资金",
        "risk_level": "中等",
        "expected_return": "高",
        "description": "综合评分0.9及以上的优选组合，均衡度高，分散度高"
    },
    "✅ 适度配置组合": {
        "groups": [6, 7, 8, 9, 17, 20, 21, 22, 23, 24, 28, 30, 31],
        "allocation": "30%资金",
        "risk_level": "中低",
        "expected_return": "中等",
        "description": "评分在0.75-0.89之间的优质组合，风险适中"
    },
    "📊 其他配置组合": {
        "groups": [10, 25, 26, 27, 29],
        "allocation": "20%资金",
        "risk_level": "分散",
        "expected_return": "多样化",
        "description": "剩余组合，提供更全面的号码覆盖"
    }
}

# 解析 analysis_report.txt 生成分析结果结构
def parse_analysis_report(filename):
    results = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    group_id = 0
    for i, line in enumerate(lines):
        if line.startswith('第') and '组' in line:
            group_id += 1
            red = eval(line.split('红球[')[1].split(']')[0])
            blue = int(line.split('蓝球:')[1].strip())
            score_line = lines[i+4] if i+4 < len(lines) else ''
            score = float(score_line.split('综合评分:')[1].strip()) if '综合评分:' in score_line else 0.0
            # 评级
            if score >= 0.9:
                rating = '★★★★★'
            elif score >= 0.8:
                rating = '★★★★'
            elif score >= 0.7:
                rating = '★★★'
            elif score >= 0.6:
                rating = '★★'
            else:
                rating = '★'
            results.append({
                'group_id': group_id,
                'numbers': {'red': red, 'blue': blue},
                'overall_score': score,
                'rating': rating
            })
    return results

def generate_investment_plan(portfolios, number_groups):
    print("🎯 玄机AI系统3.0 - 投资组合优化配置")
    print("=" * 70)
    for portfolio_name, portfolio_info in portfolios.items():
        print(f"\n{portfolio_name}")
        print("-" * 50)
        print(f"📊 资金分配: {portfolio_info['allocation']}")
        print(f"⚠️  风险等级: {portfolio_info['risk_level']}")
        print(f"📈 预期回报: {portfolio_info['expected_return']}")
        print(f"📝 组合描述: {portfolio_info['description']}")
        print(f"\n🔢 包含组号: {portfolio_info['groups']}")
        print("具体号码:")
        for group_id in portfolio_info['groups']:
            group_data = next((g for g in number_groups if g.get('group_id') == group_id), None)
            if group_data:
                numbers = group_data['numbers']
                score = group_data['overall_score']
                rating = group_data['rating']
                print(f"   第{group_id:2d}组: 红球{numbers['red']} + 蓝球{numbers['blue']:2d} | 评分:{score:.3f} {rating}")
    total_groups = sum(len(portfolio['groups']) for portfolio in portfolios.values())
    print(f"\n📈 总体统计:")
    print(f"   总组数: {total_groups}组")
    print(f"   资金分配: 50% + 30% + 20% = 100%")
    print(f"   风险分散: 高中低三档风险平衡")

def calculate_portfolio_performance(portfolios, number_groups):
    print(f"\n📊 投资组合表现分析")
    print("-" * 50)
    for portfolio_name, portfolio_info in portfolios.items():
        group_scores = []
        for group_id in portfolio_info['groups']:
            group_data = next((g for g in number_groups if g.get('group_id') == group_id), None)
            if group_data:
                group_scores.append(group_data['overall_score'])
        if group_scores:
            avg_score = sum(group_scores) / len(group_scores)
            max_score = max(group_scores)
            min_score = min(group_scores)
            print(f"{portfolio_name}:")
            print(f"   平均评分: {avg_score:.3f}")
            print(f"   最高评分: {max_score:.3f}")
            print(f"   最低评分: {min_score:.3f}")
            print(f"   组合稳定性: {'高' if (max_score - min_score) < 0.1 else '中' if (max_score - min_score) < 0.2 else '低'}")

def generate_investment_advice():
    print(f"\n💡 投资执行建议")
    print("-" * 50)
    advice_points = [
        "🎯 重点投资组合 - 投入50%资金，这是核心盈利来源",
        "✅ 适度配置组合 - 投入30%资金，平衡风险与收益",
        "📊 其他配置组合 - 投入20%资金，实现全面号码覆盖",
        "💰 建议每期固定投入金额，避免情绪化投资",
        "📈 定期回顾组合表现，每季度重新评估一次",
        "🛡️ 设置止损线，单期损失不超过总投入的20%",
        "🎲 保持理性心态，彩票本质是概率游戏"
    ]
    for advice in advice_points:
        print(f"   • {advice}")

if __name__ == "__main__":
    print("开始生成投资组合配置...\n")
    analysis_results = parse_analysis_report("analysis_report.txt")
    generate_investment_plan(investment_portfolios, analysis_results)
    calculate_portfolio_performance(investment_portfolios, analysis_results)
    generate_investment_advice()
    print(f"\n🎉 投资组合配置完成！")
    print("=" * 70)
    print("建议按照上述配置执行投资，祝您好运！🍀")
