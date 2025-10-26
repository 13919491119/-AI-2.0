"""
夫妻八字匹配与家庭预测分析脚本
- 输入夫妻双方阳历出生时间，自动排盘并分析五行互补、格局、用神、生肖、流年变化
- 输出双方八字排盘、五行分布、匹配度建议、未来家庭主要变化预测（简化版）
"""
from collections import Counter
from bazi_chart import solar2bazi

def get_wuxing(gan_zhi):
    gan_map = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    zhi_map = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    wuxing = []
    for g in gan_zhi['gan']:
        wuxing.append(gan_map.get(g,'未知'))
    for z in gan_zhi['zhi']:
        wuxing.append(zhi_map.get(z,'未知'))
    return Counter(wuxing)

def analyze_couple(wife, husband):
    print('【妻子八字排盘】')
    bazi_w = solar2bazi(*wife)
    print('年柱:', bazi_w.get('year'))
    print('月柱:', bazi_w.get('month'))
    print('日柱:', bazi_w.get('day'))
    print('时柱:', bazi_w.get('hour'))
    print('天干:', bazi_w.get('gan'))
    print('地支:', bazi_w.get('zhi'))
    print('生肖:', bazi_w.get('zodiac'))
    wuxing_w = get_wuxing(bazi_w)
    print('五行分布:', dict(wuxing_w))
    print('\n【丈夫八字排盘】')
    bazi_h = solar2bazi(*husband)
    print('年柱:', bazi_h.get('year'))
    print('月柱:', bazi_h.get('month'))
    print('日柱:', bazi_h.get('day'))
    print('时柱:', bazi_h.get('hour'))
    print('天干:', bazi_h.get('gan'))
    print('地支:', bazi_h.get('zhi'))
    print('生肖:', bazi_h.get('zodiac'))
    wuxing_h = get_wuxing(bazi_h)
    print('五行分布:', dict(wuxing_h))
    # 匹配度分析
    print('\n【五行互补与匹配度分析】')
    match_score = sum(min(wuxing_w[k], wuxing_h[k]) for k in ['金','木','水','火','土'])
    print(f'五行互补分数: {match_score}（越高越互补）')
    if match_score >= 5:
        print('五行互补良好，家庭和谐基础较强。')
    elif match_score >= 3:
        print('五行互补一般，需注意性格与健康互补。')
    else:
        print('五行互补较弱，建议加强沟通与调和。')
    # 生肖关系
    print('\n【生肖关系】')
    print(f'妻子生肖: {bazi_w.get("zodiac")}，丈夫生肖: {bazi_h.get("zodiac")})')
    # 未来家庭预测（简化）
    print('\n【未来家庭主要变化预测】')
    if wuxing_w['水'] + wuxing_h['水'] > 2:
        print('家庭易有变动、迁居、事业调整。')
    if wuxing_w['火'] + wuxing_h['火'] > 3:
        print('家庭活力充沛，易有子女、创业、健康需关注。')
    if wuxing_w['土'] + wuxing_h['土'] > 3:
        print('家庭稳定，财产积累较好，但需防固执与沟通障碍。')
    print('流年影响建议：关注双方八字主五行与流年五行变化，适时调整家庭规划。')

if __name__ == '__main__':
    # 妻子：1988-5-27 20:30，丈夫：1987-11-12 20:30
    wife = (1988,5,27,20,30,0)
    husband = (1987,11,12,20,30,0)
    analyze_couple(wife, husband)
