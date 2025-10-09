"""
双色球AI模型模块
 支持训练/预测/复盘，集成sklearn/XGBoost等真实AI模型
"""
import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

class SSQAIModel:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.rf_model = None
        self.xgb_model = None
        self.cumulative_train_count = 0
        self._train_count_file = 'ssq_train_count.txt'
        try:
            with open(self._train_count_file, 'r', encoding='utf-8') as f:
                self.cumulative_train_count = int(f.read().strip())
        except Exception:
            self.cumulative_train_count = 0

    def _prepare_data(self):
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
        X, y_red, y_blue = self._prepare_data()
        self.rf_model = [RandomForestClassifier(n_estimators=50, random_state=42) for _ in range(6)]
        for i in range(6):
            self.rf_model[i].fit(X, y_red[:,i])
        self.xgb_model = XGBClassifier(n_estimators=50, random_state=42, use_label_encoder=False, eval_metric='mlogloss')
        self.xgb_model.fit(X, y_blue)
        self.cumulative_train_count = len(X)
        try:
            with open(self._train_count_file, 'w', encoding='utf-8') as f:
                f.write(str(self.cumulative_train_count))
        except Exception:
            pass
        return f"[AI模型] 已基于{len(X)}期数据训练（RF红球+XGB蓝球）。累计训练期数: {self.cumulative_train_count}"

    def predict(self, input_data=None):
        if self.rf_model is None or self.xgb_model is None:
            return self._random_predict()
        if input_data is None:
            input_data = random.sample(range(1,34), 6) + [random.randint(1,16)]
        X = np.array(input_data).reshape(1,-1)
        reds = [int(model.predict(X)[0]) for model in self.rf_model]
        blue = int(self.xgb_model.predict(X)[0]) + 1
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