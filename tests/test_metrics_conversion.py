import optimize_models


def test_metrics_to_weights_basic():
    metrics = {
        'liuyao': {'total': 100, 'red_hit': 120, 'blue_hit': 10, 'full_hit': 0},
        'liuren': {'total': 100, 'red_hit': 150, 'blue_hit': 12, 'full_hit': 1},
        'qimen': {'total': 100, 'red_hit': 160, 'blue_hit': 8, 'full_hit': 2},
    }
    weights = optimize_models.metrics_to_weights(metrics, min_weight=0.01)
    assert isinstance(weights, dict)
    # 所有模型权重和为 1（或接近，四舍五入后为1）
    s = sum(weights.values())
    assert abs(s - 1.0) < 1e-6
    for v in weights.values():
        assert v >= 0.01
