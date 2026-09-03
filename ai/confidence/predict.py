"""Loads the trained confidence model once per process and scores a feature vector.

This is the function ai/graph/nodes.py's score node calls (Week 8, Rishikesh). See
train.py for how the model was trained and docs/confidence-model.md for the honest
read of what the score does and doesn't mean.
"""

import sys
from pathlib import Path

import joblib

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from features import ConfidenceFeatures  # noqa: E402

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

_model = None


def _get_model():
    global _model
    if _model is None:
        path = ARTIFACTS_DIR / "confidence_model.joblib"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found — run `python ai/confidence/train.py` first.")
        _model = joblib.load(path)
    return _model


def predict_confidence(features: ConfidenceFeatures) -> float:
    """Probability (0-1) that a human reviewer would accept this draft as-is or with
    only a light edit, per the trained model."""
    model = _get_model()
    return float(model.predict_proba([features.to_vector()])[0][1])
