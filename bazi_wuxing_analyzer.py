# 八字五行精准分析模块

TIANGAN_WUXING = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
DIZHI_WUXING = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
CANGGAN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '庚', '戊'], '午': ['丁', '己'], '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'], '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲']
}

def count_wuxing(tiangans, dizhis, include_canggan=True):
    """
    统计八字天干地支及藏干五行分布。
    :param tiangans: list, 四柱天干
    :param dizhis: list, 四柱地支
    :param include_canggan: bool, 是否统计地支藏干
    :return: dict, 五行分布
    """
    wuxing_count = {'金': 0, '木': 0, '水': 0, '火': 0, '土': 0}
    for tg in tiangans:
        wuxing_count[TIANGAN_WUXING.get(tg, '')] += 1
    for dz in dizhis:
        wuxing_count[DIZHI_WUXING.get(dz, '')] += 1
        if include_canggan:
            for cg in CANGGAN.get(dz, []):
                wuxing_count[TIANGAN_WUXING.get(cg, '')] += 1
    return wuxing_count

if __name__ == "__main__":
    # 示例：丙辰 丙子 己亥 己巳
    tiangans = ['丙', '丙', '己', '己']
    dizhis = ['辰', '子', '亥', '巳']
    result = count_wuxing(tiangans, dizhis)
    print("五行分布：", result)
