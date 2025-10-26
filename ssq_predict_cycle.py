
from __future__ import annotations
# 集成批量复盘与学习升级功能
def batch_replay_learn():
    import subprocess
    try:
        print("[自动复盘] 正在批量复盘与模型学习升级...")
        subprocess.run(['python3', 'ssq_batch_replay_learn.py'], check=True)
        print("[自动复盘] 批量复盘与学习升级已完成。")
    except Exception as e:
        print(f"[自动复盘] 批量复盘失败: {e}")

# 可在主循环或定时任务中调用 batch_replay_learn()
"""
双色球多模型预测闭环主控
支持：小六爻、小六壬、奇门遁甲、AI模型预测
自动循环、匹配度评估、完全匹配告警、特征融合与自主学习

新增：
- 连续闭环执行（按期次循环直至匹配或达到安全上限）
- 预测尝试日志与策略统计
- 启发式融合、随机兜底与 DeepSeek 智能建议
- 报告持久化（JSON/Markdown）
"""

import json
import os
import random
import re
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

from ssq_data import SSQDataManager
from ssq_ai_model import SSQAIModel
from cultural_predictor import CulturalPredictor
from cultural_deep_model import CulturalDeepModel
try:
    from deepseek_api import DeepseekAPI  # type: ignore
except Exception:  # 导入失败时保持占位，运行时再降级
    DeepseekAPI = None  # type: ignore

class SSQPredictCycle:
    def __init__(self, data_path: str):
        self.data_manager = SSQDataManager(csv_path=data_path)
        self.ai_model = SSQAIModel(self.data_manager)
        self.history = self.data_manager.history
        self.models = ['liuyao', 'liuren', 'qimen', 'ai', 'cultural_dl']
        self._last_fusion_trace = None  # 保存最近一次融合的权重/先验轨迹，便于报告与审计
        self.match_log: List[Dict[str, object]] = []
        self.loop_attempts: List[Dict[str, object]] = []
        self.issue_states: Dict[int, Dict[str, object]] = {}
        self._deepseek_client: Optional[object] = None
        self._cultural_dl: Optional[CulturalDeepModel] = None
        self._cultural_dl_path = os.getenv('SSQ_CULDL_PATH', 'models/cultural_deep.joblib')

        # 可配置融合参数（通过环境变量覆盖）
        self.alpha_red = self._get_env_float('SSQ_ALPHA_RED', 0.1, 0.0, 1.0)
        self.alpha_blue = self._get_env_float('SSQ_ALPHA_BLUE', 0.1, 0.0, 1.0)
        self.enforce_region_coverage = self._get_env_bool('SSQ_REGION_COVERAGE', True)
        self.region_buckets = self._parse_region_buckets(
            os.getenv('SSQ_REGION_BUCKETS', '1-11,12-22,23-33')
        )
        # 采样与多样性控制
        self.temp_red = self._get_env_float('SSQ_TEMP_RED', 1.0, 0.05, 5.0)
        self.temp_blue = self._get_env_float('SSQ_TEMP_BLUE', 1.0, 0.05, 5.0)
        self.top_p_red = self._get_env_float('SSQ_TOPP_RED', 1.0, 0.05, 1.0)
        self.top_p_blue = self._get_env_float('SSQ_TOPP_BLUE', 1.0, 0.05, 1.0)
        self.enforce_candidate_diversity = self._get_env_bool('SSQ_DIVERSIFY', True)
        try:
            self.max_overlap_reds = int(float(os.getenv('SSQ_MAX_OVERLAP', '3')))
            self.max_overlap_reds = max(0, min(5, self.max_overlap_reds))
        except Exception:
            self.max_overlap_reds = 3
        # 文化偏好影响强度（按策略分别控制红/蓝），可由环境或融合配置覆盖
        self.cultural_gamma: Dict[str, Dict[str, float]] = {
            'liuyao': {
                'red': self._get_env_float('SSQ_GAMMA_LIUYAO_RED', 1.0, 0.0, 2.0),
                'blue': self._get_env_float('SSQ_GAMMA_LIUYAO_BLUE', 1.0, 0.0, 2.0),
            },
            'liuren': {
                'red': self._get_env_float('SSQ_GAMMA_LIUREN_RED', 1.0, 0.0, 2.0),
                'blue': self._get_env_float('SSQ_GAMMA_LIUREN_BLUE', 1.0, 0.0, 2.0),
            },
            'qimen': {
                'red': self._get_env_float('SSQ_GAMMA_QIMEN_RED', 1.0, 0.0, 2.0),
                'blue': self._get_env_float('SSQ_GAMMA_QIMEN_BLUE', 1.0, 0.0, 2.0),
            },
        }
        # 可复现随机种子
        seed_raw = os.getenv('SSQ_SEED')
        if seed_raw is not None:
            try:
                random.seed(int(seed_raw))
            except Exception:
                pass
        # 若未通过环境变量覆盖，则尝试从权重文件载入调优器写入的最佳融合参数
        self._maybe_load_best_fusion()

        # 连续预测产物路径
        self._reports_dir = os.path.join(os.getcwd(), 'reports')
        self._static_dir = os.path.join(os.getcwd(), 'static')
        self._live_jsonl = os.path.join(self._reports_dir, 'ssq_live_predictions.jsonl')
        self._live_latest = os.path.join(self._static_dir, 'ssq_live_prediction.json')

        # 文化推演与自学习开关/参数
        self.enable_culture_debate = self._get_env_bool('SSQ_CULTURE_DEBATE', True)
        try:
            self.culture_iters = int(float(os.getenv('SSQ_CULTURE_ITERS', '3')))
        except Exception:
            self.culture_iters = 3
        try:
            self.culture_topk = int(float(os.getenv('SSQ_CULTURE_TOPK', '5')))
        except Exception:
            self.culture_topk = 5
        self.culture_learn = self._get_env_bool('SSQ_CULTURE_LEARN', True)
        self.culmem_path = os.getenv('SSQ_CULMEM_PATH', 'ssq_cultural_memory.json')
        # 文化记忆对融合的影响强度
        self.alpha_mem_red = self._get_env_float('SSQ_ALPHA_CMEM_RED', 0.05, 0.0, 1.0)
        self.alpha_mem_blue = self._get_env_float('SSQ_ALPHA_CMEM_BLUE', 0.05, 0.0, 1.0)
        # 文化记忆更新控制
        self.culmem_decay = self._get_env_float('SSQ_CULMEM_DECAY', 0.999, 0.9, 1.0)
        self.culmem_boost_fused = self._get_env_float('SSQ_CULMEM_BOOST_FUSED', 0.01, 0.0, 1.0)
        self.culmem_boost_candidate = self._get_env_float('SSQ_CULMEM_BOOST_CAND', 0.002, 0.0, 1.0)
        # 深度文化模型重评分设置
        self.enable_dl_rescore = self._get_env_bool('SSQ_DL_RESCORE', True)
        self.dl_score_mix = self._get_env_float('SSQ_DL_SCORE_MIX', 0.3, 0.0, 1.0)

    def _ensure_io_dirs(self):
        try:
            os.makedirs(self._reports_dir, exist_ok=True)
            os.makedirs(self._static_dir, exist_ok=True)
        except Exception:
            pass

    def _maybe_load_best_fusion(self):
        try:
            env_overrides = any([
                os.getenv('SSQ_ALPHA_RED'), os.getenv('SSQ_TEMP_RED'), os.getenv('SSQ_TOPP_RED')
            ])
            if env_overrides:
                return
            path = 'ssq_strategy_weights.json'
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            fusion = payload.get('fusion') if isinstance(payload, dict) else None
            if not isinstance(fusion, dict):
                return
            self.alpha_red = float(fusion.get('alpha_red', self.alpha_red))
            self.temp_red = float(fusion.get('temp_red', self.temp_red))
            self.top_p_red = float(fusion.get('top_p_red', self.top_p_red))
            # 同步加载蓝球侧参数（若存在）
            self.alpha_blue = float(fusion.get('alpha_blue', self.alpha_blue))
            self.temp_blue = float(fusion.get('temp_blue', self.temp_blue))
            self.top_p_blue = float(fusion.get('top_p_blue', self.top_p_blue))
            # 加载文化gamma（若存在）
            cg = fusion.get('cultural_gamma') if isinstance(fusion, dict) else None
            if isinstance(cg, dict):
                for strat in ['liuyao','liuren','qimen']:
                    if isinstance(cg.get(strat), dict):
                        try:
                            rv = cg[strat].get('red')
                            if rv is not None:
                                self.cultural_gamma[strat]['red'] = max(0.0, min(2.0, float(rv)))
                        except Exception:
                            pass
                        try:
                            bv = cg[strat].get('blue')
                            if bv is not None:
                                self.cultural_gamma[strat]['blue'] = max(0.0, min(2.0, float(bv)))
                        except Exception:
                            pass
        except Exception:
            pass

    @staticmethod
    def _get_env_float(name: str, default: float, min_v: Optional[float] = None, max_v: Optional[float] = None) -> float:
        try:
            v = float(os.getenv(name, str(default)))
            if min_v is not None:
                v = max(min_v, v)
            if max_v is not None:
                v = min(max_v, v)
            return v
        except Exception:
            return default

    @staticmethod
    def _get_env_bool(name: str, default: bool) -> bool:
        try:
            raw = os.getenv(name)
            if raw is None:
                return default
            raw = raw.strip().lower()
            if raw in ('1','true','yes','on'):
                return True
            if raw in ('0','false','no','off'):
                return False
            return default
        except Exception:
            return default

    @staticmethod
    def _parse_region_buckets(spec: str) -> List[Tuple[int,int]]:
        buckets: List[Tuple[int,int]] = []
        try:
            for part in (spec or '').split(','):
                part = part.strip()
                if not part:
                    continue
                if '-' in part:
                    a,b = part.split('-',1)
                    lo = int(a)
                    hi = int(b)
                    if 1 <= lo <= hi <= 33:
                        buckets.append((lo,hi))
            if not buckets:
                buckets = [(1,11),(12,22),(23,33)]
        except Exception:
            buckets = [(1,11),(12,22),(23,33)]
        return buckets

    def predict_liuyao(self, issue_idx):
        # 小六爻：以时为要、重时日，叠加文化五行偏好
        reds = []
        base = (issue_idx * 6) % 33
        for i in range(6):
            val = (base + i * 5 + i * issue_idx) % 33 + 1
            reds.append(val)
        # 文化偏好打分并微调
        red_scores, blue_scores = CulturalPredictor().scores(bias={'hour': 1.6, 'day': 1.2})
        cg = self.cultural_gamma.get('liuyao', {'red': 1.0, 'blue': 1.0})
        reds = self._rerank_with_scores(reds, red_scores, gamma=cg.get('red', 1.0))
        blue = (sum(reds) + issue_idx) % 16 + 1
        # 小幅叠加文化蓝球偏好
        blue = self._adjust_blue_with_scores(blue, blue_scores, gamma=cg.get('blue', 1.0))
        return sorted(set(reds))[:6], blue

    def predict_liuren(self, issue_idx):
        # 小六壬：以月日为纲，叠加文化偏好
        stems_cycle = [4, 9, 2, 7, 1, 6, 10, 3, 8, 5]
        branches_cycle = [11, 22, 5, 16, 27, 8, 19, 30, 13, 24, 35, 6]
        stem = stems_cycle[issue_idx % len(stems_cycle)]
        branch = branches_cycle[issue_idx % len(branches_cycle)]
        base = (issue_idx * 7 + stem * 3 + branch) % 33
        offsets = [stem, branch, stem + branch, stem * 2, branch // 2 + issue_idx, stem * branch]
        reds = []
        for off in offsets:
            val = (base + off) % 33 + 1
            if val not in reds:
                reds.append(val)
            if len(reds) == 6:
                break
        while len(reds) < 6:
            base = (base + 5) % 33
            val = base + 1
            if val not in reds:
                reds.append(val)
        red_scores, blue_scores = CulturalPredictor().scores(bias={'month': 1.5, 'day': 1.3})
        cg = self.cultural_gamma.get('liuren', {'red': 1.0, 'blue': 1.0})
        reds = self._rerank_with_scores(reds, red_scores, gamma=cg.get('red', 1.0))
        blue = (stem * 3 + branch + issue_idx) % 16 + 1
        blue = self._adjust_blue_with_scores(blue, blue_scores, gamma=cg.get('blue', 1.0))
        return sorted(reds), blue

    def predict_qimen(self, issue_idx):
        # 奇门遁甲：以季节与日主为重，叠加文化偏好
        palaces = [1, 3, 5, 7, 9, 2, 4, 6, 8]
        gates = [8, 9, 1, 2, 3, 4, 5, 6]
        wonders = [3, 6, 9]
        instruments = [6, 7, 8, 9, 1, 2]
        base = (issue_idx * 9 + palaces[issue_idx % len(palaces)] * 2) % 33
        reds = []
        for i in range(6):
            palace = palaces[(issue_idx + i) % len(palaces)]
            gate = gates[(issue_idx + i) % len(gates)]
            wonder = wonders[(issue_idx + i) % len(wonders)]
            instrument = instruments[(issue_idx + i) % len(instruments)]
            val = (base + palace * wonder + gate + instrument * (i + 1)) % 33 + 1
            if val not in reds:
                reds.append(val)
            else:
                val = (val + i + gate) % 33 + 1
                if val not in reds:
                    reds.append(val)
            if len(reds) == 6:
                break
        while len(reds) < 6:
            base = (base + 7) % 33
            val = base + 1
            if val not in reds:
                reds.append(val)
        red_scores, blue_scores = CulturalPredictor().scores(bias={'season': 1.5, 'day': 1.2})
        cg = self.cultural_gamma.get('qimen', {'red': 1.0, 'blue': 1.0})
        reds = self._rerank_with_scores(reds, red_scores, gamma=cg.get('red', 1.0))
        blue_seed = palaces[issue_idx % len(palaces)] + wonders[issue_idx % len(wonders)]
        blue = (sum(reds) + blue_seed + issue_idx) % 16 + 1
        blue = self._adjust_blue_with_scores(blue, blue_scores, gamma=cg.get('blue', 1.0))
        return sorted(reds), blue

    def predict_ai(self, issue_idx):
        # AI模型预测扩展
        # 1. 基于历史开奖数据，自动训练随机森林/XGBoost模型
        # 2. 融合冷热号、奇偶、区间、连号、质数等统计特征
        # 3. 可集成启发式规则与大模型语义解读
        reds, blue = self.ai_model.predict()
        return reds, blue

    def _ensure_cultural_dl(self):
        if self._cultural_dl is not None:
            return self._cultural_dl
        try:
            # 优先加载
            os.makedirs(os.path.dirname(self._cultural_dl_path), exist_ok=True)
            mdl = None
            if os.path.exists(self._cultural_dl_path):
                mdl = CulturalDeepModel.load(self._cultural_dl_path)
            if mdl is None:
                mdl = CulturalDeepModel()
                ok = mdl.fit(self.history)
                if ok:
                    try:
                        mdl.save(self._cultural_dl_path)
                    except Exception:
                        pass
            self._cultural_dl = mdl
        except Exception:
            self._cultural_dl = None
        return self._cultural_dl

    def predict_cultural_dl(self, issue_idx):
        mdl = self._ensure_cultural_dl()
        if mdl is None:
            return self._random_numbers()
        reds, blue = mdl.predict_numbers(issue_idx)
        # 与文化gamma兼容：做一次轻量重排/调整
        red_scores, blue_scores = CulturalPredictor().scores(bias={'hour': 1.6, 'day': 1.2})
        cg = self.cultural_gamma.get('liuyao', {'red': 1.0, 'blue': 1.0})
        reds = self._rerank_with_scores(reds, red_scores, gamma=cg.get('red', 1.0))
        blue = self._adjust_blue_with_scores(blue, blue_scores, gamma=cg.get('blue', 1.0))
        return sorted(set(reds))[:6], int(blue)

    def _random_numbers(self):
        reds = random.sample(range(1,34), 6)
        blue = random.randint(1,16)
        return reds, blue

    # --- 文化信号融合微调 ---
    def _rerank_with_scores(self, reds: List[int], scores: Dict[int, float], gamma: float = 1.0) -> List[int]:
        # 用分数与原序混合对候选重排；保持集合规模
        uniq = list(dict.fromkeys(reds))
        if not uniq:
            return []
        g = max(0.0, min(1.0, float(gamma)))
        # 原序得分（越靠前越高）
        n = float(len(uniq))
        base_rank = {x: (n - i) / n for i, x in enumerate(uniq)}
        jitter = 0.02
        uniq.sort(key=lambda x: g * float(scores.get(x, 0.0)) + (1.0 - g) * base_rank.get(x, 0.0) + random.uniform(-jitter, jitter), reverse=True)
        return uniq[:6]

    def _adjust_blue_with_scores(self, blue: int, scores: Dict[int, float], gamma: float = 1.0) -> int:
        # 若文化分数提示其它蓝球略优，以概率替换（概率随gamma缩放）
        if not scores:
            return blue
        best = max(range(1,17), key=lambda b: scores.get(b, 0.0))
        if best != blue:
            g = max(0.0, min(2.0, float(gamma)))
            p = min(0.9, 0.2 * g)  # 基础20%概率，乘以gamma
            if random.random() < p:
                return best
        return blue

    def match(self, pred_reds, pred_blue, true_reds, true_blue):
        return set(pred_reds) == set(true_reds) and pred_blue == true_blue

    def _ensure_deepseek_client(self):
        if self._deepseek_client is False:
            return None
        if self._deepseek_client not in (None, False):
            return self._deepseek_client
        if DeepseekAPI is None:
            self._deepseek_client = False
            return None
        try:
            self._deepseek_client = DeepseekAPI()
        except Exception:
            self._deepseek_client = False
        return self._deepseek_client or None

    def _record_attempt(
        self,
        issue_idx: int,
        strategy: str,
        pred_reds: List[int],
        pred_blue: int,
        true_reds: List[int],
        true_blue: int,
        issue_state: Dict[str, object],
        meta: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        is_match = self.match(pred_reds, pred_blue, true_reds, true_blue)
        attempt_count = int(issue_state.get('attempts', 0)) + 1
        issue_state['attempts'] = attempt_count
        strategies = issue_state.setdefault('strategies', {})
        stats = strategies.setdefault(strategy, {'attempts': 0, 'matches': 0})
        stats['attempts'] += 1
        if is_match:
            stats['matches'] += 1
            issue_state['matched'] = True
            issue_state['matched_strategy'] = strategy
            issue_state['matched_attempt'] = attempt_count
            issue_state['matched_numbers'] = {
                'reds': sorted(pred_reds),
                'blue': pred_blue,
            }
        record = {
            'issue': issue_idx,
            'strategy': strategy,
            'pred_reds': sorted(pred_reds),
            'pred_blue': pred_blue,
            'true_reds': sorted(true_reds),
            'true_blue': true_blue,
            'is_match': is_match,
            'attempt_index': attempt_count,
            'timestamp': time.time(),
            'meta': meta or {},
        }
        self.loop_attempts.append(record)
        return record

    def _load_strategy_weights(self) -> Optional[Dict[str, float]]:
        path = 'ssq_strategy_weights.json'
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    w = data.get('weights', {})
                    if isinstance(w, dict) and w:
                        # 接受策略集合（含 cultural_dl）
                        return {str(k): float(v) for k, v in w.items() if str(k) in {'liuyao','liuren','qimen','ai','cultural_dl'}}
        except Exception:
            return None
        # 动态回退：基于最近窗口表现自适应权重（若无配置文件）
        try:
            # 从 issue_states 统计各策略在最近 N 期的尝试/完全命中
            last_n = int(os.getenv('SSQ_FUSION_WEIGHT_WINDOW', '50') or '50')
            keys = list(sorted(self.issue_states.keys()))
            picked = keys[-last_n:] if last_n > 0 else keys
            stat: Dict[str, Dict[str, float]] = {}
            for k in picked:
                st = self.issue_states.get(k) or {}
                strategies = st.get('strategies', {}) or {}
                if isinstance(strategies, dict):
                    for name, s in strategies.items():
                        if str(name) not in {'liuyao','liuren','qimen','ai','cultural_dl'}:
                            continue
                        d = stat.setdefault(str(name), {'attempts': 0.0, 'matches': 0.0})
                        try:
                            d['attempts'] += float(s.get('attempts', 0))
                            d['matches'] += float(s.get('matches', 0))
                        except Exception:
                            pass
            # 平滑并 softmax 成为权重
            if stat:
                import math
                scores: Dict[str, float] = {}
                for name, d in stat.items():
                    a = float(d.get('attempts', 0.0))
                    m = float(d.get('matches', 0.0))
                    # 稳健率估计（拉普拉斯平滑）：(m+1)/(a+4)
                    rate = (m + 1.0) / (a + 4.0) if a >= 0 else 1.0
                    scores[name] = rate
                # softmax
                mx = max(scores.values()) if scores else 1.0
                exps = {k: math.exp(v - mx) for k, v in scores.items()}
                s = sum(exps.values()) or 1.0
                weights = {k: (exps[k] / s) for k in exps}
                return weights
        except Exception:
            pass
        return None

    def _fuse_from_attempts(self, attempts: List[Dict[str, object]]) -> Tuple[List[int], int]:
        reds_counter = Counter()
        blue_counter = Counter()
        weights = self._load_strategy_weights() or {}
        fusion_trace = {"weights": dict(weights), "priors": {}}
        # 读取号码先验作为平滑项
        red_prior = {n: 0.0 for n in range(1,34)}
        blue_prior = {n: 0.0 for n in range(1,17)}
        try:
            with open('ssq_ball_priors.json', 'r', encoding='utf-8') as f:
                pri = json.load(f)
                r = pri.get('red', {})
                b = pri.get('blue', {})
                # 归一化为概率
                r_sum = sum(float(r.get(str(k), 0)) for k in range(1,34)) or 1.0
                b_sum = sum(float(b.get(str(k), 0)) for k in range(1,17)) or 1.0
                for k in range(1,34):
                    red_prior[k] = float(r.get(str(k), 0)) / r_sum
                for k in range(1,17):
                    blue_prior[k] = float(b.get(str(k), 0)) / b_sum
        except Exception:
            pass
        # 结合 AI 与文化深度模型的分布作为先验（均值融合近似贝叶斯）
        try:
            # 当前期次（从 attempts 里推断）
            cur_issue = None
            for a in reversed(attempts):
                if isinstance(a, dict) and 'issue' in a:
                    cur_issue = int(a.get('issue'))
                    break
            if cur_issue is None:
                cur_issue = len(self.history) - 1
            # AI 分布（红33、蓝16）
            ai_red_p, ai_blue_p = None, None
            if hasattr(self.ai_model, 'get_distributions'):
                try:
                    ai_red_p, ai_blue_p = self.ai_model.get_distributions()
                except Exception:
                    ai_red_p, ai_blue_p = None, None
            # 文化深度分布
            cul_red_p, cul_blue_p = None, None
            try:
                mdl = self._ensure_cultural_dl()
                if mdl:
                    cul_red_p, cul_blue_p = mdl.predict_distributions(cur_issue)
            except Exception:
                cul_red_p, cul_blue_p = None, None
            if ai_red_p and cul_red_p:
                for k in range(1,34):
                    red_prior[k] = 0.5 * float(ai_red_p[k-1]) + 0.5 * float(cul_red_p[k-1])
            if ai_blue_p and cul_blue_p:
                for k in range(1,17):
                    blue_prior[k] = 0.5 * float(ai_blue_p[k-1]) + 0.5 * float(cul_blue_p[k-1])
            fusion_trace["priors"] = {"red": red_prior.copy(), "blue": blue_prior.copy()}
        except Exception:
            pass
        # 累计策略计票
        for attempt in attempts:
            w = 1.0
            try:
                w = float(weights.get(str(attempt.get('strategy')), 1.0))
            except Exception:
                w = 1.0
            # 记录权重轨迹
            fusion_trace.setdefault("weights", {})[str(attempt.get('strategy'))] = w
            for red in attempt.get('pred_reds', []):
                reds_counter[red] += w
            blue = attempt.get('pred_blue')
            if isinstance(blue, int):
                blue_counter[blue] += w
        # 加入小幅先验平滑与“文化记忆”，避免冷门极端化（强度可由环境变量配置）
        alpha_red = float(self.alpha_red)
        alpha_blue = float(self.alpha_blue)
        total_red_votes = float(sum(reds_counter.values()))
        total_blue_votes = float(sum(blue_counter.values()))
        if total_red_votes > 0:
            for k in range(1,34):
                reds_counter[k] += alpha_red * red_prior.get(k, 0.0) * total_red_votes
        if total_blue_votes > 0:
            for k in range(1,17):
                blue_counter[k] += alpha_blue * blue_prior.get(k, 0.0) * total_blue_votes
        # 文化记忆（来自“自学自推”）作为额外平滑
        if (self.alpha_mem_red > 1e-9 or self.alpha_mem_blue > 1e-9):
            mem = self._load_cultural_memory()
            if mem:
                mred = mem.get('red', {})
                mblue = mem.get('blue', {})
                rsum = sum(float(mred.get(k, 0.0)) for k in range(1,34))
                bsum = sum(float(mblue.get(k, 0.0)) for k in range(1,17))
                if total_red_votes > 0 and rsum > 0:
                    for k in range(1,34):
                        reds_counter[k] += self.alpha_mem_red * (float(mred.get(k, 0.0)) / rsum) * total_red_votes
                if total_blue_votes > 0 and bsum > 0:
                    for k in range(1,17):
                        blue_counter[k] += self.alpha_mem_blue * (float(mblue.get(k, 0.0)) / bsum) * total_blue_votes
        # 采样或贪心选择
        fused_reds: List[int] = []
        use_sampling_red = (abs(self.temp_red - 1.0) > 1e-9) or (self.top_p_red < 0.999)
        if use_sampling_red and sum(reds_counter.values()) > 0:
            fused_reds = self._weighted_sample_without_replacement(
                values=list(range(1,34)),
                weights=[float(reds_counter.get(i, 0.0)) for i in range(1,34)],
                k=6,
                temperature=self.temp_red,
                top_p=self.top_p_red,
            )
        else:
            fused_reds = [num for num, _ in reds_counter.most_common(6)]
            while len(fused_reds) < 6:
                candidate = random.randint(1, 33)
                if candidate not in fused_reds:
                    fused_reds.append(candidate)
        # 多样性约束：可配置的区域覆盖
        if self.enforce_region_coverage:
            def _region_idx(x: int) -> Optional[int]:
                for i,(lo,hi) in enumerate(self.region_buckets):
                    if lo <= x <= hi:
                        return i
                return None
            regions: Dict[int,int] = {i:0 for i in range(len(self.region_buckets))}
            for r in fused_reds:
                ri = _region_idx(r)
                if ri is not None:
                    regions[ri] += 1
            # 若有缺失区域，则尝试从剩余高票中补齐
            if any(v == 0 for v in regions.values()):
                candidates_sorted = [n for n, _ in reds_counter.most_common(33) if n not in fused_reds]
                # 循环补齐至每个分桶至少1个
                for rid, v in regions.items():
                    if v > 0:
                        continue
                    for c in candidates_sorted:
                        ri = _region_idx(c)
                        if ri == rid:
                            # 替换一个属于当前最多分桶的元素
                            # 统计当前分桶分布
                            counts = {i:0 for i in range(len(self.region_buckets))}
                            for val in fused_reds:
                                rj = _region_idx(val)
                                if rj is not None:
                                    counts[rj] += 1
                            # 找到一个可替换位
                            replaced = False
                            for i, v0 in enumerate(list(fused_reds)):
                                rj = _region_idx(v0)
                                if rj is not None and counts[rj] > 1:
                                    counts[rj] -= 1
                                    fused_reds[i] = c
                                    regions[rid] += 1
                                    replaced = True
                                    break
                            if replaced:
                                break
        fused_blue = None
        use_sampling_blue = (abs(self.temp_blue - 1.0) > 1e-9) or (self.top_p_blue < 0.999)
        if blue_counter:
            if use_sampling_blue:
                fused_blue = self._weighted_sample_single(
                    values=list(range(1,17)),
                    weights=[float(blue_counter.get(i, 0.0)) for i in range(1,17)],
                    temperature=self.temp_blue,
                    top_p=self.top_p_blue,
                )
            else:
                fused_blue = blue_counter.most_common(1)[0][0]
        if fused_blue is None:
            fused_blue = random.randint(1, 16)
        # 存储轨迹（内存+文件），便于报告采集
        try:
            self._last_fusion_trace = {
                "fused_reds": sorted(fused_reds[:6]),
                "fused_blue": int(fused_blue),
                "fusion": fusion_trace,
            }
            os.makedirs('reports', exist_ok=True)
            with open('reports/fusion_trace_last.json', 'w', encoding='utf-8') as f:
                json.dump(self._last_fusion_trace, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return sorted(fused_reds[:6]), fused_blue

    # ---------- 采样辅助 ----------
    def _weighted_sample_single(self, values: List[int], weights: List[float], temperature: float = 1.0, top_p: float = 1.0) -> int:
        assert len(values) == len(weights)
        # 温度缩放：p_i ∝ w_i^(1/T)
        ws = [max(0.0, w) for w in weights]
        if sum(ws) <= 0:
            return random.choice(values)
        if abs(temperature - 1.0) > 1e-9:
            invT = 1.0 / max(1e-6, temperature)
            ws = [w ** invT for w in ws]
        s = sum(ws)
        probs = [w / s for w in ws]
        # top-p 过滤
        if top_p < 0.999:
            pairs = sorted(zip(values, probs), key=lambda x: x[1], reverse=True)
            cum = 0.0
            kept: List[Tuple[int,float]] = []
            for v, p in pairs:
                kept.append((v, p))
                cum += p
                if cum >= top_p:
                    break
            vs = [v for v, _ in kept]
            ps = [p for _, p in kept]
            s2 = sum(ps) or 1.0
            ps = [p / s2 for p in ps]
            return random.choices(vs, weights=ps, k=1)[0]
        return random.choices(values, weights=probs, k=1)[0]

    def _weighted_sample_without_replacement(self, values: List[int], weights: List[float], k: int, temperature: float = 1.0, top_p: float = 1.0) -> List[int]:
        selected: List[int] = []
        pool_vals = list(values)
        pool_w = [max(0.0, w) for w in weights]
        for _ in range(max(0, k)):
            if not pool_vals:
                break
            choice = self._weighted_sample_single(pool_vals, pool_w, temperature=temperature, top_p=top_p)
            selected.append(choice)
            # 移除已选择项
            idx = pool_vals.index(choice)
            pool_vals.pop(idx)
            pool_w.pop(idx)
        # 若不够则随机补齐
        while len(selected) < k:
            c = random.choice([v for v in range(1,34) if v not in selected])
            selected.append(c)
        return selected

    def generate_candidates_from_attempts(self, attempts: List[Dict[str, object]], count: int = 5) -> List[Dict[str, int]]:
        """基于若干尝试记录，生成多组候选，带多样性约束。"""
        candidates: List[Tuple[List[int], int]] = []
        tries_per = 50
        for _ in range(max(1, min(50, count))):
            ok = False
            for _t in range(tries_per):
                reds, blue = self._fuse_from_attempts(attempts)
                if not self.enforce_candidate_diversity:
                    ok = True
                    cand = (reds, blue)
                    break
                # 检查与已选的重合度
                too_similar = False
                for r0, _b0 in candidates:
                    overlap = len(set(r0) & set(reds))
                    if overlap > self.max_overlap_reds:
                        too_similar = True
                        break
                if not too_similar:
                    ok = True
                    cand = (reds, blue)
                    break
            if not ok:
                # 退化：直接接受当前采样
                cand = self._fuse_from_attempts(attempts)
            candidates.append(cand)
        raw = [{'reds': sorted(r), 'blue': int(b)} for r, b in candidates]
        # 文化推演与微调（可开关）
        if self.enable_culture_debate:
            refined, _meta = self._refine_by_culture(raw)
            ranked = self._maybe_rescore_by_deep(refined)
            return ranked
        return self._maybe_rescore_by_deep(raw)

    # ---------- 深度文化模型重评分 ----------
    def _dl_distributions(self, issue_idx: int) -> Optional[Tuple[List[float], List[float]]]:
        mdl = self._ensure_cultural_dl()
        if mdl is None:
            return None
        try:
            return mdl.predict_distributions(issue_idx)
        except Exception:
            return None

    def _dl_score(self, issue_idx: int, reds: List[int], blue: int) -> float:
        d = self._dl_distributions(issue_idx)
        if not d:
            return 0.0
        rp, bp = d
        # 使用对数概率和（稳定、可加），并做简单归一
        import math
        logsum = 0.0
        for r in reds:
            p = max(1e-9, float(rp[r-1] if 1 <= r <= 33 else 1e-9))
            logsum += math.log(p)
        pblue = max(1e-9, float(bp[blue-1] if 1 <= blue <= 16 else 1e-9))
        logsum += math.log(pblue)
        return float(logsum)

    def _maybe_rescore_by_deep(self, cands: List[Dict[str,int]]) -> List[Dict[str,int]]:
        if not self.enable_dl_rescore or not cands:
            return cands
        try:
            # 以当前历史长度作为虚拟期次索引（与连续模式一致的增长基准）
            base_idx = len(self.history) - 1 if self.history else 0
            scored: List[Tuple[float, Dict[str,int]]] = []
            # 先计算文化分数与深度分数，并归一后线性混合
            cul_scores: List[float] = []
            dl_scores: List[float] = []
            for i, c in enumerate(cands):
                reds = list(c.get('reds', []))
                blue = int(c.get('blue', 1))
                cul_scores.append(self._cultural_score(reds, blue))
                dl_scores.append(self._dl_score(base_idx + i, reds, blue))
            # 归一（防止全零）
            def _norm(xs: List[float]) -> List[float]:
                import math
                if not xs:
                    return xs
                m = min(xs)
                xs2 = [x - m for x in xs]
                s = sum(xs2) or 1.0
                return [x/s for x in xs2]
            cul_n = _norm(cul_scores)
            dl_n = _norm(dl_scores)
            mix = float(self.dl_score_mix)
            for idx, c in enumerate(cands):
                score = (1.0 - mix) * cul_n[idx] + mix * dl_n[idx]
                scored.append((score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored]
        except Exception:
            return cands

    # ================= 文化推演/论证与自学习 =================
    def _cultural_profiles(self) -> List[Tuple[str, Dict[str, float]]]:
        # 三种文化视角的偏置配置，与各策略预测时保持一致
        return [
            ('liuyao', {'hour': 1.6, 'day': 1.2}),
            ('liuren', {'month': 1.5, 'day': 1.3}),
            ('qimen', {'season': 1.5, 'day': 1.2}),
        ]

    def _cultural_score(self, reds: List[int], blue: int) -> float:
        # 汇聚多文化视角的加权得分（简单求和/归一）
        total = 0.0
        for _name, bias in self._cultural_profiles():
            try:
                rs, bs = CulturalPredictor().scores(bias=bias)
            except Exception:
                rs, bs = {}, {}
            # 归一化分母，避免绝对值尺度差异
            rden = sum(float(max(0.0, v)) for v in rs.values()) or 1.0
            bden = sum(float(max(0.0, v)) for v in bs.values()) or 1.0
            rsum = sum(float(rs.get(n, 0.0)) for n in reds) / rden
            bval = float(bs.get(blue, 0.0)) / bden
            total += rsum + bval
        return float(total)

    def _refine_by_culture(self, candidates: List[Dict[str, int]]) -> Tuple[List[Dict[str, int]], Dict[str, object]]:
        # 对候选进行若干次“文化论证”迭代，尝试用高分备选替换低分元素
        iters = max(0, int(self.culture_iters))
        topk = max(1, int(self.culture_topk))
        profiles = self._cultural_profiles()
        meta: Dict[str, object] = {'iters': iters, 'topk': topk, 'details': []}
        out: List[Dict[str, int]] = []
        for cand in candidates:
            reds = list(sorted(set(int(x) for x in cand.get('reds', []))))[:6]
            blue = int(cand.get('blue', 1))
            before = self._cultural_score(reds, blue)
            for _ in range(iters):
                # 预备多视角评分
                try:
                    scores_r_list: List[Dict[int,float]] = []
                    scores_b_list: List[Dict[int,float]] = []
                    for _name, bias in profiles:
                        rs, bs = CulturalPredictor().scores(bias=bias)
                        scores_r_list.append(rs)
                        scores_b_list.append(bs)
                except Exception:
                    scores_r_list, scores_b_list = [], []
                # 聚合红分数与蓝分数
                agg_r = {i: 0.0 for i in range(1,34)}
                agg_b = {i: 0.0 for i in range(1,17)}
                for rs in scores_r_list:
                    for i,v in rs.items():
                        agg_r[i] = agg_r.get(i, 0.0) + float(v)
                for bs in scores_b_list:
                    for i,v in bs.items():
                        agg_b[i] = agg_b.get(i, 0.0) + float(v)
                # 找出当前红球中分最低者与非入选中的高分候选
                reds_sorted = sorted(list(reds), key=lambda x: agg_r.get(x, 0.0))
                if reds_sorted:
                    worst = reds_sorted[0]
                else:
                    worst = None
                alt_pool = [i for i in range(1,34) if i not in reds]
                alt_sorted = sorted(alt_pool, key=lambda x: agg_r.get(x, 0.0), reverse=True)[:topk]
                improved = False
                best_try = (reds[:], blue, before)
                # 尝试替换红球
                for alt in alt_sorted:
                    if worst is None:
                        break
                    trial_reds = sorted(list(set([x for x in reds if x != worst] + [alt])))[:6]
                    sc = self._cultural_score(trial_reds, blue)
                    if sc > best_try[2] + 1e-9:
                        best_try = (trial_reds, blue, sc)
                        improved = True
                # 尝试优化蓝球
                blue_alts = sorted(range(1,17), key=lambda x: agg_b.get(x, 0.0), reverse=True)[:topk]
                for b2 in blue_alts:
                    trial_reds = best_try[0]
                    sc = self._cultural_score(trial_reds, b2)
                    if sc > best_try[2] + 1e-9:
                        best_try = (trial_reds, b2, sc)
                        improved = True
                reds, blue, before = best_try
                if not improved:
                    break
            after = before
            out.append({'reds': reds, 'blue': blue})
            meta['details'].append({'before': float(before), 'after': float(after)})
        return out, meta

    def _load_cultural_memory(self) -> Optional[Dict[str, Dict[int, float]]]:
        try:
            if not os.path.exists(self.culmem_path):
                return None
            with open(self.culmem_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            red = {int(k): float(v) for k, v in (raw.get('red', {}) or {}).items() if 1 <= int(k) <= 33}
            blue = {int(k): float(v) for k, v in (raw.get('blue', {}) or {}).items() if 1 <= int(k) <= 16}
            return {'red': red, 'blue': blue}
        except Exception:
            return None

    def _save_cultural_memory(self, red: Dict[int,float], blue: Dict[int,float]) -> None:
        try:
            payload = {
                'version': 1,
                'updated_at': time.time(),
                'red': {str(k): float(v) for k, v in red.items()},
                'blue': {str(k): float(v) for k, v in blue.items()},
            }
            with open(self.culmem_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _update_cultural_memory(self, fused: Tuple[List[int], int] | Dict[str,int], candidates: List[Dict[str,int]]) -> None:
        if not self.culture_learn:
            return
        try:
            mem = self._load_cultural_memory() or {'red': {i: 0.0 for i in range(1,34)}, 'blue': {i: 0.0 for i in range(1,17)}}
            red = mem.get('red', {})
            blue = mem.get('blue', {})
            # 衰减
            decay = float(self.culmem_decay)
            for i in range(1,34):
                red[i] = float(red.get(i, 0.0)) * decay
            for i in range(1,17):
                blue[i] = float(blue.get(i, 0.0)) * decay
            # 提升：融合结果权重大，候选较小
            try:
                if isinstance(fused, dict):
                    fused_reds = fused.get('reds', [])
                    fused_blue = fused.get('blue', 1)
                else:
                    fused_reds, fused_blue = fused
                for r in fused_reds:
                    if 1 <= int(r) <= 33:
                        red[int(r)] = red.get(int(r), 0.0) + float(self.culmem_boost_fused)
                if 1 <= int(fused_blue) <= 16:
                    blue[int(fused_blue)] = blue.get(int(fused_blue), 0.0) + float(self.culmem_boost_fused)
            except Exception:
                pass
            for c in candidates:
                for r in c.get('reds', []):
                    if 1 <= int(r) <= 33:
                        red[int(r)] = red.get(int(r), 0.0) + float(self.culmem_boost_candidate)
                b = c.get('blue', 1)
                if 1 <= int(b) <= 16:
                    blue[int(b)] = blue.get(int(b), 0.0) + float(self.culmem_boost_candidate)
            self._save_cultural_memory(red, blue)
        except Exception:
            pass

    def _parse_numbers_from_text(self, text: str) -> Optional[Tuple[List[int], int]]:
        numbers = [int(x) for x in re.findall(r"\d+", text)]
        reds = [n for n in numbers if 1 <= n <= 33][:6]
        blue_candidates = [n for n in numbers if 1 <= n <= 16]
        blue = None
        if blue_candidates:
            # 尝试挑选未出现在红球中的候选
            for candidate in blue_candidates:
                if candidate not in reds:
                    blue = candidate
                    break
            if blue is None:
                blue = blue_candidates[0]
        if len(reds) == 6 and isinstance(blue, int):
            return sorted(reds), blue
        return None

    def _consult_deepseek(
        self,
        issue_idx: int,
        true_reds: List[int],
        true_blue: int,
        issue_state: Dict[str, object],
        attempts: List[Dict[str, object]],
    ) -> Optional[Dict[str, object]]:
        client = self._ensure_deepseek_client()
        if client is None:
            return None
        last_attempts = attempts[-5:]
        attempt_brief = []
        for attempt in last_attempts:
            attempt_brief.append(
                f"策略:{attempt['strategy']} 红:{attempt['pred_reds']} 蓝:{attempt['pred_blue']} 匹配:{attempt['is_match']}"
            )
        prompt = (
            "我们正在复盘双色球预测闭环，请基于以下尝试给予新的预测建议。"
            "请输出6个1-33的红球与1个1-16的蓝球，尽量避免重复。"
        )
        messages = [
            {"role": "system", "content": "你是辅助双色球预测的数字分析顾问。"},
            {
                "role": "user",
                "content": (
                    f"期次索引:{issue_idx} 已尝试{issue_state.get('attempts', 0)}次。最近尝试: "
                    + " | ".join(attempt_brief)
                ),
            },
            {"role": "user", "content": prompt},
        ]
        try:
            response = client.chat(messages)
        except Exception:
            return None
        content = ''
        if isinstance(response, dict):
            choices = response.get('choices') if isinstance(response.get('choices'), list) else []
            if choices:
                content = choices[0].get('message', {}).get('content', '')
        if not content:
            return None
        parsed = self._parse_numbers_from_text(content)
        if not parsed:
            return None
        reds, blue = parsed
        return self._record_attempt(
            issue_idx,
            'deepseek_suggestion',
            reds,
            blue,
            true_reds,
            true_blue,
            issue_state,
            meta={'raw': content},
        )

    def run_cycle(self):
        for idx, (true_reds, true_blue) in enumerate(self.history):
            for model in self.models:
                if model == 'liuyao':
                    pred_reds, pred_blue = self.predict_liuyao(idx)
                elif model == 'liuren':
                    pred_reds, pred_blue = self.predict_liuren(idx)
                elif model == 'qimen':
                    pred_reds, pred_blue = self.predict_qimen(idx)
                elif model == 'ai':
                    pred_reds, pred_blue = self.predict_ai(idx)
                elif model == 'cultural_dl':
                    pred_reds, pred_blue = self.predict_cultural_dl(idx)
                else:
                    continue
                is_match = self.match(pred_reds, pred_blue, true_reds, true_blue)
                self.match_log.append({
                    'issue': idx,
                    'model': model,
                    'pred_reds': pred_reds,
                    'pred_blue': pred_blue,
                    'true_reds': true_reds,
                    'true_blue': true_blue,
                    'is_match': is_match
                })
                if is_match:
                    print(f"[完全匹配] 期次:{idx} 模型:{model} 号码:{pred_reds}|{pred_blue} 预测次数:{len(self.match_log)}")
                    # 可扩展：自动弹窗/推送/进入下一期
        print("[周期预测完成] 匹配日志已生成。")

    def run_closed_loop(
        self,
        max_attempts_per_issue: int = 120,
        consult_external: bool = True,
        consult_interval: int = 12,
        sleep_interval: float = 0.0,
        log_dir: str = 'reports',
        train_ai: bool = True,
        max_seconds_per_issue: float | None = None,
    ) -> Dict[str, object]:
        """连续执行闭环预测并生成综合摘要。"""
        self.loop_attempts.clear()
        self.issue_states.clear()
        os.makedirs(log_dir, exist_ok=True)
        if train_ai:
            try:
                self.ai_model.train()
            except Exception:
                pass
        for issue_idx, (true_reds_raw, true_blue) in enumerate(self.history):
            true_reds = list(true_reds_raw)
            issue_state: Dict[str, object] = {
                'issue': issue_idx,
                'attempts': 0,
                'matched': False,
            }
            issue_attempts: List[Dict[str, object]] = []
            start_ts = time.time()
            attempts_unlimited = (max_attempts_per_issue is None) or (int(max_attempts_per_issue) <= 0)
            def _time_budget_ok() -> bool:
                if max_seconds_per_issue is None:
                    return True
                try:
                    return (time.time() - start_ts) < float(max_seconds_per_issue)
                except Exception:
                    return True
            while attempts_unlimited or issue_state['attempts'] < max_attempts_per_issue:
                if not _time_budget_ok():
                    break
                for model in self.models:
                    if model == 'liuyao':
                        pred_reds, pred_blue = self.predict_liuyao(issue_idx)
                    elif model == 'liuren':
                        pred_reds, pred_blue = self.predict_liuren(issue_idx)
                    elif model == 'qimen':
                        pred_reds, pred_blue = self.predict_qimen(issue_idx)
                    elif model == 'ai':
                        pred_reds, pred_blue = self.predict_ai(issue_idx)
                    elif model == 'cultural_dl':
                        pred_reds, pred_blue = self.predict_cultural_dl(issue_idx)
                    else:
                        continue
                    attempt = self._record_attempt(
                        issue_idx,
                        model,
                        pred_reds,
                        pred_blue,
                        true_reds,
                        true_blue,
                        issue_state,
                    )
                    issue_attempts.append(attempt)
                    if issue_state.get('matched'):
                        break
                if issue_state.get('matched'):
                    break
                if (not attempts_unlimited) and issue_state['attempts'] >= max_attempts_per_issue:
                    break
                if issue_attempts:
                    fused_reds, fused_blue = self._fuse_from_attempts(issue_attempts)
                    fused_attempt = self._record_attempt(
                        issue_idx,
                        'heuristic_fusion',
                        fused_reds,
                        fused_blue,
                        true_reds,
                        true_blue,
                        issue_state,
                        meta={'source': 'frequency_majority'},
                    )
                    issue_attempts.append(fused_attempt)
                    if issue_state.get('matched'):
                        break
                if not _time_budget_ok():
                    break
                if (not attempts_unlimited) and issue_state['attempts'] >= max_attempts_per_issue:
                    break
                random_reds, random_blue = self._random_numbers()
                random_attempt = self._record_attempt(
                    issue_idx,
                    'random_fallback',
                    random_reds,
                    random_blue,
                    true_reds,
                    true_blue,
                    issue_state,
                    meta={'source': 'stochastic'},
                )
                issue_attempts.append(random_attempt)
                if issue_state.get('matched'):
                    break
                if (
                    consult_external
                    and issue_state['attempts'] >= consult_interval
                    and issue_state['attempts'] % consult_interval == 0
                ):
                    suggestion = self._consult_deepseek(
                        issue_idx,
                        true_reds,
                        true_blue,
                        issue_state,
                        issue_attempts,
                    )
                    if suggestion:
                        issue_attempts.append(suggestion)
                        if issue_state.get('matched'):
                            break
                if not _time_budget_ok():
                    break
                if (not attempts_unlimited) and issue_state['attempts'] >= max_attempts_per_issue:
                    break
                if sleep_interval > 0:
                    time.sleep(sleep_interval)
            if not issue_state.get('matched'):
                issue_state['matched'] = False
                issue_state.setdefault('strategies', {})
                # 构造备注：兼容按次数与按时间两种限制
                remark_parts = []
                if not attempts_unlimited:
                    remark_parts.append(f"未在尝试上限 {max_attempts_per_issue} 次内完成完全匹配")
                if max_seconds_per_issue is not None:
                    remark_parts.append(f"已达时间上限 {max_seconds_per_issue}s")
                if remark_parts:
                    issue_state['remarks'] = '，'.join(remark_parts) + '，已自动进入下一期。'
                else:
                    issue_state['remarks'] = '已自动进入下一期。'
            # 汇总每期的外部建议采纳统计，便于报告做趋势分析
            try:
                strategies = issue_state.get('strategies', {}) or {}
                ds = strategies.get('deepseek_suggestion', {}) or {}
                issue_state['deepseek_attempts'] = int(ds.get('attempts', 0))
                issue_state['deepseek_matched'] = bool(
                    issue_state.get('matched_strategy') == 'deepseek_suggestion' or int(ds.get('matches', 0)) > 0
                )
            except Exception:
                pass
            self.issue_states[issue_idx] = issue_state
        summary = self._build_closed_loop_summary(max_attempts_per_issue)
        self._persist_closed_loop_summary(log_dir, summary)
        return summary

    def _build_closed_loop_summary(self, max_attempts_per_issue: int) -> Dict[str, object]:
        strategy_stats: Dict[str, Dict[str, int]] = {}
        for attempt in self.loop_attempts:
            strategy = str(attempt.get('strategy'))
            entry = strategy_stats.setdefault(strategy, {'attempts': 0, 'matches': 0})
            entry['attempts'] += 1
            if attempt.get('is_match'):
                entry['matches'] += 1
        total_attempts = sum(stat['attempts'] for stat in strategy_stats.values())
        total_matches = sum(stat['matches'] for stat in strategy_stats.values())
        summary = {
            'total_attempts': total_attempts,
            'total_matches': total_matches,
            'strategy_stats': strategy_stats,
            'issue_states': list(self.issue_states.values()),
            'max_attempts_per_issue': max_attempts_per_issue,
            'generated_at': time.time(),
        }
        return summary

    def _persist_closed_loop_summary(self, log_dir: str, summary: Dict[str, object]) -> None:
        json_path = os.path.join(log_dir, 'ssq_closed_loop_summary.json')
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        md_path = os.path.join(log_dir, f'ssq_closed_loop_{timestamp}.md')
        lines: List[str] = [
            '# 双色球闭环预测摘要',
            '',
            f"- 总尝试次数: {summary.get('total_attempts', 0)}",
            f"- 完全匹配次数: {summary.get('total_matches', 0)}",
            f"- 单期尝试安全上限: {summary.get('max_attempts_per_issue', 0)}",
            '',
            '## 策略统计',
        ]
        for strategy, stats in summary.get('strategy_stats', {}).items():
            lines.append(
                f"- {strategy}: 尝试 {stats['attempts']} 次，完全匹配 {stats['matches']} 次"
            )
        lines.append('')
        lines.append('## 各期概览')
        for issue_state in summary.get('issue_states', []):
            issue = issue_state.get('issue')
            attempts = issue_state.get('attempts')
            matched = issue_state.get('matched')
            matched_strategy = issue_state.get('matched_strategy', '-')
            remark = issue_state.get('remarks', '')
            lines.append(
                f"- 期次索引 {issue}: 尝试 {attempts} 次，匹配={matched}，策略={matched_strategy} {remark}"
            )
        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        except Exception:
            pass

    # ================= 连续预测（无新数据也持续） =================
    def _append_live_record(self, rec: Dict[str, object], max_lines: int = 2000) -> None:
        self._ensure_io_dirs()
        try:
            # 1) 追加 JSONL
            with open(self._live_jsonl, 'a', encoding='utf-8') as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            # 2) 写 latest 静态 JSON
            with open(self._live_latest, 'w', encoding='utf-8') as f:
                json.dump(rec, f, ensure_ascii=False, indent=2)
            # 3) 简易截断（保持最近 max_lines 行）
            try:
                with open(self._live_jsonl, 'r', encoding='utf-8') as rf:
                    lines = rf.readlines()
                if len(lines) > max_lines:
                    with open(self._live_jsonl, 'w', encoding='utf-8') as wf:
                        wf.writelines(lines[-max_lines:])
            except Exception:
                pass
        except Exception:
            pass

    def run_continuous_live(self) -> None:
        """在无新数据的前提下，也持续用不同算法循环预测，定期产出候选与融合结果。
        环境变量控制：
          - SSQ_CONT_INTERVAL: 周期秒（默认 60）
          - SSQ_CONT_CANDIDATES: 每周期融合多候选数量（默认 5）
          - SSQ_CONT_MAX_LOG: live JSONL 最多行数（默认 2000）
          - SSQ_CONT_MAX_TICKS: 最大循环次数（默认无限，用于验证）
        """
        try:
            interval = float(os.getenv('SSQ_CONT_INTERVAL', '60'))
        except Exception:
            interval = 60.0
        try:
            n_cands = int(float(os.getenv('SSQ_CONT_CANDIDATES', '5')))
        except Exception:
            n_cands = 5
        try:
            max_lines = int(float(os.getenv('SSQ_CONT_MAX_LOG', '2000')))
        except Exception:
            max_lines = 2000
        try:
            max_ticks_env = os.getenv('SSQ_CONT_MAX_TICKS')
            max_ticks = int(max_ticks_env) if max_ticks_env else None
        except Exception:
            max_ticks = None

        self._ensure_io_dirs()
        tick = 0
        base_idx = len(self.history) - 1 if self.history else 0
        while True:
            now_ts = time.time()
            # 虚拟期次索引：随 tick 增长，驱动部分策略参数变化
            virt_idx = base_idx + tick
            # 逐策略出数
            attempts: List[Dict[str, object]] = []
            for model in self.models:
                try:
                    if model == 'liuyao': pr, pb = self.predict_liuyao(virt_idx)
                    elif model == 'liuren': pr, pb = self.predict_liuren(virt_idx)
                    elif model == 'qimen': pr, pb = self.predict_qimen(virt_idx)
                    elif model == 'ai': pr, pb = self.predict_ai(virt_idx)
                    elif model == 'cultural_dl': pr, pb = self.predict_cultural_dl(virt_idx)
                    else: pr, pb = self.predict_ai(virt_idx)
                except Exception:
                    # 单策略失败时退化随机
                    pr, pb = self._random_numbers()
                attempts.append({'strategy': model, 'pred_reds': pr, 'pred_blue': pb})
            # 单组融合与多候选
            try:
                fused_reds, fused_blue = self._fuse_from_attempts(attempts)
            except Exception:
                fused_reds, fused_blue = self._random_numbers()
            try:
                candidates = self.generate_candidates_from_attempts(attempts, count=max(1, min(50, n_cands)))
            except Exception:
                candidates = [{'reds': sorted(self._random_numbers()[0]), 'blue': self._random_numbers()[1]}]
            rec = {
                'ts': now_ts,
                'virtual_issue': virt_idx,
                'params': {
                    'interval': interval,
                    'candidates': n_cands,
                    'temp_red': self.temp_red,
                    'temp_blue': self.temp_blue,
                    'top_p_red': self.top_p_red,
                    'top_p_blue': self.top_p_blue,
                    'alpha_red': self.alpha_red,
                    'alpha_blue': self.alpha_blue,
                    'diversify': self.enforce_candidate_diversity,
                    'max_overlap': getattr(self, 'max_overlap_reds', 3),
                },
                'attempts': attempts,
                'fused': {'reds': sorted(fused_reds), 'blue': int(fused_blue)},
                'candidates': candidates,
            }
            # 自学习：根据候选与融合更新文化记忆（可开关）
            try:
                self._update_cultural_memory({'reds': sorted(fused_reds), 'blue': int(fused_blue)}, candidates)
                rec['culture_learned'] = True
            except Exception:
                rec['culture_learned'] = False
            self._append_live_record(rec, max_lines=max_lines)
            tick += 1
            if max_ticks is not None and tick >= max_ticks:
                break
            try:
                time.sleep(max(0.0, float(interval)))
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    cycle = SSQPredictCycle(data_path='ssq_history.csv')
    # 若开启连续模式，则进入持续循环；否则执行一次闭环复盘
    if os.getenv('SSQ_CONTINUOUS', '0') == '1':
        cycle.run_continuous_live()
    else:
        cycle.run_closed_loop(consult_external=False, max_attempts_per_issue=30)
