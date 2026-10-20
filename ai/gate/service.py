"""Gate service (Blueprint V2 §9 stages 7 and 8; Roadmap Week 8, Rishikesh).

Loads the trained confidence model once, scores a draft from its signal vector, and
assigns a lane with the active threshold set:

    fast       score >= fast threshold (and the draft can answer)
    assisted   score >= assisted threshold
    escalate   otherwise, or the draft cannot answer, or no threshold is certified

A lane whose threshold could not be certified stays closed. The score comes with the
top reasons that pulled it down, so the workbench can explain the lane.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

ARTIFACT_DIR = ROOT / "ai" / "confidence_model" / "artifacts"


@dataclass(frozen=True)
class Thresholds:
    version: str
    fast: float | None
    assisted: float | None


@dataclass(frozen=True)
class Decision:
    score: float | None
    lane: str
    reasons: list[str]
    model_version: str


@lru_cache(maxsize=4)
def load_model(name: str = "confidence-v1-judge"):
    """The joblib artifact written by ai/confidence_model/train.py, or None if absent."""
    import joblib

    path = ARTIFACT_DIR / f"{name}.joblib"
    return joblib.load(path)["model"] if path.exists() else None


@lru_cache(maxsize=1)
def _article_topics() -> dict[str, str]:
    from benchmark.kb import load_articles

    return {a.id: a.topic or "none" for a in load_articles(ROOT / "data" / "kb") if a.id}


def lane_for(score: float | None, can_answer: bool | None, thresholds: Thresholds | None) -> str:
    if score is None or not can_answer or thresholds is None:
        return "escalate"
    if thresholds.fast is not None and score >= thresholds.fast:
        return "fast"
    if thresholds.assisted is not None and score >= thresholds.assisted:
        return "assisted"
    return "escalate"


def decide(features: dict, department: str | None, top_article_key: str | None, can_answer: bool | None,
           thresholds: Thresholds | None, model=None) -> Decision:
    """Score one draft. `features` is its features-v1 signal vector."""
    from confidence_model.dataset import Row

    model = model or load_model()
    if model is None:
        return Decision(None, "escalate", ["no confidence model is deployed"], "none")
    topic = _article_topics().get(top_article_key or "", "none")
    row = Row("live", "live", "live", "?", department or "?", topic, "live", can_answer, features, None)
    score = float(model.predict([row])[0])
    reasons = model.top_reasons([row])[0]
    if not can_answer:
        reasons = ["the draft says the evidence cannot answer", *reasons]
    return Decision(round(score, 4), lane_for(score, can_answer, thresholds), reasons[:3], model.version)
