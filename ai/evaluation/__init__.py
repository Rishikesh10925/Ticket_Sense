"""TicketSense evaluation package: the shared metrics spine every experiment uses.

`python tasks.py reproduce` (or `make reproduce`) regenerates every table and figure
through this package; see ai/evaluation/reproduce.py.
"""

from evaluation.bootstrap import Interval, bootstrap_ci, paired_bootstrap_diff
from evaluation.metrics import (
    RiskCoverage,
    aurc,
    auroc_unacceptable,
    brier_score,
    excess_aurc,
    expected_calibration_error,
    optimal_aurc,
    reliability_bins,
    risk_at_coverage,
    risk_coverage_curve,
)
from evaluation.risk_control import LaneThresholds, ThresholdResult, learn_then_test, select_lane_thresholds

__all__ = [
    "Interval",
    "LaneThresholds",
    "RiskCoverage",
    "ThresholdResult",
    "aurc",
    "auroc_unacceptable",
    "bootstrap_ci",
    "brier_score",
    "excess_aurc",
    "expected_calibration_error",
    "learn_then_test",
    "optimal_aurc",
    "paired_bootstrap_diff",
    "reliability_bins",
    "risk_at_coverage",
    "risk_coverage_curve",
    "select_lane_thresholds",
]
