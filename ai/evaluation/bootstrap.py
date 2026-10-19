"""Group-aware bootstrap intervals (Blueprint V2 §15.2).

Tickets generated from the same scenario share a `group_id`; they are not independent,
so resampling is done over groups, not tickets. With no groups every ticket is its own
group, which reduces to the ordinary bootstrap.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

Metric = Callable[..., float]


@dataclass(frozen=True)
class Interval:
    estimate: float
    low: float
    high: float
    n_resamples: int

    def excludes_zero(self) -> bool:
        return self.low > 0 or self.high < 0

    def __str__(self) -> str:
        return f"{self.estimate:.4f} [{self.low:.4f}, {self.high:.4f}]"


def _group_index(groups: ArrayLike | None, n: int) -> list[NDArray[np.intp]]:
    if groups is None:
        return [np.array([i]) for i in range(n)]
    g = np.asarray(groups)
    if g.shape != (n,):
        raise ValueError("groups must have one entry per item")
    _, inverse = np.unique(g, return_inverse=True)
    return [np.flatnonzero(inverse == k) for k in range(inverse.max() + 1)]


def _resample_indices(members: list[NDArray[np.intp]], rng: np.random.Generator) -> NDArray[np.intp]:
    picks = rng.integers(0, len(members), size=len(members))
    return np.concatenate([members[p] for p in picks])


def _metric_on(metric: Metric, arrays: Sequence[NDArray], idx: NDArray[np.intp]) -> float:
    try:
        return float(metric(*(a[idx] for a in arrays)))
    except ValueError:
        return float("nan")  # e.g. a resample with one class only


def bootstrap_ci(
    metric: Metric,
    *arrays: ArrayLike,
    groups: ArrayLike | None = None,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> Interval:
    """Percentile interval for `metric(*arrays)`. Resamples that make the metric
    undefined are dropped (and should be rare; check `n_resamples` on the result)."""
    data = [np.asarray(a) for a in arrays]
    n = data[0].shape[0]
    if any(a.shape[0] != n for a in data):
        raise ValueError("all arrays must have the same length")
    members = _group_index(groups, n)
    rng = np.random.default_rng(seed)

    values = np.array([_metric_on(metric, data, _resample_indices(members, rng)) for _ in range(n_resamples)])
    values = values[np.isfinite(values)]
    estimate = float(metric(*data))
    low, high = np.quantile(values, [alpha / 2, 1 - alpha / 2])
    return Interval(estimate, float(low), float(high), int(values.size))


def paired_bootstrap_diff(
    metric: Callable[[NDArray, NDArray], float],
    score_a: ArrayLike,
    score_b: ArrayLike,
    labels: ArrayLike,
    groups: ArrayLike | None = None,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> Interval:
    """Interval for metric(a) - metric(b) on the *same* resampled tickets each round,
    which is what H1's decision rule needs (AURC difference excludes zero)."""

    def diff(a: NDArray, b: NDArray, y: NDArray) -> float:
        return metric(a, y) - metric(b, y)

    return bootstrap_ci(diff, score_a, score_b, labels, groups=groups, n_resamples=n_resamples, alpha=alpha, seed=seed)
