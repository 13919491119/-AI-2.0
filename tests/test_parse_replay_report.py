import os
import optimize_models


def test_parse_replay_report_sample(tmp_path, monkeypatch):
    # create a small fake report matching expected format
    content = '''双色球历史批量复盘与模型学习升级报告

模型：liuyao
总期数：2
红球命中总数：3
蓝球命中总数：1
全中（红+蓝）期数：0

模型：liuren
总期数：2
红球命中总数：4
蓝球命中总数：0
全中（红+蓝）期数：1
'''
    p = tmp_path / "sample_report.txt"
    p.write_text(content, encoding='utf-8')
    stats = optimize_models.parse_replay_report(str(p))
    assert 'liuyao' in stats and 'liuren' in stats
    assert stats['liuyao']['total'] == 2
    assert stats['liuyao']['red_hit'] == 3
    assert stats['liuren']['full_hit'] == 1
