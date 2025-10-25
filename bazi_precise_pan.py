# 自动化八字精准排盘脚本
# 依赖：lunarcalendar、sxtwl（如需更专业可扩展）
from lunarcalendar import Converter, Solar, Lunar
from datetime import datetime

# 八字天干地支表
TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 六十甲子表
JIAZI = [TIANGAN[i%10]+DIZHI[i%12] for i in range(60)]

def get_ganzhi_year(year):
    # 以1984甲子年为基准
    offset = (year - 1984) % 60
    return JIAZI[offset]

def get_ganzhi_month(year, month):
    # 月干支需结合年干支和节气，简化算法：
    # 通常正月为丙寅，依次推算
    base = ['丙寅','丁卯','戊辰','己巳','庚午','辛未','壬申','癸酉','甲戌','乙亥','丙子','丁丑']
    offset = (month - 1) % 12
    return base[offset]

def get_ganzhi_day(date):
    # 需用万年历或专业库，简化：用1984-01-01为甲子日
    base_date = datetime(1984,1,1)
    delta = (date - base_date).days
    idx = delta % 60
    return JIAZI[idx]

def get_ganzhi_hour(day_gan, hour):
    # 时柱干支，需结合日干
    hour_branch = DIZHI[(hour//2)%12]
    # 时干推算，简化：甲日甲子时，依次推算
    gan_offset = (TIANGAN.index(day_gan)*2 + hour//2)%10
    hour_gan = TIANGAN[gan_offset]
    return hour_gan + hour_branch

def bazi_pan(y, m, d, hour):
    solar_date = datetime(y, m, d)
    year_gz = get_ganzhi_year(y)
    month_gz = get_ganzhi_month(y, m)
    day_gz = get_ganzhi_day(solar_date)
    day_gan = day_gz[0]
    hour_gz = get_ganzhi_hour(day_gan, hour)
    return {
        '年柱': year_gz,
        '月柱': month_gz,
        '日柱': day_gz,
        '时柱': hour_gz
    }

if __name__ == "__main__":
    # 示例：1976年11月13日 11:30
    result = bazi_pan(1976, 11, 13, 11)
    print("八字排盘结果：")
    print(result)
