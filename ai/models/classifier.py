"""Packaged inference interface for the trained classifiers.

Loads the three joblib artifacts produced by train_classifier.py once (module-level,
so the backend doesn't reload them per request) and exposes a single classify_ticket()
call. This is the integration point backend/app/services/classification.py imports.

Artifacts must exist first: run train_classifier.py, which requires the `ai` extra
(`uv sync --extra ai` from backend/) — this module itself only needs the already-fitted
pipelines (scikit-learn + joblib), not pandas/sentence-transformers.
"""

from dataclasses import dataclass
from pathlib import Path

import joblib

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


@dataclass
class ClassificationResult:
    department: str
    priority: str
    sentiment: str


def _load(name: str):
    path = ARTIFACTS_DIR / f"{name}_classifier.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `python ai/models/train_classifier.py` first."
        )
    return joblib.load(path)


_department_model = None
_priority_model = None
_sentiment_model = None


def _models():
    global _department_model, _priority_model, _sentiment_model
    if _department_model is None:
        _department_model = _load("department")
        _priority_model = _load("priority")
        _sentiment_model = _load("sentiment")
    return _department_model, _priority_model, _sentiment_model


def classify_ticket(subject: str, description: str) -> ClassificationResult:
    text = [f"{subject} {description}".strip()]
    department_model, priority_model, sentiment_model = _models()
    return ClassificationResult(
        department=department_model.predict(text)[0],
        priority=priority_model.predict(text)[0],
        sentiment=sentiment_model.predict(text)[0],
    )
