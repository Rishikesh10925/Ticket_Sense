"""Selective-prediction and calibration metrics (Blueprint V2 §4.3, §4.4, §15.1).

Conventions used everywhere in this package:

- `confidence`: higher means "more likely acceptable". Any signal (the confidence
  model, top-1 similarity, verbalised confidence, ...) is evaluated the same way.
- `acceptable`: 1 if the draft is acceptable (rubric labels A or M), 0 otherwise.
- risk = share of *shown* drafts that are not acceptable; coverage = share shown.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _as_arrays(confidence: ArrayLike, acceptable: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    conf = np.asarray(confidence, dtype=float)
    acc = np.asarray(acceptable, dtype=float)
    if conf.shape != acc.shape or conf.ndim != 1:
        raise ValueError("confidence and acceptable must be 1-D arrays of equal length")
    if conf.size == 0:
        raise ValueError("empty input")
    if not np.isin(acc, (0.0, 1.0)).all():
        raise ValueError("acceptable must contain only 0 and 1")
    return conf, acc


@dataclass(frozen=True)
class RiskCoverage:
    thresholds: NDArray[np.float64]  # descending: strict -> lenient
    coverage: NDArray[np.float64]
    risk: NDArray[np.float64]


def risk_coverage_curve(confidence: ArrayLike, acceptable: ArrayLike) -> RiskCoverage:
    """Risk and coverage at every distinct threshold, strict to lenient. Tied scores
    enter together, so the curve does not depend on an arbitrary tie order."""
    conf, acc = _as_arrays(confidence, acceptable)
    order = np.argsort(-conf, kind="stable")
    conf_sorted, bad_sorted = conf[order], 1.0 - acc[order]

    # Last index of each run of equal scores = the point where that threshold's set ends.
    boundaries = np.flatnonzero(np.r_[conf_sorted[1:] != conf_sorted[:-1], True])
    n_shown = boundaries + 1.0
    n_bad = np.cumsum(bad_sorted)[boundaries]
    return RiskCoverage(
        thresholds=conf_sorted[boundaries],
        coverage=n_shown / conf.size,
        risk=n_bad / n_shown,
    )


def aurc(confidence: ArrayLike, acceptable: ArrayLike) -> float:
    """Area under the risk-coverage curve (lower is better). Each threshold's risk is
    weighted by the coverage it adds; without ties this equals the mean of the
    selective risk over k = 1..n shown drafts [Geifman & El-Yaniv 2017]."""
    rc = risk_coverage_curve(confidence, acceptable)
    widths = np.diff(np.r_[0.0, rc.coverage])
    return float(np.sum(rc.risk * widths))


def optimal_aurc(acceptable: ArrayLike) -> float:
    """AURC of a perfect ranking (all acceptable drafts first) for this label set."""
    acc = np.asarray(acceptable, dtype=float)
    # A perfect oracle gives each draft a distinct score, acceptable ones on top.
    oracle = acc + np.linspace(0.5, 0.0, acc.size, endpoint=False)
    return aurc(oracle, acc)


def excess_aurc(confidence: ArrayLike, acceptable: ArrayLike) -> float:
    """AURC minus the oracle AURC: removes the part caused by the base error rate, so
    numbers are comparable across subsets with different error rates."""
    return aurc(confidence, acceptable) - optimal_aurc(acceptable)


def risk_at_coverage(confidence: ArrayLike, acceptable: ArrayLike, coverage: float) -> float:
    """Selective risk when the top `coverage` share of drafts is shown (§15.1 reports
    50, 70 and 90 percent). Uses the smallest threshold set reaching that coverage."""
    if not 0.0 < coverage <= 1.0:
        raise ValueError("coverage must be in (0, 1]")
    rc = risk_coverage_curve(confidence, acceptable)
    idx = int(np.searchsorted(rc.coverage, coverage - 1e-12))
    return float(rc.risk[min(idx, rc.risk.size - 1)])


def auroc_unacceptable(confidence: ArrayLike, acceptable: ArrayLike) -> float:
    """Probability that a random unacceptable draft gets a lower confidence than a random
    acceptable one (ties count half). 0.5 is chance; undefined if one class is absent."""
    conf, acc = _as_arrays(confidence, acceptable)
    pos, neg = conf[acc == 1], conf[acc == 0]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    # Mann-Whitney U via average ranks.
    ranks = _average_ranks(np.r_[pos, neg])
    u = ranks[: pos.size].sum() - pos.size * (pos.size + 1) / 2
    return float(u / (pos.size * neg.size))


def _average_ranks(values: NDArray[np.float64]) -> NDArray[np.float64]:
    order = np.argsort(values, kind="stable")
    sorted_vals = values[order]
    ranks = np.empty(values.size)
    start = 0
    for end in np.r_[np.flatnonzero(sorted_vals[1:] != sorted_vals[:-1]) + 1, values.size]:
        ranks[order[start:end]] = (start + end + 1) / 2.0  # mean of 1-based ranks start+1..end
        start = end
    return ranks


def brier_score(probability: ArrayLike, acceptable: ArrayLike) -> float:
    prob, acc = _as_arrays(probability, acceptable)
    return float(np.mean((prob - acc) ** 2))


@dataclass(frozen=True)
class Reliability:
    bin_edges: NDArray[np.float64]
    mean_confidence: NDArray[np.float64]  # NaN for empty bins
    accuracy: NDArray[np.float64]  # NaN for empty bins
    counts: NDArray[np.int64]


def reliability_bins(probability: ArrayLike, acceptable: ArrayLike, n_bins: int = 10) -> Reliability:
    """Equal-width bins over [0, 1] for the reliability diagram."""
    prob, acc = _as_arrays(probability, acceptable)
    if prob.min() < 0 or prob.max() > 1:
        raise ValueError("calibration metrics need probabilities in [0, 1]")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(prob, edges[1:-1], right=True), 0, n_bins - 1)
    counts = np.bincount(idx, minlength=n_bins)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_conf = np.bincount(idx, weights=prob, minlength=n_bins) / counts
        accuracy = np.bincount(idx, weights=acc, minlength=n_bins) / counts
    return Reliability(edges, mean_conf, accuracy, counts.astype(np.int64))


def expected_calibration_error(probability: ArrayLike, acceptable: ArrayLike, n_bins: int = 10) -> float:
    """Count-weighted mean |accuracy - confidence| over bins [Guo et al. 2017]."""
    rel = reliability_bins(probability, acceptable, n_bins)
    mask = rel.counts > 0
    weights = rel.counts[mask] / rel.counts.sum()
    return float(np.sum(weights * np.abs(rel.accuracy[mask] - rel.mean_confidence[mask])))
