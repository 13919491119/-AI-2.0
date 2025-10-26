"""
多源特征融合与深度学习集成
- 将六爻、掌诀等特征编码为AI模型输入
- 构建融合训练集，集成深度学习模型（占位示例）
"""
import pandas as pd # pyright: ignore[reportMissingModuleSource]
from sklearn.ensemble import RandomForestClassifier
import requests
from bs4 import BeautifulSoup

FEATURE_CSV = 'ssq_liuyao_features.csv'
PALM_JSON = 'liuren_palm_win_prob.json'
MODEL_PATH = 'fusion_rf_model.joblib'

# 加载融合特征数据集
def load_features():
    df = pd.read_csv(FEATURE_CSV)
    # 示例：将六爻特征与红球、蓝球、掌诀权重拼接
    for i in range(1,7):
        df[f'六爻{i}'] = df[f'六爻{i}'].astype(int)
    # 掌诀权重（简化：全部用大安权重）
    import json
    with open(PALM_JSON, encoding='utf-8') as f:
        palm_prob = json.load(f)
    daan_weights = [float(palm_prob['大安'].get(str(i),0.0)) for i in range(1,34)]
    for i in range(1,7):
        df[f'掌诀权重{i}'] = daan_weights[i-1]
    return df

def train_model():
    df = load_features()
    # 简化：以六爻+掌诀权重预测红1是否为奇数
    X = df[[f'六爻{i}' for i in range(1,7)] + [f'掌诀权重{i}' for i in range(1,7)]]
    y = (df['红1'] % 2).astype(int)
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    import joblib
    joblib.dump(model, MODEL_PATH)
    print(f'融合深度学习模型已训练并保存: {MODEL_PATH}')

if __name__ == '__main__':
    # 示例：采集指定阳历八字排盘
    def fetch_bazi_pan(year, month, day, hour, minute=0):
        BASE_URL = 'https://m.buyiju.com/qiming/bazi/'
        params = {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'sex': 1,
            'act': 'csshow',
        }
        resp = requests.post(BASE_URL, data=params, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        result = {}
        pan_div = soup.find('div', class_='bazi-pan')
        if pan_div:
            result['bazi_pan'] = pan_div.get_text(strip=True)
        date_info = soup.find('div', class_='bazi-date')
        if date_info:
            result['date_info'] = date_info.get_text(strip=True)
        return result
    bazi_result = fetch_bazi_pan(1976, 11, 13, 11, 30)
    print('1976年11月13日11:30 八字排盘采集结果:')
    print(bazi_result)
    bazi_result_2025 = fetch_bazi_pan(2025, 10, 11, 19, 0)
    print('2025年10月11日19:00 八字排盘采集结果:')
    print(bazi_result_2025)
    # 本地八字排盘（无需网页采集）
    try:
        from bazi_chart import solar2bazi
        bazi_2025 = solar2bazi(2025, 10, 11, 19, 0, 0)
        print('2025年10月11日19:00 八字排盘结果:')
        print('年柱:', bazi_2025.get('year'))
        print('月柱:', bazi_2025.get('month'))
        print('日柱:', bazi_2025.get('day'))
        print('时柱:', bazi_2025.get('hour'))
        print('天干:', bazi_2025.get('gan'))
        print('地支:', bazi_2025.get('zhi'))
        print('生肖:', bazi_2025.get('zodiac'))
        print('农历:', bazi_2025.get('lunar'))
        print('阳历:', bazi_2025.get('solar'))
    except Exception as e:
        print('本地八字排盘失败:', e)
    train_model()
