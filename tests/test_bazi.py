import json
from tools.bazi_lib import BaziCalculator


def test_calculate_structure():
    calc = BaziCalculator()
    res = calc.calculate(1976, 11, 13, 11)
    # 基本键存在
    assert '年柱' in res
    assert '时柱' in res
    assert 'precision' in res

    # precision 要么是 'sxtwl'（若已安装），要么 'fallback'
    assert res['precision'] in ('sxtwl', 'fallback')
