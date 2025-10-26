"""
夫妻八字专项预测脚本
- 输入夫妻双方阳历出生时间，自动排盘并分析流年、流月、子女、事业等专项预测（简化版）
- 输出双方八字排盘、五行分布、流年流月五行变化、子女与事业趋势建议
"""
from collections import Counter
from bazi_chart import solar2bazi
from datetime import datetime
zhi_map = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}

def get_wuxing(gan_zhi):
    gan_map = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    wuxing = []
    for g in gan_zhi['gan']:
        wuxing.append(gan_map.get(g,'未知'))
    for z in gan_zhi['zhi']:
        wuxing.append(zhi_map.get(z,'未知'))
    return Counter(wuxing)

def liunian_liuyue(y, m, d, H, M, years=5):
    liunian_gan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    liunian_zhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    now = datetime.now()
    base_year = now.year
    print('\n流年五行变化（未来5年）:')
    wx_count = Counter()
    yearly_details = []
    for i in range(years):
        year = base_year + i
        gan = liunian_gan[(year-4)%10]
        zhi = liunian_zhi[(year-4)%12]
        gan_wx = get_wuxing({'gan':[gan],'zhi':[zhi]})
        wx_str = ', '.join([f'{k}={v}' for k,v in gan_wx.items()])
        yearly_details.append({'year': year, 'gan': gan, 'zhi': zhi, 'wx': dict(gan_wx)})
        print(f'{year}年: 天干{gan} 地支{zhi} | 五行: {wx_str}')
        wx_count += gan_wx
    print(f'五年流年五行总计: {dict(wx_count)}')
    # 细化健康、财运专项分析
    print('\n【健康专项预测 - 细化】')
    # 当五行偏弱或偏强时给出生活方式建议
    dominant = [k for k,v in wx_count.items() if v >= 3]
    weak = [k for k,v in wx_count.items() if v == 0]
    if dominant:
        for d in dominant:
            if d == '水':
                print('水旺：注意肾脏、泌尿系统，建议少盐多钾、避免熬夜，适量游泳/温泉放松。')
            if d == '火':
                print('火旺：注意心血管与情绪管理，建议有氧运动、戒烟限酒、冥想或规律作息。')
            if d == '土':
                print('土旺：注意脾胃消化，建议清淡饮食、少油腻、多纤维，定期体检胃肠道。')
            if d == '金':
                print('金旺：注意呼吸系统与皮肤，建议室内空气质量管理、适度户外活动、少接触刺激性物质。')
            if d == '木':
                print('木旺：注意肝胆和筋骨，建议戒酒保肝、适度拉伸与力量训练。')
    if weak:
        for w in weak:
            if w == '水':
                print('水弱：补水与休息，增加黑色食物如黑芝麻、黑豆，注意补肾养生。')
            if w == '火':
                print('火弱：适当增加日照与辛温食物，参加社交与演讲提升活力。')
            if w == '土':
                print('土弱：饮食规律、少生冷，适当吃山药、薯类稳固脾胃。')
            if w == '金':
                print('金弱：加强呼吸训练、吃白色食物如梨、萝卜，注意保温防寒。')
            if w == '木':
                print('木弱：增加绿色蔬菜、户外活动，注意疏导情绪与增强筋骨。')

    print('\n【财运专项预测 - 细化】')
    # 提供短期/中期/长期理财策略建议
    if wx_count['土'] + wx_count['金'] >= 6:
        print('- 总体：财富积累期，风险承受能力较高，适合配置低中风险长期资产（房地产/稳健基金）。')
        print('- 短期：可把部分闲置资金参与短期理财或货币基金以提高流动性。')
        print('- 中期：优先配置债券基金与蓝筹股，关注通胀与税务规划。')
        print('- 长期：持续定投优质资产，配置固定收益和实物资产以稳固财富。')
    elif wx_count['木'] + wx_count['水'] >= 6:
        print('- 总体：财富有波动，适合创新与创业投资，但需控制仓位与分散风险。')
        print('- 短期：保持流动性，避免高杠杆投机。')
        print('- 中期：关注成长型行业（科技、消费升级），小仓位尝试新机会。')
        print('- 长期：构建多元化组合，保留现金以应对波动。')
    else:
        print('- 总体：稳健为主，建议资产配置均衡，侧重长期价值投资与紧急备用金。')
        print('- 短期：保持3-6个月的生活费作为流动性保障。')
        print('- 中期：低风险固定收益类产品为主，逐步增加股票类配置。')
        print('- 长期：复利为王，保持定投与资产再平衡。')
    # 返回统计供上层调用
    return {'wx_count': dict(wx_count), 'yearly': yearly_details}
    print('\n流月五行变化（未来12月）:')
    for i in range(12):
        month = (now.month + i - 1) % 12 + 1
        zhi = liunian_zhi[(month-1)%12]
        print(f'{month}月: 地支{zhi} | 五行: {zhi_map.get(zhi,"未知")}')

def predict_children(wuxing_w, wuxing_h):
    print('\n【子女趋势预测】')
    if wuxing_w['火'] + wuxing_h['火'] > 3:
        print('子女缘较旺，易有子女或子女活力充沛。')
    elif wuxing_w['水'] + wuxing_h['水'] > 2:
        print('子女缘变动，注意健康与沟通。')
    else:
        print('子女缘一般，建议顺其自然。')

def predict_career(wuxing_w, wuxing_h):
    print('\n【事业趋势预测】')
    if wuxing_w['土'] + wuxing_h['土'] > 3:
        print('事业稳定，适合积累财富、长期发展。')
    elif wuxing_w['木'] + wuxing_h['木'] > 2:
        print('事业有创新、变动机会，适合创业或转型。')
    elif wuxing_w['金'] + wuxing_h['金'] > 2:
        print('事业有贵人助力，适合合作、管理岗位。')
    else:
        print('事业平稳，建议稳中求进。')

def analyze_couple_special(wife, husband):
    print('【妻子八字排盘】')
    bazi_w = solar2bazi(*wife)
    wuxing_w = get_wuxing(bazi_w)
    print('【丈夫八字排盘】')
    bazi_h = solar2bazi(*husband)
    wuxing_h = get_wuxing(bazi_h)
    liunian_res_w = liunian_liuyue(*wife)
    liunian_res_h = liunian_liuyue(*husband)
    predict_children(wuxing_w, wuxing_h)
    predict_career(wuxing_w, wuxing_h)
    # 个体失衡诊断（示例：夫妻双方五行合并分析）
    combined = Counter()
    combined.update(wuxing_w)
    combined.update(wuxing_h)
    print('\n【夫妻合并五行诊断】')
    print('合并五行分布:', dict(combined))
    # 如果任一五行为0，提示补救建议
    for k in ['水','火','土','金','木']:
        if combined.get(k,0) == 0:
            print(f'五行{k}在家庭中偏弱，建议通过饮食/环境/佩饰等方式进行适度补充。')

if __name__ == '__main__':
    # 妻子：1988-5-27 20:30，丈夫：1987-11-12 20:30
    wife = (1988,5,27,20,30,0)
    husband = (1987,11,12,20,30,0)
    analyze_couple_special(wife, husband)
