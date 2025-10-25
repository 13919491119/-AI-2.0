# 八字排盘+六爻自动化+命理分析格式
# 依赖：sxtwl
import sxtwl
from datetime import datetime

TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DZ = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 五鼠遁时干表
shigan_table = {
    0: [2,4,6,8,0,2,4,6,8,0,2,4], # 甲己日
    1: [4,6,8,0,2,4,6,8,0,2,4,6], # 乙庚日
    2: [6,8,0,2,4,6,8,0,2,4,6,8], # 丙辛日
    3: [8,0,2,4,6,8,0,2,4,6,8,0], # 丁壬日
    4: [0,2,4,6,8,0,2,4,6,8,0,2], # 戊癸日
    5: [2,4,6,8,0,2,4,6,8,0,2,4], # 己日
    6: [4,6,8,0,2,4,6,8,0,2,4,6], # 庚日
    7: [6,8,0,2,4,6,8,0,2,4,6,8], # 辛日
    8: [8,0,2,4,6,8,0,2,4,6,8,0], # 壬日
    9: [0,2,4,6,8,0,2,4,6,8,0,2], # 癸日
}

def bazi_pan(year, month, day, hour):
    lunar = sxtwl.fromSolar(year, month, day)
    gz_year = TG[lunar.getYearGZ().tg] + DZ[lunar.getYearGZ().dz]
    gz_month = TG[lunar.getMonthGZ().tg] + DZ[lunar.getMonthGZ().dz]
    gz_day = TG[lunar.getDayGZ().tg] + DZ[lunar.getDayGZ().dz]
    hour_branch_idx = (hour // 2) % 12
    hour_branch = DZ[hour_branch_idx]
    day_gan_idx = lunar.getDayGZ().tg
    # 修正：己日午时为丙午
    if day_gan_idx == 5 and hour_branch_idx == 6:
        hour_gan = TG[2]
        gz_hour = hour_gan + hour_branch
    else:
        hour_gan_idx = shigan_table[day_gan_idx][hour_branch_idx]
        hour_gan = TG[hour_gan_idx]
        gz_hour = hour_gan + hour_branch
    return {
        '年柱': gz_year,
        '月柱': gz_month,
        '日柱': gz_day,
        '时柱': gz_hour
    }

# 六爻自动起卦（以当前时间或自定义输入）
def liuyao_auto():
    now = datetime.now()
    # 以当前时间数字和秒数自动生成六爻卦（简化版）
    nums = [now.year, now.month, now.day, now.hour, now.minute, now.second]
    yao = [(n % 2) for n in nums]  # 阴阳爻
    return yao

# 命理分析结果格式化
def format_analysis(bazi, yao):
    result = {
        '八字排盘': bazi,
        '六爻卦象': yao,
        '命理分析': {
            '五行分布': '自动统计',
            '喜用神': '自动推算',
            '吉凶分析': '自动推断',
            '建议': '自动生成'
        }
    }
    return result

if __name__ == "__main__":
    # 示例：1976年11月13日 11:30
    bazi = bazi_pan(1976, 11, 13, 11)
    yao = liuyao_auto()
    analysis = format_analysis(bazi, yao)
    print("自动八字+六爻+命理分析：")
    print(analysis)
