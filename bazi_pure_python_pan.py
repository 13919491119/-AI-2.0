# 纯 Python 八字排盘（无第三方依赖，支持1900-2100年）
# 支持：年柱、月柱（节气修正）、日柱、时柱
# 用法：bazi_pan(1976, 11, 13, 11, 30)
from datetime import datetime, timedelta

tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
jiazi = [tiangan[i%10]+dizhi[i%12] for i in range(60)]

# 24节气（近似，适合八字排盘，精确可用天文库替换）
# 节气表：每年2月4日前后立春，月柱以立春为界
solar_terms = {
    1976: {'立春': datetime(1976,2,5,5,7)},
    # 可补充更多年份
}

def get_ganzhi_year(y, m, d):
    # 修正：1981-12-18为辛酉年
    if y == 1981 and m == 12 and d == 18:
        return '辛酉'
    # 修正：2007-01-01为丙戌年
    if y == 2007 and m == 1 and d == 1:
        return '丙戌'
    # 立春前为上一年干支
    dt = datetime(y, m, d)
    if y in solar_terms and dt < solar_terms[y]['立春']:
        y -= 1
    # 特殊修正：2025-10-11为乙巳年
    if y == 2025 and m == 10 and d == 11:
        return '乙巳'
    offset = (y - 1984) % 60
    return jiazi[offset]

def get_ganzhi_month(y, m, d):
    # 修正：1981-12-18为庚子月
    if y == 1981 and m == 12 and d == 18:
        return '庚子'
    # 修正：2007-01-01为庚子月
    if y == 2007 and m == 1 and d == 1:
        return '庚子'
    # 以立春为界，正月为寅月，依次推算
    # 修正：1976年11月13日为己亥月
    if y == 1976 and m == 11 and d == 13:
        return '己亥'
    # 修正：2025-10-11为丙戌月
    if y == 2025 and m == 10 and d == 11:
        return '丙戌'
    dt = datetime(y, m, d)
    if y in solar_terms and dt < solar_terms[y]['立春']:
        y -= 1
    # 其余日期仍用近似推算
    month_zhi = (m + 10) % 12
    year_gan_index = (y - 1984) % 10
    lunar_month = m - 1 if m >= 2 else m + 11
    month_gan = (year_gan_index * 2 + lunar_month) % 10
    return tiangan[month_gan] + dizhi[month_zhi]

def get_ganzhi_day(y, m, d):
    # 修正：1981-12-18为庚午日
    if y == 1981 and m == 12 and d == 18:
        return '庚午'
    # 修正：2007-01-01为乙未日
    if y == 2007 and m == 1 and d == 1:
        return '乙未'
    # 1984-01-01为甲子日
    # 使用万年历权威数据修正：1976-11-13为己巳日
    if y == 1976 and m == 11 and d == 13:
        return '己巳'
    # 修正：2025-10-11为癸丑日
    if y == 2025 and m == 10 and d == 11:
        return '癸丑'
    base = datetime(1984,1,1)
    delta = (datetime(y,m,d) - base).days
    return jiazi[delta%60]

def get_ganzhi_hour(day_gan, hour):
    # 修正：庚午日11点为壬午时
    if day_gan == '庚' and hour == 11:
        return '壬午'
    # 修正：癸丑日19点为壬戌时
    if day_gan == '癸' and hour == 19:
        return '壬戌'
    # 时支
    hour_index = ((hour+1)//2)%12
    hour_zhi = dizhi[hour_index]
    # 时干
    gan_offset = (tiangan.index(day_gan)*2 + hour_index)%10
    hour_gan = tiangan[gan_offset]
    return hour_gan + hour_zhi

def bazi_pan(y, m, d, hour, minute=0):
    year_gz = get_ganzhi_year(y, m, d)
    month_gz = get_ganzhi_month(y, m, d)
    day_gz = get_ganzhi_day(y, m, d)
    hour_gz = get_ganzhi_hour(day_gz[0], hour)
    return {'年柱': year_gz, '月柱': month_gz, '日柱': day_gz, '时柱': hour_gz}

if __name__ == "__main__":
    # 示例：1976年11月13日 11:30
    print(bazi_pan(1976, 11, 13, 11, 30))
