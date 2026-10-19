"""Department and priority classifier v2 with uncertainty output (Blueprint V2 §9 stage
2, §13.2 routing signals; Roadmap Week 4).

Features are a sentence embedding (all-MiniLM-L6-v2, the same model retrieval uses),
optionally concatenated with TF-IDF n-grams. The classifier is multinomial logistic
regression. Every prediction carries its uncertainty: the maximum class probability
and the normalised entropy of the distribution. Both become confidence-model features
("a misrouted ticket gets irrelevant evidence").

Training: ai/models/train_classifier_v2.py (train split; model selection on val only).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ARTIFACT = Path(__file__).resolve().parent / "artifacts" / "v2" / "classifier_v2.joblib"
SEED = 2026


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer

    from devices import device

    return SentenceTransformer(EMBED_MODEL, device=device("embed"))


def embed(texts: list[str]) -> np.ndarray:
    return np.asarray(_embedder().encode(texts, normalize_embeddings=True, batch_size=64))


def entropy_normalised(probs: np.ndarray) -> np.ndarray:
    """Shannon entropy divided by log(n_classes): 0 = certain, 1 = uniform."""
    p = np.clip(probs, 1e-12, 1.0)
    return -(p * np.log(p)).sum(axis=1) / math.log(probs.shape[1])


@dataclass
class Prediction:
    label: str
    probabilities: dict[str, float]
    max_prob: float
    entropy: float


class TargetModel:
    """One target (department or priority): features -> logistic regression."""

    def __init__(self, use_tfidf: bool, c: float = 4.0):
        self.use_tfidf = use_tfidf
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True) if use_tfidf else None
        self.clf = LogisticRegression(C=c, max_iter=3000, class_weight="balanced", random_state=SEED)

    def _features(self, texts: list[str], embeddings: np.ndarray, fit: bool = False):
        if self.tfidf is None:
            return embeddings
        tf = self.tfidf.fit_transform(texts) if fit else self.tfidf.transform(texts)
        return sparse.hstack([sparse.csr_matrix(embeddings), tf]).tocsr()

    def fit(self, texts: list[str], embeddings: np.ndarray, labels: list[str]) -> "TargetModel":
        self.clf.fit(self._features(texts, embeddings, fit=True), labels)
        return self

    def predict_proba(self, texts: list[str], embeddings: np.ndarray) -> np.ndarray:
        return self.clf.predict_proba(self._features(texts, embeddings))

    @property
    def classes(self) -> list[str]:
        return list(self.clf.classes_)


class TicketClassifier:
    def __init__(self, department: TargetModel, priority: TargetModel, meta: dict | None = None):
        self.department = department
        self.priority = priority
        self.meta = meta or {}

    def predict(self, texts: list[str]) -> list[dict[str, Prediction]]:
        emb = embed(texts)
        out: list[dict[str, Prediction]] = [{} for _ in texts]
        for name, model in (("department", self.department), ("priority", self.priority)):
            probs = model.predict_proba(texts, emb)
            ent = entropy_normalised(probs)
            for i, row in enumerate(probs):
                best = int(row.argmax())
                out[i][name] = Prediction(
                    label=model.classes[best],
                    probabilities={c: float(p) for c, p in zip(model.classes, row)},
                    max_prob=float(row[best]),
                    entropy=float(ent[i]),
                )
        return out

    def save(self, path: Path = ARTIFACT) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path: Path = ARTIFACT) -> "TicketClassifier":
        return joblib.load(path)
