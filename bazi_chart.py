"""
自动排盘模块（增强版）：基于 lunar-python 完成公历/农历与八字（干支四柱）换算。
- 新增 tz 时区参数（Asia/Shanghai、UTC、UTC+8、UTC-5 等），会先换算到北京时间再排盘。
- 新增 sect 参数（1/2）用于“晚子时”流派切换（影响日柱计算）。
提供：
- solar2bazi(公历, tz, sect)
- lunar2bazi(农历, tz, sect)
返回四柱干支、天干/地支拆分、生肖、节气与中/西历对应信息。
"""
from __future__ import annotations

from typing import Dict, Any, Tuple, Optional
import datetime as _dt
try:
    from zoneinfo import ZoneInfo as _ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    _ZoneInfo = None  # type: ignore
Solar = None  # type: ignore
Lunar = None  # type: ignore
EightChar = None  # type: ignore


def _parse_tz(tz: Optional[str]) -> _dt.tzinfo:
    """解析时区字符串：优先 IANA 名称（如 Asia/Shanghai），其次 UTC±偏移。
    未识别时返回 UTC。
    """
    s = (tz or '').strip()
    # IANA 时区
    if _ZoneInfo is not None and s and '/' in s:
        try:
            return _ZoneInfo(s)
        except Exception:
            pass
    # UTC±HH[:MM]
    if s.upper().startswith('UTC') or s.upper().startswith('GMT'):
        try:
            base = s[0:3].upper()
            rest = s[3:]
            if not rest:
                return _dt.timezone(_dt.timedelta(0), name='UTC')
            sign = 1
            if rest[0] == '+':
                sign = 1
                rest = rest[1:]
            elif rest[0] == '-':
                sign = -1
                rest = rest[1:]
            parts = rest.split(':')
            h = int(parts[0]) if parts and parts[0] else 0
            m = int(parts[1]) if len(parts) > 1 else 0
            delta = _dt.timedelta(hours=sign * h, minutes=sign * m)
            return _dt.timezone(delta, name=s.upper())
        except Exception:
            return _dt.timezone(_dt.timedelta(0), name='UTC')
    # 特例：Asia/Shanghai 默认
    if _ZoneInfo is not None and s.lower() in ('', 'asia/shanghai', 'cn', 'cst', 'beijing'):
        try:
            return _ZoneInfo('Asia/Shanghai')
        except Exception:
            pass
    # 兜底 UTC
    return _dt.timezone(_dt.timedelta(0), name='UTC')


def _bj_tz() -> _dt.tzinfo:
    if _ZoneInfo is not None:
        try:
            return _ZoneInfo('Asia/Shanghai')
        except Exception:
            pass
    return _dt.timezone(_dt.timedelta(hours=8), name='UTC+8')


def _to_bj_components(year: int, month: int, day: int, hour: int, minute: int, second: int, tz: Optional[str]) -> Tuple[int, int, int, int, int, int]:
    tzinfo = _parse_tz(tz)
    bj = _bj_tz()
    try:
        dt_local = _dt.datetime(year, month, day, hour, minute, second, tzinfo=tzinfo)
    except ValueError:
        # 若时间非法（如 24:00），做简单归一
        dt_local = _dt.datetime(year, month, day, min(max(hour, 0), 23), min(max(minute, 0), 59), min(max(second, 0), 59), tzinfo=tzinfo)
    dt_bj = dt_local.astimezone(bj)
    return dt_bj.year, dt_bj.month, dt_bj.day, dt_bj.hour, dt_bj.minute, dt_bj.second


def _get_gz(lunar: Any, kind: str) -> str:
    """兼容不同版本的 lunar-python 干支方法。kind in {year,month,day,hour}"""
    # 常见方法名：getYearInGanZhi / getYearGanZhi
    name_candidates = {
        'year': ['getYearInGanZhi', 'getYearGanZhi'],
        'month': ['getMonthInGanZhi', 'getMonthGanZhi'],
        'day': ['getDayInGanZhi', 'getDayGanZhi'],
        'hour': ['getTimeInGanZhi', 'getTimeGanZhi'],
    }.get(kind, [])
    for nm in name_candidates:
        fn = getattr(lunar, nm, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    return ''


def _split_gz(gz: Any):
    try:
        if isinstance(gz, str) and len(gz) >= 2:
            return gz[0], gz[1]
    except Exception:
        pass
    return None, None


def _bazi_from_lunar(lunar: Any, sect: int = 2) -> Dict[str, Any]:
    """使用 EightChar 计算四柱，支持 sect 流派切换。"""
    global EightChar
    if EightChar is None:
        from lunar_python import EightChar as _EightChar  # type: ignore
        EightChar = _EightChar
    ec = EightChar.fromLunar(lunar)
    try:
        ec.setSect(1 if int(sect) == 1 else 2)
    except Exception:
        try:
            ec.setSect(2)
        except Exception:
            pass
    # 获取八字四柱（年、月、日、时）天干地支
    y_gz = ec.getYear()
    m_gz = ec.getMonth()
    d_gz = ec.getDay()
    h_gz = ec.getTime()
    yg, yz = _split_gz(y_gz)
    mg, mz = _split_gz(m_gz)
    dg, dz = _split_gz(d_gz)
    hg, hz = _split_gz(h_gz)
    return {
        'year': y_gz,
        'month': m_gz,
        'day': d_gz,
        'hour': h_gz,
        'sect': 1 if int(sect) == 1 else 2,
        'gan': [yg, mg, dg, hg],
        'zhi': [yz, mz, dz, hz],
        'lunar': {
            'year': getattr(lunar, 'getYear', lambda: None)(),
            'month': getattr(lunar, 'getMonth', lambda: None)(),
            'day': getattr(lunar, 'getDay', lambda: None)(),
            'leap': _safe_leap(lunar),
            'month_in_chinese': _safe_call(lunar, ['getMonthInChinese']),
            'day_in_chinese': _safe_call(lunar, ['getDayInChinese']),
        },
        'solar': {
            'year': getattr(lunar.getSolar(), 'getYear', lambda: None)(),
            'month': getattr(lunar.getSolar(), 'getMonth', lambda: None)(),
            'day': getattr(lunar.getSolar(), 'getDay', lambda: None)(),
        },
        'zodiac': getattr(lunar, 'getYearShengXiao', lambda: None)(),
        'jie_qi': _safe_jieqi(lunar),
    }


def _safe_jieqi(lunar: Any):
    # 优先返回当前农历对象的节气名（若可得），否则返回节气表键集合
    # 低版本可能无 getJieQi 方法
    fn1 = getattr(lunar, 'getJieQi', None)
    if callable(fn1):
        try:
            return fn1()
        except Exception:
            pass
    fn2 = getattr(lunar, 'getJieQiTable', None)
    if callable(fn2):
        try:
            tbl = fn2()
            try:
                return list(tbl.keys())
            except Exception:
                return None
        except Exception:
            return None
    return None


def _safe_call(obj: Any, names: Any, default=None):
    for nm in names:
        fn = getattr(obj, nm, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                continue
    return default


def _safe_leap(lunar: Any) -> bool:
    # 兼容多版本：尝试 isLeap / isLeapMonth / 通过中文月份是否以“闰”开头判断
    for nm in ['isLeap', 'isLeapMonth']:
        fn = getattr(lunar, nm, None)
        if callable(fn):
            try:
                val = fn()
                if isinstance(val, bool):
                    return val
            except Exception:
                pass
    try:
        name = _safe_call(lunar, ['getMonthInChinese'])
        if isinstance(name, str) and name.startswith('闰'):
            return True
    except Exception:
        pass
    return False


def solar2bazi(year: int, month: int, day: int, hour: int = 12, minute: int = 0, second: int = 0, *, tz: Optional[str] = None, sect: int = 2) -> Dict[str, Any]:
    # 惰性导入，避免编辑器找不到依赖时报错
    global Solar
    if Solar is None:
        from lunar_python import Solar as _Solar  # type: ignore
        Solar = _Solar
    # 换算到北京时间
    by, bm, bd, bh, bmin, bs = _to_bj_components(year, month, day, hour, minute, second, tz)
    solar = Solar.fromYmdHms(by, bm, bd, bh, bmin, bs)
    lunar = solar.getLunar()
    return _bazi_from_lunar(lunar, sect=sect)


def lunar2bazi(year: int, month: int, day: int, is_leap_month: bool = False, hour: int = 12, minute: int = 0, second: int = 0, *, tz: Optional[str] = None, sect: int = 2) -> Dict[str, Any]:
    """农历输入 + 时区：
    先将农历YMD映射到对应的公历日期（北京时间），再用“给定时区的时刻”换算成北京时间的时分秒，最终以北京时间排盘。
    这样处理能在跨时区场景下更贴近“先换算到北京时刻再排盘”的习惯。
    """
    global Lunar
    if Lunar is None:
        from lunar_python import Lunar as _Lunar  # type: ignore
        Lunar = _Lunar

    # 先拿到该农历日期对应的公历日（以北京时间定义的传统农历为准）
    try:
        lunar_date = None
        # 先尝试带闰月标记版本
        for ctor in (
            lambda: Lunar.fromYmd(year, month, day, is_leap_month),  # type: ignore
            lambda: Lunar.fromYmd(year, month, day),  # type: ignore
        ):
            try:
                lunar_date = ctor()
                if lunar_date is not None:
                    break
            except Exception:
                continue
        if lunar_date is None:
            lunar_date = Lunar.fromYmd(year, month, day)  # type: ignore
        s = lunar_date.getSolar()
        solar_y, solar_m, solar_d = s.getYear(), s.getMonth(), s.getDay()
    except Exception:
        # 兜底：若失败，按输入年月日近似作为公历
        solar_y, solar_m, solar_d = year, month, day

    # 将“输入时刻（在 tz 时区）”换算为北京时间的时刻
    by, bm, bd, bh, bmin, bs = _to_bj_components(solar_y, solar_m, solar_d, hour, minute, second, tz)

    # 最终以北京时间的公历时刻排盘
    return solar2bazi(by, bm, bd, bh, bmin, bs, tz='Asia/Shanghai', sect=sect)


if __name__ == '__main__':
    demo = solar2bazi(1990, 1, 1, 8, 30, 0)
    from json import dumps
    print(dumps(demo, ensure_ascii=False, indent=2))
