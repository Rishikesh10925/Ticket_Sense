

def test_a_coarse_grid_avoids_tiny_first_tests():
    import numpy as np

    from evaluation.risk_control import DEFAULT_GRID, learn_then_test

    # 200 drafts, 85% acceptable, but the single most confident one is unacceptable.
    rng = np.random.default_rng(0)
    conf = np.sort(rng.uniform(0.3, 0.98, 200))[::-1]
    acc = (rng.uniform(size=200) < 0.85).astype(float)
    acc[:1] = 0
    every_score = learn_then_test(conf, acc, alpha=0.40, delta=0.10)
    grid = learn_then_test(conf, acc, alpha=0.40, delta=0.10, candidates=DEFAULT_GRID)
    assert grid.threshold is not None and grid.coverage > 0.9
    assert every_score.coverage <= grid.coverage
