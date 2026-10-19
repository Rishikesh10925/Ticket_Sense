"""Risk-controlled threshold selection, Learn-then-Test style (Blueprint V2 §4.5, §13.4).

For each candidate threshold t, the null hypothesis is "drafts scoring >= t are
unacceptable more than `alpha` of the time". Its exact one-sided binomial p-value is
P(Binomial(n_t, alpha) <= k_t), where n_t drafts are shown and k_t are unacceptable.
Thresholds are tested in a fixed sequence from strict to lenient, stopping at the first
one that cannot be rejected at level `delta` (fixed-sequence testing controls the
family-wise error without a multiplicity correction) [Angelopoulos et al. 2021].

The very strictest thresholds show only a handful of drafts, and below
n_min = ceil(log(delta) / log(1 - alpha)) shown drafts the null can never be rejected,
even with zero errors. Those candidates are skipped rather than tested; otherwise the
sequence would always stop at its first step. The skip depends on the scores only,
never on the labels, so it does not weaken the guarantee.

Guarantee, when new tickets are exchangeable with the calibration tickets: with
probability at least 1 - delta, the true unacceptable rate above the returned
threshold is at most alpha. Under topic shift it can fail; H3 measures that.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike
from scipy.stats import binom


@dataclass(frozen=True)
class ThresholdResult:
    threshold: float | None  # None: no threshold could be certified, the lane stays closed
    alpha: float
    delta: float
    n_shown: int
    n_unacceptable: int
    coverage: float
    p_value: float | None

    @property
    def empirical_risk(self) -> float | None:
        return self.n_unacceptable / self.n_shown if self.n_shown else None


def binomial_p_value(n_shown: int, n_unacceptable: int, alpha: float) -> float:
    """p-value for H0: risk > alpha, given k unacceptable out of n shown."""
    if n_shown == 0:
        return 1.0
    return float(binom.cdf(n_unacceptable, n_shown, alpha))


def min_testable_size(alpha: float, delta: float) -> int:
    """Fewest shown drafts for which zero errors would reject H0: (1-alpha)^n <= delta."""
    return math.ceil(math.log(delta) / math.log(1 - alpha))


def learn_then_test(
    confidence: ArrayLike,
    acceptable: ArrayLike,
    alpha: float = 0.10,
    delta: float = 0.10,
    min_shown: int | None = None,
) -> ThresholdResult:
    """Most lenient threshold whose risk is certified <= alpha with prob >= 1 - delta."""
    conf = np.asarray(confidence, dtype=float)
    acc = np.asarray(acceptable, dtype=float)
    if conf.shape != acc.shape or conf.ndim != 1 or conf.size == 0:
        raise ValueError("confidence and acceptable must be equal-length 1-D arrays")
    if not (0 < alpha < 1 and 0 < delta < 1):
        raise ValueError("alpha and delta must be in (0, 1)")

    if min_shown is None:
        min_shown = min_testable_size(alpha, delta)

    best = ThresholdResult(None, alpha, delta, 0, 0, 0.0, None)
    for t in np.unique(conf)[::-1]:  # strict -> lenient
        shown = conf >= t
        n = int(shown.sum())
        if n < min_shown:
            continue  # untestable by construction; decided from scores alone
        k = int((acc[shown] == 0).sum())
        p = binomial_p_value(n, k, alpha)
        if p > delta:
            break  # fixed sequence: the first failure ends the search
        best = ThresholdResult(float(t), alpha, delta, n, k, n / conf.size, p)
    return best


@dataclass(frozen=True)
class LaneThresholds:
    fast: ThresholdResult
    assisted: ThresholdResult

    def lane(self, score: float, can_answer: bool = True) -> str:
        """Blueprint §9.1: fast >= high threshold; assisted between; else escalate.
        A draft whose model said it cannot answer always escalates."""
        if not can_answer:
            return "escalate"
        if self.fast.threshold is not None and score >= self.fast.threshold:
            return "fast"
        if self.assisted.threshold is not None and score >= self.assisted.threshold:
            return "assisted"
        return "escalate"


def select_lane_thresholds(
    confidence: ArrayLike,
    acceptable: ArrayLike,
    alpha_fast: float = 0.10,
    alpha_assisted: float = 0.40,
    delta: float = 0.10,
) -> LaneThresholds:
    return LaneThresholds(
        fast=learn_then_test(confidence, acceptable, alpha_fast, delta),
        assisted=learn_then_test(confidence, acceptable, alpha_assisted, delta),
    )
