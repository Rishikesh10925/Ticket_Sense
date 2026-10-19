"""Cheap baselines B0 and B4 to B7 (Blueprint V2 §14; Roadmap Week 6, Shivaganesh).

Every baseline turns a draft into one confidence number (higher = more likely
acceptable), so they all go through the same risk-coverage evaluation as the proposed
model:

    B0   always show (constant 1) / always escalate (constant 0): bound the curves
    B4   top-1 retrieval similarity: cosine similarity of the best final passage
    B5   cross-encoder reranker score of the best final passage
    B6   entailment score: share of the draft's claims supported by their citations
    B7   logistic regression on B4, B5 and B6 only, fitted on calibration labels

B1 to B3 (verbalised confidence, token probability, self-consistency) need extra model
calls and are computed in Week 7.

A draft the pipeline would not show (schema-invalid or "cannot answer") still gets a
score. Drafts with no claims get B6 = 0, the same as a draft whose claims are all
unsupported: nothing in it is verified.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from evaluation.bootstrap import bootstrap_ci
from evaluation.metrics import aurc, auroc_unacceptable, excess_aurc

BASELINE_VERSION = "baselines-v1"
CHEAP = ("B4", "B5", "B6")


@dataclass(frozen=True)
class DraftSignals:
    draft_id: str
    ticket_id: str
    group_id: str
    top1_similarity: float | None  # B4
    top1_rerank: float | None  # B5
    groundedness: float | None  # B6

    def features(self) -> list[float]:
        return [
            self.top1_similarity if self.top1_similarity is not None else 0.0,
            # Raw cross-encoder logits; squashed so B7's scaling is not dominated by outliers.
            1 / (1 + math.exp(-self.top1_rerank)) if self.top1_rerank is not None else 0.0,
            self.groundedness if self.groundedness is not None else 0.0,
        ]


def baseline_scores(signals: Sequence[DraftSignals]) -> dict[str, NDArray[np.float64]]:
    x = np.array([s.features() for s in signals], dtype=float).reshape(len(signals), 3)
    n = len(signals)
    return {
        "B0-show": np.ones(n),
        "B0-escalate": np.zeros(n),
        "B4": x[:, 0],
        "B5": x[:, 1],
        "B6": x[:, 2],
    }


class B7:
    """Logistic regression on the three cheap signals, with standardisation. Fitted on
    the calibration split only; never on the locked test set."""

    def __init__(self, c: float = 1.0):
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        self.model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=1000))

    def fit(self, signals: Sequence[DraftSignals], acceptable: Sequence[bool]) -> "B7":
        y = np.asarray(acceptable, dtype=int)
        if len(set(y)) < 2:
            raise ValueError("B7 needs both acceptable and unacceptable calibration drafts")
        self.model.fit(np.array([s.features() for s in signals]), y)
        return self

    def predict(self, signals: Sequence[DraftSignals]) -> NDArray[np.float64]:
        return self.model.predict_proba(np.array([s.features() for s in signals]))[:, 1]

    @property
    def coefficients(self) -> dict[str, float]:
        lr = self.model[-1]
        return dict(zip(CHEAP, (round(float(c), 4) for c in lr.coef_[0])))


def compare(
    scores: dict[str, NDArray[np.float64]],
    acceptable: Sequence[bool],
    groups: Sequence[str],
    n_boot: int = 2000,
    seed: int = 2026,
) -> dict[str, dict]:
    """AURC, excess AURC and AUROC (detecting unacceptable drafts) for each baseline,
    with group-aware bootstrap intervals (resampling scenario groups, not tickets)."""
    y = np.asarray(acceptable, dtype=float)
    out = {}
    for name, conf in scores.items():
        ci = bootstrap_ci(aurc, conf, y, groups=groups, n_resamples=n_boot, seed=seed)
        out[name] = {
            "aurc": round(aurc(conf, y), 4),
            "aurc_ci": [round(ci.low, 4), round(ci.high, 4)],
            "e_aurc": round(excess_aurc(conf, y), 4),
            "auroc_unacceptable": round(auroc_unacceptable(conf, y), 4) if 0 < y.sum() < len(y) else None,
        }
    return out
