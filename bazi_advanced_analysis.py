"""
八字高级命理分析脚本（单人）
- 输入阳历出生时间，自动排盘并分析五行分布、格局、用神、流年（简化版）
- 输出年柱、月柱、日柱、时柱、天干、地支、生肖、五行统计、格局、用神建议、流年五行变化
"""
import sys
from collections import Counter
from datetime import datetime

def get_wuxing(gan_zhi):
    gan_map = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    zhi_map = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    wuxing = []
    for g in gan_zhi['gan']:
        wuxing.append(gan_map.get(g,'未知'))
    for z in gan_zhi['zhi']:
        wuxing.append(zhi_map.get(z,'未知'))
    return Counter(wuxing)

def analyze_bazi(y, m, d, H, M):
    from bazi_chart import solar2bazi
    bazi = solar2bazi(y, m, d, H, M, 0)
    print('八字排盘:')
    print('年柱:', bazi.get('year'))
    print('月柱:', bazi.get('month'))
    print('日柱:', bazi.get('day'))
    print('时柱:', bazi.get('hour'))
    print('天干:', bazi.get('gan'))
    print('地支:', bazi.get('zhi'))
    print('生肖:', bazi.get('zodiac'))
    print('农历:', bazi.get('lunar'))
    print('阳历:', bazi.get('solar'))
    wuxing_stat = get_wuxing(bazi)
    print('\n五行分布:')
    for k,v in wuxing_stat.items():
        print(f'{k}: {v}')
    main_wuxing = max(wuxing_stat, key=wuxing_stat.get)
    print(f'主五行（最多）: {main_wuxing}')
    # 格局分析（简化）
    print('\n格局分析:')
    if bazi.get('gan')[2] == '庚':
        print('日主为庚金，格局偏金，宜土生金、忌火克金。')
    elif bazi.get('gan')[2] == '甲':
        print('日主为甲木，格局偏木，宜水生木、忌金克木。')
    elif bazi.get('gan')[2] == '丙':
        print('日主为丙火，格局偏火，宜木生火、忌水克火。')
    else:
        print('日主为', bazi.get('gan')[2], '，请结合实际五行分布综合分析。')
    # 用神细化建议
    print('\n用神细化建议:')
    if main_wuxing == '金':
        print('用神宜土、水，忌火、木过旺。')
    elif main_wuxing == '木':
        print('用神宜水、火，忌金、土过旺。')
    elif main_wuxing == '火':
        print('用神宜木、土，忌水、金过旺。')
    elif main_wuxing == '土':
        print('用神宜火、金，忌木、水过旺。')
    elif main_wuxing == '水':
        print('用神宜金、木，忌土、火过旺。')
    else:
        print('五行分布异常，建议人工复核。')
    # 流年分析（近10年）
    print('\n流年五行变化（近10年）:')
    liunian_gan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    liunian_zhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    for i in range(10):
        year = y + i
        gan = liunian_gan[(year-4)%10]
        zhi = liunian_zhi[(year-4)%12]
        gan_wx = get_wuxing({'gan':[gan],'zhi':[zhi]})
        wx_str = ', '.join([f'{k}={v}' for k,v in gan_wx.items()])
        print(f'{year}年: 天干{gan} 地支{zhi} | 五行: {wx_str}')

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print('用法: python3 bazi_advanced_analysis.py YEAR MONTH DAY HOUR MINUTE')
        sys.exit(1)
    y, m, d, H, M = map(int, sys.argv[1:6])
    analyze_bazi(y, m, d, H, M)
