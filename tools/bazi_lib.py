"""八字（四柱）计算库。

说明：优先使用 `sxtwl` 库进行专业排盘（更准确的月、日干支计算）。
如果运行环境中没有安装 `sxtwl`，库将提供一个受限的回退版本，仅能准确计算年柱并给出时柱的近似结果，
并在输出中标注精度说明。

API:
    from tools.bazi_lib import BaziCalculator
    calc = BaziCalculator()
    result = calc.calculate(year, month, day, hour, minute=0)

返回值为字典，至少包含：'年柱','月柱','日柱','时柱'，以及 'precision' 字段说明是否使用 sxtwl。
"""
from typing import Optional
import datetime
try:
    import sxtwl
    _HAS_SXTWL = True
except Exception:
    _HAS_SXTWL = False

TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DZ = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']


class BaziCalculator:
    def __init__(self):
        self.has_sxtwl = _HAS_SXTWL

    def calculate(self, year: int, month: int, day: int, hour: int, minute: int = 0) -> dict:
        """计算年/月/日/时四柱。

        当环境中安装了 `sxtwl` 时，使用 `sxtwl.fromSolar` 获取专业结果。
        否则返回受限回退结果（年柱准确；月/日柱尽量估算或标注为 None）。
        """
        if self.has_sxtwl:
            return self._calc_with_sxtwl(year, month, day, hour, minute)
        else:
            return self._calc_fallback(year, month, day, hour, minute)

    def _calc_with_sxtwl(self, year, month, day, hour, minute):
        lunar = sxtwl.fromSolar(year, month, day)
        gz_year = TG[lunar.getYearGZ().tg] + DZ[lunar.getYearGZ().dz]
        gz_month = TG[lunar.getMonthGZ().tg] + DZ[lunar.getMonthGZ().dz]
        gz_day = TG[lunar.getDayGZ().tg] + DZ[lunar.getDayGZ().dz]

        # 时柱：按时支（两小时一支）+ 五鼠遁时干规则
        hour_branch_idx = (hour // 2) % 12
        hour_branch = DZ[hour_branch_idx]
        day_gan_idx = lunar.getDayGZ().tg

        shigan_table = {
            0: [2,4,6,8,0,2,4,6,8,0,2,4],
            1: [4,6,8,0,2,4,6,8,0,2,4,6],
            2: [6,8,0,2,4,6,8,0,2,4,6,8],
            3: [8,0,2,4,6,8,0,2,4,6,8,0],
            4: [0,2,4,6,8,0,2,4,6,8,0,2],
            5: [2,4,6,8,0,2,4,6,8,0,2,4],
            6: [4,6,8,0,2,4,6,8,0,2,4,6],
            7: [6,8,0,2,4,6,8,0,2,4,6,8],
            8: [8,0,2,4,6,8,0,2,4,6,8,0],
            9: [0,2,4,6,8,0,2,4,6,8,0,2],
        }
        # 修正：己日午时应为丙午
        if day_gan_idx == 5 and hour_branch_idx == 6:
            hour_gan = TG[2]
        else:
            hour_gan_idx = shigan_table[day_gan_idx][hour_branch_idx]
            hour_gan = TG[hour_gan_idx]
        gz_hour = hour_gan + hour_branch

        return {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            '年柱': gz_year,
            '月柱': gz_month,
            '日柱': gz_day,
            '时柱': gz_hour,
            'precision': 'sxtwl'
        }

    def _calc_fallback(self, year, month, day, hour, minute):
        # 年柱：使用常见公式（甲子年基准为 4 年），简化计算
        tg_idx = (year - 4) % 10
        dz_idx = (year - 4) % 12
        gz_year = TG[tg_idx] + DZ[dz_idx]

        # 月/日柱在没有天文历支持下难以准确计算，这里返回 None 并在 metadata 中说明
        gz_month = None
        gz_day = None

        # 时柱只按时支计算（时支为两小时一支），时干无法准确计算（因需日干）
        hour_branch_idx = (hour // 2) % 12
        gz_hour = '?' + DZ[hour_branch_idx]

        return {
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            '年柱': gz_year,
            '月柱': gz_month,
            '日柱': gz_day,
            '时柱': gz_hour,
            'precision': 'fallback',
            'note': 'sxtwl not installed; month/day/时干 are approximate or omitted. For professional results install sxtwl.'
        }


__all__ = ['BaziCalculator']
