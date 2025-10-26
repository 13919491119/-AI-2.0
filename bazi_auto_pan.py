# 八字自动排盘脚本
# 依赖：lunarcalendar
from lunarcalendar import Converter, Solar, Lunar
from datetime import datetime

# 输入：阴历生日、出生时辰（24小时制）、性别、出生地
# 示例：2025年10月11日 19点 女 青岛

def lunar_to_solar(year, month, day):
    lunar = Lunar(year, month, day, isleap=False)
    solar = Converter.Lunar2Solar(lunar)
    return solar

def get_bazi(year, month, day, hour):
    # 这里只做演示，实际八字排盘需结合天干地支算法
    # 可扩展：用专业八字库如 sxtwl 或 openbazi
    # 返回：年柱、月柱、日柱、时柱
    # 这里只返回阳历和时辰，八字算法可后续补充
    solar = lunar_to_solar(year, month, day)
    solar_str = f"{solar.year}-{solar.month}-{solar.day} {hour}:00"
    return {
        "阳历": solar_str,
        "八字排盘": "（此处可集成天干地支算法，自动输出年柱、月柱、日柱、时柱）"
    }

if __name__ == "__main__":
    # 示例：2025年10月11日（阴历），19点
    lunar_year = 2025
    lunar_month = 10
    lunar_day = 11
    hour = 19
    result = get_bazi(lunar_year, lunar_month, lunar_day, hour)
    print("自动八字排盘结果：")
    print(result)
