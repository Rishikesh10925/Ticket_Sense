import pytest

from evaluation.agreement import cohen_kappa, fleiss_kappa, pair_report


def test_perfect_agreement_is_one_and_chance_is_about_zero():
    a = ["A", "M", "R", "W"] * 5
    assert cohen_kappa(a, a) == 1.0
    assert abs(cohen_kappa(["A", "M"] * 10, ["A"] * 10 + ["M"] * 10)) < 0.01


def test_known_value():
    # 2x2 example: po = 0.7, pe = 0.7*0.6 + 0.3*0.4 = 0.54 -> kappa 0.16 / 0.46
    a = ["1"] * 25 + ["1"] * 10 + ["0"] * 5 + ["0"] * 10
    b = ["1"] * 25 + ["0"] * 10 + ["1"] * 5 + ["0"] * 10
    assert cohen_kappa(a, b, categories=("0", "1")) == pytest.approx(0.3478, abs=1e-4)


def test_linear_weights_reward_near_misses():
    a = ["A", "A", "R", "W"] * 5
    near = ["M", "A", "W", "W"] * 5  # off by one step
    far = ["W", "A", "A", "W"] * 5  # off by three steps
    assert cohen_kappa(a, near, weights="linear") > cohen_kappa(a, far, weights="linear")


def test_fleiss_three_raters():
    assert fleiss_kappa([["A", "A", "A"], ["W", "W", "W"], ["M", "M", "M"]]) == 1.0
    assert fleiss_kappa([["A", "A"], ["W", "M"]]) is not None and fleiss_kappa([["A"]]) is None


def test_small_samples_are_not_reported_as_numbers():
    assert "insufficient" in pair_report(["A"] * 5, ["A"] * 5)["status"]
    full = pair_report(["A", "M", "R", "W"] * 3, ["A", "M", "R", "W"] * 3)
    assert full["kappa"] == 1.0 and full["acceptable_agreement"] == 1.0
