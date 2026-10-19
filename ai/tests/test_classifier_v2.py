import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "models"))

from classifier_v2 import TargetModel, entropy_normalised  # noqa: E402


def test_entropy_is_zero_when_certain_and_one_when_uniform():
    ent = entropy_normalised(np.array([[1.0, 0.0, 0.0], [1 / 3, 1 / 3, 1 / 3]]))
    assert ent[0] < 1e-6 and abs(ent[1] - 1.0) < 1e-6


def test_target_model_learns_from_embeddings_and_tfidf():
    rng = np.random.default_rng(0)
    centers = {"SAP": rng.normal(size=8), "HR": rng.normal(size=8)}
    labels = ["SAP", "HR"] * 40
    emb = np.stack([centers[lab] + rng.normal(scale=0.2, size=8) for lab in labels])
    texts = [f"{lab.lower()} issue number {i}" for i, lab in enumerate(labels)]
    for use_tfidf in (False, True):
        model = TargetModel(use_tfidf).fit(texts, emb, labels)
        probs = model.predict_proba(texts, emb)
        pred = [model.classes[i] for i in probs.argmax(axis=1)]
        assert np.mean([p == g for p, g in zip(pred, labels)]) > 0.95
        assert np.allclose(probs.sum(axis=1), 1.0)
