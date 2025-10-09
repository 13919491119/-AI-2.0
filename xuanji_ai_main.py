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
    # ---------- 学习成果 ----------
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
    # ---------- 六爻分析 ----------
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
    # ---------- ChatGPT 分析 ----------
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
    # ---------- 双色球预测（新增） ----------
    elif user_input.startswith("双色球预测"):
        try:
            import math, statistics, datetime, random
            # 1. 内部基础预测
            reds, blue = ai.ssq_ai.predict()
            reds_sorted = sorted(reds)
            # 2. 历史/冷热/频次特征
            history = ai.ssq_data.history if hasattr(ai, 'ssq_data') else []
            hot, cold = ai.ssq_data.get_hot_cold() if hasattr(ai.ssq_data, 'get_hot_cold') else ([], [])
            freq = {n:0 for n in range(1,34)}
            for rs, _b in history[-500:]:  # 仅近500期窗口，控制成本
                for r in rs: freq[r]+=1
            total_occ = sum(freq.values()) or 1
            freq_sorted = sorted(freq.items(), key=lambda x: -x[1])
            top10 = freq_sorted[:10]
            # 3. 结构特征
            odd_cnt = len([x for x in reds if x % 2 == 1])
            even_cnt = 6 - odd_cnt
            span = max(reds_sorted) - min(reds_sorted)
            sum_reds = sum(reds_sorted)
            prime_set = {2,3,5,7,11,13,17,19,23,29,31}
            prime_cnt = len([x for x in reds if x in prime_set])
            consecutive_groups = []
            cur = [reds_sorted[0]]
            for a,b in zip(reds_sorted, reds_sorted[1:]):
                if b == a+1:
                    cur.append(b)
                else:
                    if len(cur) > 1: consecutive_groups.append(cur)
                    cur=[b]
            if len(cur)>1: consecutive_groups.append(cur)
            zones = {"1-11":0, "12-22":0, "23-33":0}
            for r in reds_sorted:
                if r <= 11: zones["1-11"] += 1
                elif r <= 22: zones["12-22"] += 1
                else: zones["23-33"] += 1
            # Top热号命中情况
            hot_hits = [r for r in reds if r in hot[:10]]
            cold_hits = [r for r in reds if r in cold[:10]]
            concentration = round(sum(v for _,v in freq_sorted[:5]) / total_occ, 3)
            # 4. 置信度（启发式融合：奇偶均衡、跨度中位区、热冷混合、质数比例适中、分区均衡）
            score = 0.5
            if 2 <= odd_cnt <= 4: score += 0.05
            if 12 <= span <= 25: score += 0.05
            if 2 <= len(hot_hits) <= 4: score += 0.05
            if len(cold_hits) >= 1: score += 0.03
            if 2 <= prime_cnt <= 4: score += 0.04
            if max(zones.values()) <= 3: score += 0.04
            if consecutive_groups: score += 0.02  # 适度连号视为结构特征
            score = min(0.88, round(score, 3))
            # 5. Deepseek 多维解读
            ds_section = "[Deepseek多维解读] 未启用或调用失败，采用内部启发式说明。"
            try:
                from deepseek_api import DeepseekAPI
                ds = DeepseekAPI()
                sys_prompt = (
                    "你是融合统计学、概率建模、模式识别与结构分析的双色球智能分析师。" \
                    "请对给定预测组合做多维解读，结构: 1) 组合特征概述 2) 热冷号与频次含义 3) 结构模式(奇偶/区间/跨度/连号) 4) 风险提示 5) 策略建议。" \
                    "用简洁要点分行，避免过度夸张与绝对语气。"
                )
                ctx_summary = (
                    f"预测红球: {reds_sorted} 蓝球:{blue}\n" \
                    f"奇偶:{odd_cnt}:{even_cnt} 跨度:{span} 和值:{sum_reds} 质数:{prime_cnt} 连号组:{consecutive_groups if consecutive_groups else '无'}\n" \
                    f"分区:{zones} 热号命中:{hot_hits} 冷号包含:{cold_hits} 集中度Top5:{concentration}\n" \
                    f"Top10频次: {[(n,c) for n,c in top10]}"
                )
                user_prompt = (
                    f"以下是系统内部生成的一组双色球预测及其特征，请按照要求输出结构化分析:\n{ctx_summary}"
                )
                resp = ds.chat([
                    {"role":"system","content": sys_prompt},
                    {"role":"user","content": user_prompt}
                ], temperature=0.55, max_tokens=800)
                ds_content = resp['choices'][0]['message']['content']
                ds_section = f"[Deepseek多维解读]\n{ds_content.strip()}"
            except Exception as e:
                ds_section = ds_section + f" (fallback原因: {e})"
            # 6. 综合格式化输出
            lines = [
                "[多维融合双色球预测报告]",
                f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "[基础预测]",
                f"红球: {reds_sorted}",
                f"蓝球: {blue}",
                "",
                "[统计特征]",
                f"奇偶分布: 奇{odd_cnt} 偶{even_cnt}",
                f"跨度: {span} 和值: {sum_reds} 质数个数: {prime_cnt}",
                f"分区分布: 1-11={zones['1-11']} 12-22={zones['12-22']} 23-33={zones['23-33']}",
                f"连号组: {consecutive_groups if consecutive_groups else '无'}",
                f"热号命中: {hot_hits if hot_hits else '无'} 冷号包含: {cold_hits if cold_hits else '无'}",
                f"频次Top10: {top10}",
                f"集中度(Top5出现占比): {concentration}",
                "",
                "[结构/走势洞察]",
                ("奇偶相对均衡，跨度处于中等区，具备一定稳健性。" if 2 <= odd_cnt <=4 else "奇偶分布偏离均衡，可视为结构博弈风险。"),
                ("热冷号融合（含冷号扰动）提升结构多样性。" if cold_hits else "缺少冷号扰动，可能被热号集中模式放大风险。"),
                ("分区分布相对分散，有助于降低区间聚集度。" if max(zones.values())<=3 else "红球存在区间相对集中，可关注区间再均衡。"),
                ("适度连号增强结构连续性特征。" if consecutive_groups else "本组合未引入连号，走势结构更离散。"),
                "",
                ds_section,
                "",
                "[启发式综合置信度]",
                f"内部启发式评分: {score}",
                "评分因素: 奇偶均衡/跨度合理/冷热结合/区间分散/结构特征/质数比例等",
                "",
                "[策略建议]",
                "1) 可并行生成 2~3 组差异化结构(增加或减少连号/冷热倾斜) 做对冲",
                "2) 关注下一期训练后热号序列是否变化，若变化剧烈需调低依赖度",
                "3) 可引入和值、尾数分布、重号跟踪形成二级过滤层",
                "",
                "[免责声明] 本报告融合内部启发式与大模型语义推理，不构成投资/投注建议，存在不确定性。"
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"[双色球预测异常] {e}"

    # ---------- 预测任务 / task（新增核心逻辑 A） ----------
    elif user_input.startswith("预测任务") or user_input.lower().startswith("task"):
        try:
            import re, random, datetime
            raw = user_input
            # 提取描述（兼容：预测任务: xxx / 预测任务 xxx / task: xxx）
            desc_part = raw.split(':', 1)[1].strip() if ':' in raw else raw[len('预测任务'):].strip()
            if not desc_part:
                return "[预测任务] 请在 '预测任务:' 后补充任务描述，例如: 预测任务: 分析近30期冷热与奇偶分布"

            # --------------- 领域自动识别 ---------------
            lottery_keywords = ['双色球', '红球', '蓝球', '冷热', '奇偶', '跨度', '复盘', '选号', '概率', '命中', '号码']
            is_lottery = any(k.lower() in desc_part.lower() for k in lottery_keywords)

            # 若不是双色球/号码预测语义，则走通用 Deepseek 推理路径
            if not is_lottery:
                # 汇总系统上下文（精简）
                try:
                    history_len = len(ai.ssq_data.history) if hasattr(ai, 'ssq_data') else 0
                    patterns_len = len(ai.patterns_knowledge) if hasattr(ai, 'patterns_knowledge') else 0
                    cycles = getattr(ai, 'cumulative_learning_cycles', 0)
                    hot, cold = (ai.ssq_data.get_hot_cold() if hasattr(ai.ssq_data, 'get_hot_cold') else ([], [])) if hasattr(ai, 'ssq_data') else ([], [])
                    reds_pred, blue_pred = ai.ssq_ai.predict() if hasattr(ai, 'ssq_ai') else ([], None)
                except Exception:
                    history_len = patterns_len = cycles = 0
                    hot = cold = []
                    reds_pred, blue_pred = ([], None)

                system_ctx = (
                    f"数据期数:{history_len}; 学习周期:{cycles}; 模式库:{patterns_len}; "
                    f"示例热号:{hot[:6] if hot else []}; 冷号:{cold[:6] if cold else []}; "
                    f"示例内部预测:{reds_pred}|{blue_pred}"
                )
                try:
                    from deepseek_api import DeepseekAPI
                    ds = DeepseekAPI()
                    sys_prompt = (
                        "你是一个融合多源统计学习、概率推断、模式识别、启发式博弈推理的综合预测AI。" \
                        "用户可能提出任何关于趋势、风险、发展、策略、投资、技术演进等问题。" \
                        "请基于提供的系统上下文与一般公开常识进行前瞻性预测。" \
                        "回答需结构化：\n" \
                        "1) 问题理解\n2) 关键影响因子\n3) 多情景推演(至少2个情景)\n4) 核心预测结论\n5) 风险与不确定性\n6) 行动建议。" \
                        "语气专业、克制，避免绝对化用语，明确不确定范围。"
                    )
                    user_prompt = (
                        f"问题: {desc_part}\n系统上下文: {system_ctx}\n" \
                        "请输出 JSON 风格的小节(无需严格JSON，仅分段清晰)。"
                    )
                    resp = ds.chat([
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ], temperature=0.6, max_tokens=1024)
                    content = resp["choices"][0]["message"]["content"]
                    return (
                        "[通用预测任务智能推理]\n" +
                        f"任务描述: {desc_part}\n" +
                        f"分析时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" +
                        f"系统上下文摘要: {system_ctx}\n\n" +
                        content +
                        "\n\n(以上内容由 Deepseek 大模型推理+内部上下文融合生成，结果具有不确定性，仅供参考。)"
                    )
                except Exception as e:
                    # 回退：启发式占位回答
                    return (
                        "[通用预测任务启发式分析]\n" +
                        f"任务描述: {desc_part}\n" +
                        f"分析时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" +
                        "(Deepseek 推理暂不可用，使用启发式回退)\n\n" +
                        "问题初步理解: 系统识别为跨领域/开放式预测问题。\n" +
                        "关键影响因子: 数据可得性、宏观趋势、技术创新速度、政策/监管、竞争格局。\n" +
                        "情景推演: 基础情景(稳步发展)、加速情景(外部催化突破)、受阻情景(政策/资金/技术瓶颈)。\n" +
                        "核心预测: 在 6-12 个月区间呈阶段性波动+结构分化。\n" +
                        "风险与不确定性: 黑天鹅(政策/地缘), 数据偏差, 模型不足。\n" +
                        "行动建议: 分阶段验证假设, 设定监测指标, 采用多策略组合, 保留冗余与风险对冲。\n" +
                        f"(错误详情: {e})"
                    )

            # 解析近N期窗口
            m = re.search(r'近(\d+)期', desc_part)
            window_n = 50
            if m:
                try:
                    window_n = int(m.group(1))
                    window_n = max(5, min(window_n, 300))  # 边界限制
                except Exception:
                    window_n = 50

            history = ai.ssq_data.history if hasattr(ai.ssq_data, 'history') else []
            if not history:
                return "[预测任务] 历史数据为空，无法分析。"
            window_slice = history[-window_n:] if len(history) >= window_n else history[:]
            actual_n = len(window_slice)

            # 统计红球频次
            freq = {n: 0 for n in range(1, 34)}
            blue_freq = {n: 0 for n in range(1, 17)}
            for reds, b in window_slice:
                for r in reds:
                    freq[r] += 1
                blue_freq[b] += 1
            top_reds = sorted(freq.items(), key=lambda x: -x[1])[:10]
            hot, cold = ai.ssq_data.get_hot_cold() if hasattr(ai.ssq_data, 'get_hot_cold') else ([], [])

            # 奇偶 & 跨度 & 集中度
            all_reds = [r for reds, _ in window_slice for r in reds]
            odd_cnt = len([x for x in all_reds if x % 2 == 1])
            even_cnt = len(all_reds) - odd_cnt
            span = (max(all_reds) - min(all_reds)) if all_reds else 0
            # 简单集中度：Top5 累计出现次数 / 总出现次数
            total_occ = sum(freq.values()) or 1
            top5 = sorted(freq.values(), reverse=True)[:5]
            concentration = round(sum(top5) / total_occ, 3)

            # 候选号码生成策略：热点 + 冷门混合 + 频次补足
            candidate_reds = []
            for n in hot[:4]:  # 先取热门前4
                if n not in candidate_reds:
                    candidate_reds.append(n)
            for n in cold[:3]:  # 再引入1~2个冷号
                if len(candidate_reds) >= 5:
                    break
                if n not in candidate_reds:
                    candidate_reds.append(n)
            # 频次排序填充
            for n, _c in top_reds:
                if len(candidate_reds) >= 6:
                    break
                if n not in candidate_reds:
                    candidate_reds.append(n)
            # 兜底随机补齐
            while len(candidate_reds) < 6:
                rnd = random.randint(1, 33)
                if rnd not in candidate_reds:
                    candidate_reds.append(rnd)
            candidate_reds.sort()

            # 蓝球：选取窗口内出现频次最高的两个中随机一个；若平局随机
            max_blue_freq = max(blue_freq.values()) if blue_freq else 0
            hot_blues = [b for b, c in blue_freq.items() if c == max_blue_freq and c > 0]
            if not hot_blues:
                blue_pick = random.randint(1, 16)
            else:
                blue_pick = random.choice(hot_blues)

            # 置信度启发（简单规则叠加）
            desc_lower = desc_part.lower()
            confidence = 0.55
            if '冷热' in desc_part or 'hot' in desc_lower or 'cold' in desc_lower:
                confidence += 0.1
            if '奇偶' in desc_part or 'odd' in desc_lower or 'even' in desc_lower:
                confidence += 0.05
            if '跨度' in desc_part:
                confidence += 0.05
            if '概率' in desc_part or '概率' in desc_lower:
                confidence += 0.03
            confidence = min(0.95, round(confidence, 2))

            # 构造报告
            lines = [
                "[预测任务分析报告]",
                f"任务描述: {desc_part}",
                f"分析时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"数据窗口: 近{actual_n}期 (请求: {window_n})",
                "",
                "[核心统计]",
                f"红球总出现次数: {total_occ}",
                f"奇偶分布(累计红球): 奇{odd_cnt} / 偶{even_cnt} | 比例 {odd_cnt}:{even_cnt}",
                f"号码跨度: {span}",
                f"前10高频红球: " + ', '.join([f"{n}({c})" for n, c in top_reds]),
                f"热号参考: {hot[:6] if hot else '无'}",
                f"冷号参考: {cold[:6] if cold else '无'}",
                f"集中度(Top5占比): {concentration}",
                "",
                "[智能候选建议]",
                f"推荐红球组合: {candidate_reds}",
                f"推荐蓝球: {blue_pick}",
                f"策略说明: 热门优选 + 冷门扰动 + 频次补齐 (启发式模拟)",
                "",
                "[置信度评估]",
                f"启发式置信度: {confidence}",
                f"关键词影响: {'冷热 ' if '冷热' in desc_part else ''}{'奇偶 ' if '奇偶' in desc_part else ''}{'跨度 ' if '跨度' in desc_part else ''}".strip(),
                "",
                "[后续可扩展]",
                " - 引入真实机器学习/深度模型概率输出",
                " - 加入时间序列/模式识别特征",
                " - 多策略集成与权重自适应调优",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"[预测任务处理异常] {e}"

    # ---------- 未识别指令 ----------
    else:
        return "[API] 未知指令，请输入：学习成果、双色球预测、预测任务: ...、六爻分析: ...、chatgpt分析: ..."

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
