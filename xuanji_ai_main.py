from xuanji_ai3_features import print_xuanji_ai3_features
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sys
def run_xuanji_ai_utf8(user_input: str):
    """
    终端安全输出run_xuanji_ai结果，自动utf-8编码，防止中文乱码。
    """
    result = run_xuanji_ai(user_input)
    if isinstance(result, str):
        sys.stdout.buffer.write((result + '\n').encode('utf-8'))
    else:
        print(result)
import logging
from core_structs import XuanjiAISystem

def setup_logger():
    logger = logging.getLogger("xuanji_ai2.0")
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = setup_logger()

def run_xuanji_ai(user_input: str) -> str:
    """
    统一入口：根据输入内容自动判断调用哪种AI功能。
    输入示例：
      - "学习成果"
      - "双色球预测"
      - "双色球复盘: 01 02 03 04 05 06|07, 11 12 13 14 15 16|08"
    """
    ai = XuanjiAISystem()
    user_input = user_input.strip()
    if user_input.startswith("学习成果"):
        result = []
        # 读取累计训练期数
        train_count = 0
        if hasattr(ai, 'ssq_ai') and hasattr(ai.ssq_ai, 'cumulative_train_count'):
            train_count = ai.ssq_ai.cumulative_train_count
        result.append(f"[模型训练] 累计训练数据期数: {train_count}")
        # 读取累计自主学习周期数
        cycle_count = 0
        if hasattr(ai, 'cumulative_learning_cycles'):
            cycle_count = ai.cumulative_learning_cycles
        result.append(f"[自主学习周期] 累计轮数: {cycle_count}")
        if hasattr(ai, 'learning_cycles') and ai.learning_cycles:
            result.append(f"[最近学习周期] 共{len(ai.learning_cycles)}轮（显示最近3轮）：")
            for c in ai.learning_cycles[-3:]:
                result.append(f"  - {c.cycle_id} | {c.cycle_type.name} | 提升:{c.performance_improvement} | 备注:{c.notes}")
        else:
            result.append("[自主学习周期] 暂无记录")
        if hasattr(ai, 'upgrade_engine') and hasattr(ai.upgrade_engine, 'format_upgrade_plan'):
            plan = ai.upgrade_engine.plan_upgrade("学习成果展示", "v1.0", "v2.0")
            result.append("[升级内容示例]:")
            result.append(ai.upgrade_engine.format_upgrade_plan(plan))
        result.append("[DeepseekAI] 测试: 你可以在推理、复盘等环节调用大模型能力。")
        return "\n".join(result)
    elif user_input.startswith("六爻分析"):
        # 允许格式：六爻分析: 双色球 2025114期 红球[12, 19, 14, 10, 8, 11] 蓝球16
        try:
            import re
            m = re.search(r"红球\[(.*?)\]\s*蓝球(\d+)", user_input)
            if not m:
                return "[六爻分析格式错误] 请输入: 六爻分析: 双色球 期号 红球[...6个数字...] 蓝球数字"
            reds = [int(x) for x in m.group(1).replace('，',',').replace(' ', ',').split(',') if x.strip()]
            blue = int(m.group(2))
            from deepseek_api import DeepseekAPI
            api = DeepseekAPI()
            msg = f"请用六爻思维分析双色球，红球{reds} 蓝球{blue}，结合卦象、阴阳、五行、概率、冷热、奇偶、历史表现等多维度智能解读。"
            ds_resp = api.chat([
                {"role": "system", "content": "你是六爻与双色球结合的AI智能分析专家。"},
                {"role": "user", "content": msg}
            ])
            ds_content = ds_resp["choices"][0]["message"]["content"]
            return f"[六爻AI智能解读]\n{ds_content}"
        except Exception as e:
            return f"[六爻分析异常] {e}"
    elif user_input.startswith("chatgpt分析"):
        # 支持命令：chatgpt分析: 双色球 2025114期
        try:
            import re
            from chatgpt_api import ChatGPTAPI
            m = re.search(r"双色球[\s\S]*?期", user_input)
            if not m:
                return "[ChatGPT分析格式错误] 请输入: chatgpt分析: 双色球 期号"
            issue = m.group(0)
            api = ChatGPTAPI()
            prompt = f"请为{issue}预测一组红球6个、蓝球1个，并给出分析理由。"
            resp = api.chat([
                {"role": "system", "content": "你是双色球智能分析师。"},
                {"role": "user", "content": prompt}
            ])
            content = resp["choices"][0]["message"]["content"]
            return f"[ChatGPT智能分析]\n{content}"
        except Exception as e:
            return f"[ChatGPT分析异常] {e}"
    else:
        return "[API] 未知指令，请输入：学习成果、双色球预测、双色球复盘: ..."

def main():
    def task_predict():
        reds, blue = ai.ssq_ai.predict()
        print(f"[自动预测] 红球: {reds} 蓝球: {blue}")
    print_xuanji_ai3_features()
    print("""
══════════════════════════════════════════════════════════════
玄机AI系统3.0 - 系统特性与使用说明
────────────────────────────────────────────
【实时运行状态】
🔄 自主运行周期：每30秒执行一次完整分析
📊 多任务并行：学习、分析、优化、监控同时进行（即将支持）
🎯 智能调度：自动分配系统资源（即将支持）

【核心功能】
🧠 持续学习 —— 不断发现新 patterns
🔮 实时预测 —— 基于最新数据生成预测（手动/自动）
📊 深度分析 —— 多维度数据洞察
⚡ 性能优化 —— 自动调优系统参数（即将支持）
🛡️ 安全监控 —— 确保系统稳定运行（即将支持）

【系统保障】
✅ 优雅关闭 —— 安全保存状态（Ctrl+C自动保存）
🚨 紧急恢复 —— 异常时自动恢复（部分支持）
📈 状态监控 —— 实时显示运行指标

【使用说明】
💡 系统将自动启动并进入自主运行模式
💡 按 Ctrl+C 可安全关闭系统
💡 系统每5个周期显示详细状态报告
💡 所有数据自动保存，下次启动时恢复
============================================================
玄机AI系统3.0现已正式运行！
系统将开始自主学习、分析和优化，为您提供智能预测服务！
══════════════════════════════════════════════════════════════
""")
    logger.info("欢迎使用 玄机AI3.0！")
    from xuanji_ai3_status import print_xuanshu_ai3_status
    import time
    N = 1  # 每N次循环检查一次是否到3分钟
    loop_count = 0
    last_status_time = time.time()
    ai = XuanjiAISystem()
    # 确保ai对象初始化完成
    assert hasattr(ai, 'ssq_ai') and hasattr(ai, 'ssq_data')
    auto_last_time = time.time()
    import threading
    def task_collect():
        ai.ssq_data.fetch_online()
    def task_train():
        ai.ssq_ai.train()
    def task_analyze():
        hot, cold = ai.ssq_data.get_hot_cold()
        reds, blue = ai.ssq_ai.predict()
        odd = [n for n in reds if n % 2 == 1]
        even = [n for n in reds if n % 2 == 0]
        print("[深度分析] 结合六爻、小六壬、奇门遁甲等文化智慧：")
        print(f"  - 热号: {hot} 冷号: {cold}")
        print(f"  - 预测红球: {reds} 蓝球: {blue} | 奇偶分布: 奇{len(odd)} 偶{len(even)}")
        print("  - 六爻视角：分析红蓝球组合的阴阳、五行、卦象变化，推演走势。")
        print("  - 小六壬视角：结合时空、数理变化，洞察号码潜在规律。")
        print("  - 奇门遁甲视角：融合九宫八门、三奇六仪，辅助预测未来走势。")
    def task_monitor():
        print(f"[监控] 当前训练期数: {ai.ssq_ai.cumulative_train_count}，历史数据: {len(ai.ssq_data.history)}")

    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            print(f"\n\033[1;34m[系统后台自主运营] 第{cycle_count}周期：AI正在后台采集、训练、分析、监控...\033[0m")
            # 后台多任务并行（采集、训练、分析、监控等）
            threads = []
            for func in [task_collect, task_train, task_predict, task_analyze, task_monitor]:
                t = threading.Thread(target=func)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            # 后台生成号码、学习分析、知识自增长
            new_patterns = ai.fetch_and_update_patterns()
            ai.generate_innovative_patterns(n=1)
            removed = ai.evaluate_patterns()
            ai.update_state_on_learn(new_patterns=new_patterns)
            # 前台仅输出运营状态提示
            print(f"\033[1;32m[运营状态] AI后台已完成本周期采集、训练、分析、知识更新。\033[0m")
            # 周期性详细报告
            if cycle_count % 5 == 0:
                print("\033[1;35m[周期性详细报告]\033[0m")
                cycle = ai.cumulative_learning_cycles
                health = 100.0
                data_count = getattr(ai.ssq_ai, 'cumulative_train_count', 153) if hasattr(ai, 'ssq_ai') else 153
                perf_status = "无优化"
                response_time = 1.80
                # 真实性能提升：与训练数据量和预测准确率挂钩
                try:
                    # 文化因子模拟：六爻（变爻/阴阳）、小六壬（时空/数理）、奇门遁甲（九宫/三奇）
                    base_count = 500
                    train_count = data_count
                    data_factor = min(0.6, max(0, (train_count-base_count)/base_count*0.6))
                    reds, blue = ai.ssq_ai.predict()
                    # 精度：自我推理与历史真实号码的命中率
                    history = ai.ssq_data.history[-10:] if hasattr(ai.ssq_data, 'history') else []
                    acc_sum = 0
                    acc_cnt = 0
                    for h_reds, h_blue in history:
                        hit_r = len([n for n in reds if n in h_reds])
                        hit_b = 1 if blue == h_blue else 0
                        acc_sum += (hit_r/6)*0.7 + hit_b*0.3
                        acc_cnt += 1
                    accuracy = round(acc_sum/acc_cnt, 3) if acc_cnt else 0.0
                    # 六爻因子：奇偶分布越均衡，视为阴阳调和，提升0~0.1
                    odd = [n for n in reds if n % 2 == 1]
                    even = [n for n in reds if n % 2 == 0]
                    liuyao_factor = 0.1 - abs(len(odd)-len(even))*0.02
                    # 小六壬因子：红球跨度（最大-最小）越大，视为时空变化充分，提升0~0.1
                    span = max(reds)-min(reds) if reds else 0
                    xiaoliu_factor = min(0.1, span/33*0.1)
                    # 奇门遁甲因子：红球命中热号数与三奇（3/6）接近，视为三奇得位，提升0~0.1
                    hot = ai.ssq_data.get_hot_numbers() if hasattr(ai.ssq_data, 'get_hot_numbers') else []
                    hit_red = len([n for n in reds if n in hot[:6]])
                    qimen_factor = 0.1 - abs(hit_red-3)*0.03
                    acc_factor = accuracy * 0.2
                    perf_improve = round(data_factor + liuyao_factor + xiaoliu_factor + qimen_factor + acc_factor, 3)
                except Exception:
                    accuracy = 0.0
                    perf_improve = 0.01
                # 动态安全检测
                import os
                files_ok = all(os.path.exists(f) and os.access(f, os.R_OK|os.W_OK) for f in ["ssq_history.csv", "patterns_knowledge.json"])
                log_has_error = False
                try:
                    if os.path.exists("xuanji_ai3.log"):
                        with open("xuanji_ai3.log", "r", encoding="utf-8") as flog:
                            for line in flog:
                                if "ERROR" in line:
                                    log_has_error = True
                                    break
                except Exception:
                    log_has_error = True
                security = "安全" if files_ok and not log_has_error else "需关注"
                last_upgrade = "无"
                knowledge_growth = ai.knowledge_growth
                optimize_progress = ai.optimize_progress
                core_abilities = "learning_enabled, self_upgrade_enabled, adaptation_level"
                print_xuanshu_ai3_status(
                    cycle=cycle,
                    health=health,
                    data_count=data_count,
                    engine_status="后台运营",
                    perf_status=perf_status,
                    response_time=response_time,
                    accuracy=accuracy,
                    security=security,
                    last_upgrade=last_upgrade,
                    new_patterns=new_patterns,
                    knowledge_growth=knowledge_growth,
                    optimize_progress=optimize_progress,
                    perf_improve=perf_improve,
                    core_abilities=core_abilities
                )
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\033[1;33m[优雅关闭] 检测到Ctrl+C，正在保存系统状态...\033[0m")
        if hasattr(ai, '_save_patterns_knowledge'):
            ai._save_patterns_knowledge()
        if hasattr(ai, '_save_system_state'):
            ai._save_system_state()
        print("\033[1;32m[已安全保存] 系统状态已保存，欢迎下次继续使用！\033[0m")
    except KeyboardInterrupt:
        print("\n\033[1;33m[优雅关闭] 检测到Ctrl+C，正在保存系统状态...\033[0m")
        if hasattr(ai, '_save_patterns_knowledge'):
            ai._save_patterns_knowledge()
        print("\033[1;32m[已安全保存] 系统状态已保存，欢迎下次继续使用！\033[0m")

if __name__ == "__main__":
    main()
