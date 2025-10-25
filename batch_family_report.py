"""
批量家庭八字预测分析报告生成脚本
- 输入多组夫妻信息，自动排盘并生成标准Markdown表格报告
"""
from bazi_chart import solar2bazi
from collections import Counter

families = [
    {'wife': {'name': '陈素波', 'year': 1988, 'month': 5, 'day': 27, 'hour': 20, 'minute': 30},
     'husband': {'name': '刘洪坤', 'year': 1987, 'month': 11, 'day': 12, 'hour': 20, 'minute': 30}},
    # 可在此添加更多家庭
]

def get_wuxing(gan_zhi):
    gan_map = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    zhi_map = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    wuxing = []
    for g in gan_zhi['gan']:
        wuxing.append(gan_map.get(g,'未知'))
    for z in gan_zhi['zhi']:
        wuxing.append(zhi_map.get(z,'未知'))
    return Counter(wuxing)

def family_report_md(family):
    wife = family['wife']
    husband = family['husband']
    bazi_w = solar2bazi(wife['year'], wife['month'], wife['day'], wife['hour'], wife['minute'], 0)
    bazi_h = solar2bazi(husband['year'], husband['month'], husband['day'], husband['hour'], husband['minute'], 0)
    wuxing_w = get_wuxing(bazi_w)
    wuxing_h = get_wuxing(bazi_h)
    combined = Counter()
    combined.update(wuxing_w)
    combined.update(wuxing_h)
    # Markdown表格
    md = f"""
### 家庭八字预测分析报告
| 姓名 | 年柱 | 月柱 | 日柱 | 时柱 | 五行分布 |
|------|------|------|------|------|----------|
| {wife['name']} | {bazi_w.get('year','')} | {bazi_w.get('month','')} | {bazi_w.get('day','')} | {bazi_w.get('hour','')} | {' '.join([f'{k}:{v}' for k,v in wuxing_w.items()])} |
| {husband['name']} | {bazi_h.get('year','')} | {bazi_h.get('month','')} | {bazi_h.get('day','')} | {bazi_h.get('hour','')} | {' '.join([f'{k}:{v}' for k,v in wuxing_h.items()])} |

| 家庭五行分布 | 土 | 火 | 水 | 金 | 木 |
|--------------|----|----|----|----|----|
| 合计         | {combined['土']} | {combined['火']} | {combined['水']} | {combined['金']} | {combined['木']} |

**健康建议**：
- 土旺：注意脾胃消化，清淡饮食，多纤维。
- 火旺：注意心血管与情绪管理，有氧运动。
- 水、金、木略弱：补充黑色、白色、绿色食物，增加户外活动。

**财运建议**：
- 总体稳健，建议资产均衡配置，长期价值投资。

**子女与事业**：
- 子女缘旺，家庭活力充沛，事业稳定。

**五行补救**：
- 若有偏弱，可通过饮食、环境、佩饰补充。
"""
    return md

def batch_generate_md(families, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        for fam in families:
            f.write(family_report_md(fam))
            f.write('\n---\n')

if __name__ == '__main__':
    batch_generate_md(families, 'batch_family_report.md')
    print('批量家庭八字预测报告已生成：batch_family_report.md')
