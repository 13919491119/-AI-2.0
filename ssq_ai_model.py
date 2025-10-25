"""
双色球AI模型模块
 支持训练/预测/复盘，集成sklearn/XGBoost等真实AI模型
 在缺少可选依赖（sklearn/xgboost）时自动降级为随机预测，避免导入时崩溃。
"""
import random

def _get_np():
    try:
        import numpy as np  # type: ignore
        return np
    except Exception:
        return None

def _get_sklearn_rf():
    try:
        from sklearn.ensemble import RandomForestClassifier  # type: ignore
        return RandomForestClassifier
    except Exception:
        return None

def _get_xgb():
    try:
        from xgboost import XGBClassifier  # type: ignore
        return XGBClassifier
    except Exception:
        return None

class SSQAIModel:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.rf_model = None
        self.xgb_model = None
        self.cumulative_train_count = 0
        self._train_count_file = 'ssq_train_count.txt'
        self._best_rf_n = 50
        self._blue_alpha = 0.2  # 蓝球概率先验融合强度（训练期自适应）
        self._red_prior_gamma = 0.2  # 红球先验分数权重（预测期用于重排）
        try:
            with open(self._train_count_file, 'r', encoding='utf-8') as f:
                self.cumulative_train_count = int(f.read().strip())
        except Exception:
            self.cumulative_train_count = 0

    def _prepare_data(self):
        np = _get_np()
        if np is None:
            return None, None, None
        history = self.data_manager.history
        X, y_red, y_blue = [], [], []
        for i in range(len(history)-1):
            reds, blue = history[i]
            next_reds, next_blue = history[i+1]
            X.append(reds + [blue])
            y_red.append(next_reds)
            y_blue.append(next_blue - 1)
        return np.array(X), np.array(y_red), np.array(y_blue)

    def train(self):
        np = _get_np()
        RF = _get_sklearn_rf()
        XGB = _get_xgb()
        X, y_red, y_blue = self._prepare_data()
        if np is None or X is None or y_red is None or y_blue is None or RF is None:
            # 依赖不全，降级
            return "[AI模型] 训练降级：缺少 numpy 或 sklearn，使用随机预测占位。"
        # 简单双阶段：时间序列验证选择 n_estimators
        n_candidates = [50, 100, 150]
        best_n = 50
        best_score = -1.0
        try:
            split_idx = int(len(X) * 0.9)
            if split_idx > 10 and split_idx < len(X):
                X_tr, X_val = X[:split_idx], X[split_idx:]
                y_tr, y_val = y_red[:split_idx], y_red[split_idx:]
                for n in n_candidates:
                    models = [RF(n_estimators=n, random_state=42) for _ in range(6)]
                    for i in range(6):
                        models[i].fit(X_tr, y_tr[:, i])
                    # 验证集平均准确率（逐位）
                    val_pred = []
                    for i in range(6):
                        val_pred.append(models[i].predict(X_val))
                    # shape: (6, n_val) -> 转置逐样本
                    correct = 0
                    total = 0
                    for j in range(X_val.shape[0]):
                        for i in range(6):
                            total += 1
                            if int(val_pred[i][j]) == int(y_val[j, i]):
                                correct += 1
                    acc = correct / max(1, total)
                    if acc > best_score:
                        best_score = acc
                        best_n = n
        except Exception:
            best_n = 50
        self._best_rf_n = best_n
        # 用最佳 n 重新训练全量模型
        self.rf_model = [RF(n_estimators=best_n, random_state=42) for _ in range(6)]
        for i in range(6):
            self.rf_model[i].fit(X, y_red[:, i])

        if XGB is not None:
            try:
                self.xgb_model = XGB(n_estimators=50, random_state=42, use_label_encoder=False, eval_metric='mlogloss')
                self.xgb_model.fit(X, y_blue)
                # 校准蓝球概率融合强度 alpha：网格搜索使验证集 top1 准确率最大
                try:
                    split_idx = int(len(X) * 0.9)
                    X_val = X[split_idx:]
                    yv = y_blue[split_idx:]
                    if len(X_val) > 10:
                        # 历史先验分布
                        prior = self._blue_prior_from_history()
                        best_acc = -1.0
                        best_alpha = self._blue_alpha
                        for alpha in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
                            correct = 0
                            for j in range(X_val.shape[0]):
                                proba = self.xgb_model.predict_proba(X_val[j:j+1])
                                if proba is None:
                                    continue
                                p = _get_np().array(proba).reshape(-1)
                                calib = (1 - alpha) * p[:16] + alpha * prior
                                pred = int(_get_np().argmax(calib)) + 1
                                if pred == int(yv[j]) + 1:
                                    correct += 1
                            acc = correct / max(1, len(X_val))
                            if acc > best_acc:
                                best_acc = acc
                                best_alpha = alpha
                        self._blue_alpha = best_alpha
                except Exception:
                    pass
            except Exception:
                self.xgb_model = None
        else:
            self.xgb_model = None

        self.cumulative_train_count = len(X)
        try:
            with open(self._train_count_file, 'w', encoding='utf-8') as f:
                f.write(str(self.cumulative_train_count))
        except Exception:
            pass
        used = "RF红球+XGB蓝球" if self.xgb_model is not None else "仅RF红球（蓝球随机）"
        return (
            f"[AI模型] 已基于{len(X)}期数据训练（{used}，RF n_estimators={self._best_rf_n}，val_acc={best_score if best_score>=0 else 'NA'}，blue_alpha={self._blue_alpha}）。"
            f"累计训练期数: {self.cumulative_train_count}"
        )

    def _red_frequency_prior(self):
        # 历史红球频率先验（归一化）
        history = self.data_manager.history
        freq = {i: 0 for i in range(1, 34)}
        for reds, _ in history:
            for r in reds:
                if 1 <= r <= 33:
                    freq[r] += 1
        total = float(sum(freq.values())) or 1.0
        return {i: (freq[i] / total) for i in range(1, 34)}

    def _blue_prior_from_history(self):
        # 历史蓝球频率先验（长度16的数组）
        np = _get_np()
        freq = [0.0] * 16
        try:
            for _, b in self.data_manager.history:
                if 1 <= int(b) <= 16:
                    freq[int(b) - 1] += 1.0
            arr = np.array(freq, dtype=float)
            s = float(arr.sum()) or 1.0
            return (arr / s).reshape(-1)
        except Exception:
            return np.ones(16, dtype=float) / 16.0

    def predict(self, input_data=None):
        np = _get_np()
        if self.rf_model is None or np is None:
            return self._random_predict()
        if input_data is None:
            input_data = random.sample(range(1,34), 6) + [random.randint(1,16)]
        X = np.array(input_data).reshape(1,-1)
        # 初始按位预测
        reds = [int(model.predict(X)[0]) for model in self.rf_model]
        # 去重与兜底：保证红球唯一且在1..33
        uniques = []
        seen = set()
        for r in reds:
            r = int(r)
            if r < 1 or r > 33:
                continue
            if r not in seen:
                seen.add(r)
                uniques.append(r)
        # 不足部分：优先用历史热号兜底，其次随机
        try:
            hot, _ = self.data_manager.get_hot_cold()
        except Exception:
            hot = []
        for h in hot:
            if len(uniques) >= 6:
                break
            if h not in seen and 1 <= h <= 33:
                seen.add(h)
                uniques.append(h)
        while len(uniques) < 6:
            c = random.randint(1,33)
            if c not in seen:
                seen.add(c)
                uniques.append(c)
        # 基于历史先验对候选进行重排（正则化）
        prior = self._red_frequency_prior()
        gamma = float(self._red_prior_gamma)
        candidates = list(set(uniques + hot))
        scores = {c: (1.0 + gamma * prior.get(c, 0.0)) for c in candidates}
        reds = sorted(candidates, key=lambda x: scores.get(x, 0.0), reverse=True)[:6]
        if self.xgb_model is not None:
            try:
                # 优先采用概率并用历史先验进行平滑校准
                blue = None
                try:
                    proba = self.xgb_model.predict_proba(X)
                    if proba is not None:
                        proba = np.array(proba).reshape(-1)
                        # 历史先验：蓝球出现频率
                        prior = self._blue_prior_from_history()
                        alpha = float(self._blue_alpha)
                        calib = (1 - alpha) * proba[:16] + alpha * prior.reshape(-1)
                        idx = int(np.argmax(calib))
                        blue = idx + 1
                except Exception:
                    blue = None
                if blue is None:
                    blue = int(self.xgb_model.predict(X)[0]) + 1
            except Exception:
                blue = random.randint(1,16)
        else:
            blue = random.randint(1,16)
        return reds, blue

    def _random_predict(self):
        reds = random.sample(range(1,34), 6)
        blue = random.randint(1,16)
        return reds, blue

    def review(self, top_n=6):
        if self.rf_model is None or self.xgb_model is None:
            return "[AI模型] 复盘：模型未训练，无法评估。"

    def auto_cycle(self, cycles=3):
        logs = []
        for i in range(cycles):
            train_log = self.train()
            review_log = self.review()
            learn_log = f"[学习] 第{i+1}轮：采集新数据/参数微调（占位）"
            upgrade_log = f"[升级] 第{i+1}轮：模型结构优化/权重调整（占位）"
            logs.append(f"---第{i+1}轮---\n{train_log}\n{review_log}\n{learn_log}\n{upgrade_log}")
        return '\n'.join(logs)

    # 新增：输出红蓝分布用于融合/评估
    def get_distributions(self):
        np = _get_np()
        # 红球：使用历史频率先验作为近似分布
        red_prior = self._red_frequency_prior()
        red_p = np.array([red_prior[i] for i in range(1,34)], dtype=float)
        red_p = red_p / (float(red_p.sum()) or 1.0)
        # 蓝球：若有模型概率则返回校准后分布，否则历史先验
        if self.xgb_model is not None:
            try:
                # 构造一个默认输入（使用最近一期红+蓝作为特征）
                hist = self.data_manager.history
                if hist:
                    last_reds, last_blue = hist[-1]
                    X = np.array(last_reds + [last_blue]).reshape(1, -1)
                else:
                    X = np.array(random.sample(range(1,34), 6) + [random.randint(1,16)]).reshape(1, -1)
                proba = self.xgb_model.predict_proba(X)
                if proba is not None:
                    p = np.array(proba).reshape(-1)[:16]
                    prior = self._blue_prior_from_history().reshape(-1)
                    alpha = float(self._blue_alpha)
                    blue_p = (1 - alpha) * p + alpha * prior
                    blue_p = blue_p / (float(blue_p.sum()) or 1.0)
                else:
                    blue_p = self._blue_prior_from_history()
            except Exception:
                blue_p = self._blue_prior_from_history()
        else:
            blue_p = self._blue_prior_from_history()
        return red_p.tolist(), (blue_p.reshape(-1).tolist() if hasattr(blue_p, 'reshape') else list(blue_p))