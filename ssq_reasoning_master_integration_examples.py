"""
双色球推理大师与现有系统集成示例

展示如何将双色球推理大师集成到现有系统中
"""

# 示例1: 在命令行菜单中集成
def add_to_cli_menu():
    """
    添加到CLI菜单的示例代码
    可以添加到 activation_persistence.py 或类似的菜单文件中
    """
    menu_text = """
    现有菜单选项...
    
    6. 双色球推理大师 (SSQ Reasoning Master) 🎯
       - 四维推理预测 (周易/统计/量子/AI)
       - AI自主循环学习
       - 预测复盘与优化
    """
    
    # 处理函数
    def handle_ssq_reasoning_master():
        from ssq_reasoning_master_integration import (
            predict_ssq,
            get_ssq_analysis_report,
            run_ssq_autonomous_cycle
        )
        
        while True:
            print("\n" + "="*60)
            print("🎯 双色球推理大师")
            print("="*60)
            print("1. 快速预测")
            print("2. 详细分析报告")
            print("3. 自主循环学习")
            print("4. 查看系统状态")
            print("0. 返回主菜单")
            print("="*60)
            
            choice = input("\n请选择 (0-4): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                from ssq_reasoning_master_integration import get_simple_ssq_prediction
                red, blue = get_simple_ssq_prediction()
                print(f"\n🎲 预测结果:")
                print(f"   红球: {red}")
                print(f"   蓝球: {blue}")
            elif choice == '2':
                report = get_ssq_analysis_report()
                print(report)
            elif choice == '3':
                iterations = input("请输入循环次数 (默认3): ").strip()
                iterations = int(iterations) if iterations.isdigit() else 3
                run_ssq_autonomous_cycle(iterations)
            elif choice == '4':
                from ssq_reasoning_master_integration import get_ssq_status
                import json
                status = get_ssq_status()
                print("\n📊 系统状态:")
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                print("\n❌ 无效选项")
            
            input("\n按回车键继续...")


# 示例2: 在API服务中集成
def add_to_api_server():
    """
    添加到API服务的示例代码
    可以添加到 api_server.py 或类似文件中
    """
    api_code = """
from flask import Flask, jsonify, request
from ssq_reasoning_master_integration import (
    predict_ssq,
    get_simple_ssq_prediction,
    review_ssq_prediction,
    get_ssq_status,
    run_ssq_autonomous_cycle
)

app = Flask(__name__)

@app.route('/api/ssq/predict', methods=['GET'])
def api_ssq_predict():
    '''快速预测接口'''
    try:
        issue = request.args.get('issue', None)
        result = predict_ssq(issue)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ssq/predict/simple', methods=['GET'])
def api_ssq_predict_simple():
    '''简单预测接口 - 只返回红球和蓝球'''
    try:
        red, blue = get_simple_ssq_prediction()
        return jsonify({
            'success': True,
            'data': {
                'red': red,
                'blue': blue
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ssq/review', methods=['POST'])
def api_ssq_review():
    '''复盘接口'''
    try:
        data = request.get_json()
        prediction_result = data.get('prediction_result')
        actual_reds = data.get('actual_reds')
        actual_blue = data.get('actual_blue')
        
        review_result = review_ssq_prediction(
            prediction_result, 
            actual_reds, 
            actual_blue
        )
        
        return jsonify({
            'success': True,
            'data': review_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ssq/status', methods=['GET'])
def api_ssq_status():
    '''状态查询接口'''
    try:
        status = get_ssq_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ssq/auto', methods=['POST'])
def api_ssq_auto():
    '''自主循环接口'''
    try:
        data = request.get_json()
        iterations = data.get('iterations', 1)
        result = run_ssq_autonomous_cycle(iterations)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    """


# 示例3: 在微信服务中集成
def add_to_wechat_server():
    """
    添加到微信服务的示例代码
    可以添加到 wechat_server.py 中
    """
    wechat_code = """
# 在处理微信消息的函数中添加

def handle_wechat_message(msg_content):
    '''处理微信消息'''
    
    # ... 现有的处理逻辑 ...
    
    # 双色球推理大师相关命令
    if '双色球预测' in msg_content or 'ssq' in msg_content.lower():
        from ssq_reasoning_master_integration import get_simple_ssq_prediction
        
        try:
            red, blue = get_simple_ssq_prediction()
            response = f'''🎯 双色球推理大师预测

🔴 红球: {' '.join(map(str, red))}
🔵 蓝球: {blue}

💡 本预测融合四维推理：
• 周易 - 五行八卦
• 统计 - 概率分析
• 量子 - 叠加坍缩
• AI - 模式识别

⚠️ 仅供参考，理性参与'''
            
            return response
            
        except Exception as e:
            return f"预测失败: {str(e)}"
    
    elif '双色球分析' in msg_content:
        from ssq_reasoning_master_integration import get_ssq_analysis_report
        
        try:
            report = get_ssq_analysis_report()
            # 微信消息可能需要截断或分段发送
            return report[:500] + "\\n\\n...（完整报告已生成）"
        except Exception as e:
            return f"分析失败: {str(e)}"
    
    elif '双色球状态' in msg_content:
        from ssq_reasoning_master_integration import get_ssq_status
        
        try:
            status = get_ssq_status()
            response = f'''📊 系统状态

训练次数: {status['training_cycles']}
复盘次数: {status['review_cycles']}
学习次数: {status['learning_cycles']}
'''
            if 'average_red_hits' in status:
                response += f'''
平均红球命中: {status['average_red_hits']:.2f}/6
蓝球命中率: {status['average_blue_hit_rate']:.2%}'''
            
            return response
        except Exception as e:
            return f"状态查询失败: {str(e)}"
    
    # ... 其他处理逻辑 ...
    """


# 示例4: 定时任务集成
def add_to_scheduled_tasks():
    """
    添加定时任务的示例
    可以与 supervisord 或 cron 配合使用
    """
    scheduled_task_code = """
# 每天自动运行一次自主循环学习
# 添加到 crontab:
# 0 2 * * * cd /path/to/-AI-2.0 && python -c "from ssq_reasoning_master_integration import run_ssq_autonomous_cycle; run_ssq_autonomous_cycle(3)"

# 或在 supervisord 配置中添加:
[program:ssq_auto_learning]
command=python -c "import time; from ssq_reasoning_master_integration import run_ssq_autonomous_cycle; 
         while True: run_ssq_autonomous_cycle(3); time.sleep(86400)"
directory=/path/to/-AI-2.0
autostart=true
autorestart=true
stderr_logfile=/var/log/ssq_auto_learning.err.log
stdout_logfile=/var/log/ssq_auto_learning.out.log
    """


# 示例5: 作为现有预测系统的增强
def integrate_with_existing_ssq_system():
    """
    与现有的 ssq_predict_cycle.py 等系统集成
    """
    integration_code = """
# 在 ssq_predict_cycle.py 中集成双色球推理大师

from ssq_reasoning_master_integration import predict_ssq, get_simple_ssq_prediction

class SSQPredictCycleEnhanced:
    def __init__(self):
        # ... 现有初始化代码 ...
        
        # 添加推理大师集成
        self.enable_reasoning_master = True
    
    def predict(self, issue):
        # 现有预测方法
        existing_prediction = self._existing_predict_logic(issue)
        
        if self.enable_reasoning_master:
            # 获取推理大师预测
            try:
                red, blue = get_simple_ssq_prediction()
                
                # 融合两种预测结果
                # 例如：取交集、加权平均等
                combined_red = self._combine_predictions(
                    existing_prediction['red'], 
                    red
                )
                combined_blue = self._select_blue(
                    existing_prediction['blue'], 
                    blue
                )
                
                return {
                    'red': combined_red,
                    'blue': combined_blue,
                    'sources': ['existing_system', 'reasoning_master']
                }
            except Exception as e:
                print(f"推理大师预测失败，使用现有系统: {e}")
                return existing_prediction
        else:
            return existing_prediction
    
    def _combine_predictions(self, pred1, pred2):
        '''组合两个预测结果'''
        # 简单策略：取交集 + 补充
        common = list(set(pred1) & set(pred2))
        
        if len(common) >= 6:
            return sorted(common[:6])
        
        # 补充缺失的号码
        all_nums = list(set(pred1 + pred2))
        result = common + [n for n in all_nums if n not in common][:6-len(common)]
        return sorted(result[:6])
    
    def _select_blue(self, blue1, blue2):
        '''选择蓝球'''
        # 简单策略：随机选择或根据置信度选择
        import random
        return random.choice([blue1, blue2])
    """


def main():
    """
    主函数 - 展示所有集成示例
    """
    print("="*70)
    print(" "*15 + "双色球推理大师集成示例")
    print("="*70)
    print("\n本文件展示了如何将双色球推理大师集成到现有系统中")
    print("\n集成方式:")
    print("1. CLI菜单集成 - 添加命令行选项")
    print("2. API服务集成 - 提供RESTful接口")
    print("3. 微信服务集成 - 响应微信消息")
    print("4. 定时任务集成 - 自动学习优化")
    print("5. 现有系统增强 - 作为预测增强模块")
    print("\n详细代码请查看本文件中的各个示例函数")
    print("="*70)


if __name__ == '__main__':
    main()
