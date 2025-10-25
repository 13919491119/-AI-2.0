"""
自动采集八字排盘与阴历阳历转换脚本
- 支持指定出生日期、时辰，自动请求 buyiju 八字排盘接口
- 解析返回结果，采集八字排盘、阴历阳历转换等数据
- 保存为 JSON，便于后续分析与集成
"""
import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = 'https://m.buyiju.com/qiming/bazi/'
OUTPUT_JSON = 'bazi_pan_results.json'

# 构造请求参数（示例：阳历 1990-01-01 08:00）
def build_params(year, month, day, hour, minute=0):
    return {
        'year': year,
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute,
        'sex': 1,  # 男：1，女：0
        'act': 'csshow',
    }

def fetch_bazi_pan(year, month, day, hour, minute=0):
    params = build_params(year, month, day, hour, minute)
    resp = requests.post(BASE_URL, data=params, timeout=10)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')
    result = {}
    # 采集八字排盘结果
    pan_div = soup.find('div', class_='bazi-pan')
    if pan_div:
        result['bazi_pan'] = pan_div.get_text(strip=True)
    # 采集阴历阳历转换
    date_info = soup.find('div', class_='bazi-date')
    if date_info:
        result['date_info'] = date_info.get_text(strip=True)
    return result

def main():
    samples = [
        (1990, 1, 1, 8),
        (2000, 5, 20, 14),
        (2010, 12, 31, 23),
    ]
    results = []
    for y, m, d, h in samples:
        try:
            res = fetch_bazi_pan(y, m, d, h)
            res['input'] = {'year': y, 'month': m, 'day': d, 'hour': h}
            results.append(res)
            print(f"采集成功: {res['input']}")
            time.sleep(1)
        except Exception as e:
            print(f"采集失败: {y}-{m}-{d} {h}: {e}")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'八字排盘与阴阳历转换数据已保存: {OUTPUT_JSON}')

if __name__ == '__main__':
    main()
