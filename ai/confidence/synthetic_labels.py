"""Synthetic outcome simulation — bootstraps confidence-model training labels since no
real human review data exists yet (Week 9+ starts collecting real Accept/Edit/Reject
outcomes; see docs/confidence-labelling-guide.md). This is honestly a proxy, not real
human judgment: a documented formula over the same five features the model trains on,
with injected randomness so a label isn't a deterministic function of its own inputs.
See docs/confidence-model.md's "What the synthetic labels are (and aren't)" section
before reading too much into the trained model's accuracy against real outcomes.
"""

import math
import random
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from features import ConfidenceFeatures  # noqa: E402

# Weights are a documented judgment call, not fitted to any data — deciding which
# signals a synthetic bootstrap should weight most heavily. Retrieval quality dominates
# (a draft is only as good as the evidence it cites), category risk is the next
# strongest (an unreliable department classification undermines everything downstream),
# freshness/OCR contribute less. Retraining on real Accept/Edit/Reject outcomes
# (Week 9+) will learn the model's own weights from data instead of this guess.
_WEIGHTS = {
    "retrieval_relevance": 2.5,
    "ticket_resolution_similarity": 1.5,
    "document_freshness": 0.5,
    "ocr_confidence": 0.5,
    "category_risk": -2.5,
}
_BIAS = -0.8  # centers the sigmoid so a "typical" ticket lands near a coin flip, not a guaranteed success


def success_probability(features: ConfidenceFeatures) -> float:
    """The synthetic formula's own belief in "success" before the random draw that
    turns it into a label — also useful on its own as a sanity-check number."""
    z = (
        _BIAS
        + _WEIGHTS["retrieval_relevance"] * features.retrieval_relevance
        + _WEIGHTS["ticket_resolution_similarity"] * features.ticket_resolution_similarity
        + _WEIGHTS["document_freshness"] * features.document_freshness
        + _WEIGHTS["ocr_confidence"] * features.ocr_confidence
        + _WEIGHTS["category_risk"] * features.category_risk
    )
    return 1 / (1 + math.exp(-z))


def simulate_outcome(features: ConfidenceFeatures, rng: random.Random) -> bool:
    """True = synthetic "success" (the draft would have been accepted or lightly
    edited), False = synthetic "failure" (rejected or heavily edited) — standing in
    for the label mapping in docs/confidence-labelling-guide.md until real reviewer
    outcomes exist."""
    return rng.random() < success_probability(features)
