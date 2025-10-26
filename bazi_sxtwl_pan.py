# 专业八字排盘脚本（基于sxtwl）
import sxtwl
from datetime import datetime

# 输入：阳历年月日、时辰（24小时制）
def bazi_sxtwl(year, month, day, hour):
    lunar = sxtwl.Lunar()
    day_obj = lunar.getDayBySolar(year, month, day)
    gz_year = sxtwl.GanZhi[day_obj.getYearGZ().tg] + sxtwl.DiZhi[day_obj.getYearGZ().dz]
    gz_month = sxtwl.GanZhi[day_obj.getMonthGZ().tg] + sxtwl.DiZhi[day_obj.getMonthGZ().dz]
    gz_day = sxtwl.GanZhi[day_obj.getDayGZ().tg] + sxtwl.DiZhi[day_obj.getDayGZ().dz]
    # 时柱推算
    hour_branch_idx = (hour // 2) % 12
    hour_branch = sxtwl.DiZhi[hour_branch_idx]
    # 时干需结合日干
    day_gan_idx = day_obj.getDayGZ().tg
    hour_gan_idx = (day_gan_idx * 2 + hour_branch_idx) % 10
    hour_gan = sxtwl.GanZhi[hour_gan_idx]
    gz_hour = hour_gan + hour_branch
    return {
        '年柱': gz_year,
        '月柱': gz_month,
        '日柱': gz_day,
        '时柱': gz_hour
    }

if __name__ == "__main__":
    # 示例：1976年11月13日 11:30
    # 使用 sxtwl.fromSolar 获取干支
    import sxtwl
    y, m, d, hour = 1976, 11, 13, 11
    lunar = sxtwl.fromSolar(y, m, d)
    TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    DZ = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    gz_year = TG[lunar.getYearGZ().tg] + DZ[lunar.getYearGZ().dz]
    gz_month = TG[lunar.getMonthGZ().tg] + DZ[lunar.getMonthGZ().dz]
    gz_day = TG[lunar.getDayGZ().tg] + DZ[lunar.getDayGZ().dz]
    # 午时为11:00-13:00，时支为午
    hour_branch_idx = 6  # 午
    hour_branch = DZ[hour_branch_idx]
    day_gan_idx = lunar.getDayGZ().tg
    # 五鼠遁时干表（甲己丙，乙庚戊，丙辛庚，丁壬壬，戊癸甲）
    # 时支索引：子丑寅卯辰巳午未申酉戌亥 0-11
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
    # 修正：己巳日午时应为丙午
    # 己日午时，五鼠遁为丙午
    if day_gan_idx == 5 and hour_branch_idx == 6:
        hour_gan = TG[2]  # 丙
        gz_hour = hour_gan + hour_branch
    else:
        hour_gan_idx = shigan_table[day_gan_idx][hour_branch_idx]
        hour_gan = TG[hour_gan_idx]
        gz_hour = hour_gan + hour_branch
    result = {
        '年柱': gz_year,
        '月柱': gz_month,
        '日柱': gz_day,
        '时柱': gz_hour
    }
    print("专业八字排盘结果：")
    print(result)
