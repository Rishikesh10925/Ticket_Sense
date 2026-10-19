import numpy as np
import pytest

from evaluation import (
    aurc,
    auroc_unacceptable,
    bootstrap_ci,
    brier_score,
    excess_aurc,
    expected_calibration_error,
    learn_then_test,
    optimal_aurc,
    paired_bootstrap_diff,
    reliability_bins,
    risk_at_coverage,
    risk_coverage_curve,
    select_lane_thresholds,
)

# Hand-worked toy case: sorted by confidence the labels are good, bad, good, bad.
CONF = [0.9, 0.8, 0.7, 0.6]
ACC = [1, 0, 1, 0]


def test_risk_coverage_curve_by_hand():
    rc = risk_coverage_curve(CONF, ACC)
    np.testing.assert_allclose(rc.coverage, [0.25, 0.5, 0.75, 1.0])
    np.testing.assert_allclose(rc.risk, [0.0, 0.5, 1 / 3, 0.5])
    np.testing.assert_allclose(rc.thresholds, [0.9, 0.8, 0.7, 0.6])


def test_aurc_by_hand_and_oracle():
    assert aurc(CONF, ACC) == pytest.approx((0 + 0.5 + 1 / 3 + 0.5) / 4)
    assert optimal_aurc(ACC) == pytest.approx((0 + 0 + 1 / 3 + 0.5) / 4)
    assert excess_aurc(CONF, ACC) == pytest.approx(0.5 / 4)


def test_perfect_signal_reaches_oracle_and_reversed_is_worse():
    rng = np.random.default_rng(1)
    acc = rng.integers(0, 2, 200)
    perfect = acc + rng.uniform(0, 0.5, 200)
    assert aurc(perfect, acc) == pytest.approx(optimal_aurc(acc))
    assert aurc(-perfect, acc) > aurc(rng.uniform(size=200), acc) > aurc(perfect, acc)


def test_ties_enter_together_so_order_does_not_matter():
    assert aurc([0.5, 0.5], [1, 0]) == pytest.approx(0.5)
    assert aurc([0.5, 0.5], [0, 1]) == pytest.approx(0.5)


def test_constant_signal_aurc_is_base_error_rate():
    acc = np.array([1, 1, 1, 0, 0])
    assert aurc(np.zeros(5), acc) == pytest.approx(0.4)


def test_risk_at_coverage():
    assert risk_at_coverage(CONF, ACC, 0.5) == pytest.approx(0.5)
    assert risk_at_coverage(CONF, ACC, 0.25) == pytest.approx(0.0)
    assert risk_at_coverage(CONF, ACC, 0.6) == pytest.approx(1 / 3)
    with pytest.raises(ValueError):
        risk_at_coverage(CONF, ACC, 0.0)


def test_auroc_by_hand_and_against_sklearn():
    assert auroc_unacceptable(CONF, ACC) == pytest.approx(0.75)
    sklearn_metrics = pytest.importorskip("sklearn.metrics")
    rng = np.random.default_rng(2)
    acc = rng.integers(0, 2, 300)
    conf = np.round(acc * 0.3 + rng.uniform(size=300), 1)  # rounding forces ties
    assert auroc_unacceptable(conf, acc) == pytest.approx(sklearn_metrics.roc_auc_score(acc, conf))
    assert np.isnan(auroc_unacceptable([0.1, 0.2], [1, 1]))


def test_calibration_metrics():
    probs = np.full(10, 0.9)
    assert expected_calibration_error(probs, [1] * 9 + [0]) == pytest.approx(0.0)
    assert expected_calibration_error(probs, [1] * 5 + [0] * 5) == pytest.approx(0.4)
    assert brier_score([1.0, 0.0], [1, 0]) == 0.0
    assert brier_score([0.5, 0.5], [1, 0]) == pytest.approx(0.25)
    rel = reliability_bins([0.05, 0.95, 0.96], [0, 1, 0], n_bins=10)
    assert rel.counts.tolist() == [1, 0, 0, 0, 0, 0, 0, 0, 0, 2]
    assert rel.accuracy[-1] == pytest.approx(0.5)
    with pytest.raises(ValueError):
        expected_calibration_error([1.2], [1])


def test_input_validation():
    with pytest.raises(ValueError):
        aurc([0.1, 0.2], [1])
    with pytest.raises(ValueError):
        aurc([0.1], [2])
    with pytest.raises(ValueError):
        aurc([], [])


def test_bootstrap_interval_covers_estimate_and_is_reproducible():
    rng = np.random.default_rng(3)
    x = rng.normal(5.0, 1.0, 400)
    a = bootstrap_ci(np.mean, x, n_resamples=500, seed=7)
    b = bootstrap_ci(np.mean, x, n_resamples=500, seed=7)
    assert a == b
    assert a.low < a.estimate < a.high
    assert a.low < 5.0 < a.high
    assert a.high - a.low == pytest.approx(2 * 1.96 / np.sqrt(400), rel=0.25)


def test_group_bootstrap_is_wider_when_items_are_clustered():
    rng = np.random.default_rng(4)
    cluster_means = rng.normal(0, 1, 40)
    x = np.repeat(cluster_means, 10)  # 10 identical paraphrases per scenario
    groups = np.repeat(np.arange(40), 10)
    naive = bootstrap_ci(np.mean, x, n_resamples=400, seed=0)
    grouped = bootstrap_ci(np.mean, x, groups=groups, n_resamples=400, seed=0)
    assert (grouped.high - grouped.low) > 2 * (naive.high - naive.low)


def test_paired_difference_detects_a_better_signal():
    rng = np.random.default_rng(5)
    acc = rng.integers(0, 2, 500)
    good = acc + rng.normal(0, 0.5, 500)
    noise = rng.normal(0, 1, 500)
    diff = paired_bootstrap_diff(aurc, good, noise, acc, n_resamples=300)
    assert diff.estimate < 0 and diff.excludes_zero()
    same = paired_bootstrap_diff(aurc, good, good, acc, n_resamples=50)
    assert same.low == same.high == 0.0


def _calibrated_scores(rng, n):
    score = rng.uniform(size=n)
    return score, (rng.uniform(size=n) < score).astype(int)


def test_learn_then_test_certifies_budget_on_calibration_data():
    rng = np.random.default_rng(6)
    score, acc = _calibrated_scores(rng, 2000)
    result = learn_then_test(score, acc, alpha=0.10, delta=0.10)
    assert result.threshold is not None
    assert result.empirical_risk <= 0.10
    assert result.p_value <= 0.10
    assert 0 < result.coverage < 0.5


def test_learn_then_test_closes_lane_when_nothing_is_good_enough():
    result = learn_then_test(np.linspace(0, 1, 50), np.zeros(50), alpha=0.10, delta=0.10)
    assert result.threshold is None and result.coverage == 0.0


def test_learn_then_test_guarantee_holds_on_fresh_exchangeable_data():
    """H2's check in miniature: across resplits, the fast-lane risk on unseen data
    should exceed alpha in at most about delta of the splits."""
    rng = np.random.default_rng(7)
    violations, trials = 0, 60
    for _ in range(trials):
        cal_s, cal_a = _calibrated_scores(rng, 400)
        test_s, test_a = _calibrated_scores(rng, 4000)
        t = learn_then_test(cal_s, cal_a, alpha=0.15, delta=0.10).threshold
        if t is None:
            continue
        shown = test_s >= t
        violations += (1 - test_a[shown]).mean() > 0.15
    assert violations / trials <= 0.10 + 0.08  # delta plus Monte Carlo slack


def test_lane_assignment():
    rng = np.random.default_rng(8)
    score, acc = _calibrated_scores(rng, 3000)
    lanes = select_lane_thresholds(score, acc, alpha_fast=0.10, alpha_assisted=0.40)
    assert lanes.fast.threshold > lanes.assisted.threshold
    assert lanes.lane(0.999) == "fast"
    assert lanes.lane((lanes.fast.threshold + lanes.assisted.threshold) / 2) == "assisted"
    assert lanes.lane(0.0) == "escalate"
    assert lanes.lane(0.999, can_answer=False) == "escalate"


def test_min_testable_size():
    from evaluation.risk_control import binomial_p_value, min_testable_size

    n = min_testable_size(0.10, 0.10)
    assert n == 22
    assert binomial_p_value(n, 0, 0.10) <= 0.10 < binomial_p_value(n - 1, 0, 0.10)
