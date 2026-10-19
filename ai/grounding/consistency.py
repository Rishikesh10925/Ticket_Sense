"""Self-consistency signal (Blueprint V2 §13.2 "Consistency"; baseline B3 [Manakul et al.
2023]; Roadmap Week 5 "consistency sampler").

Hallucinated content tends to vary between samples, while well-supported content repeats.
For one ticket we draw k extra drafts at temperature 0.7 with distinct seeds (k = 3 by
default: cut-list item 3 applied up front, ADR 002) and compare them with the main draft:

- answer agreement: share of samples whose can_answer matches the main draft;
- claim agreement: for each pair of drafts, every claim is matched to its most similar
  claim in the other draft (cosine similarity of sentence embeddings); the pair score is
  the symmetric mean of those best matches. Claim agreement is the mean over all pairs
  that include the main draft.

Both are in [0, 1]; higher means more consistent. Samples are cached like every LLM call.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from grounding.claims import split_claims

N_SAMPLES = 3
SAMPLE_TEMPERATURE = 0.7

Embedder = Callable[[list[str]], np.ndarray]


@dataclass(frozen=True)
class Consistency:
    n_samples: int
    answer_agreement: float
    claim_agreement: float | None  # None when the main draft has no claims


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed(texts: list[str]) -> np.ndarray:
    return np.asarray(_model().encode(texts, normalize_embeddings=True))


def _claims(steps: Sequence[dict]) -> list[str]:
    return [c for s in steps for c in split_claims(s.get("text", ""))]


def pair_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Symmetric mean best-match cosine between two sets of unit vectors."""
    if len(a) == 0 or len(b) == 0:
        return 1.0 if len(a) == len(b) else 0.0
    sim = a @ b.T
    return float((sim.max(axis=1).mean() + sim.max(axis=0).mean()) / 2)


def consistency(main: dict, samples: Sequence[dict], embedder: Embedder = embed) -> Consistency:
    """`main` and each sample: {"can_answer": bool|None, "steps": [{"text": ...}]}."""
    if not samples:
        raise ValueError("need at least one sample")
    answer_agreement = sum(bool(s.get("can_answer")) == bool(main.get("can_answer")) for s in samples) / len(samples)

    main_claims = _claims(main.get("steps", []))
    if not main_claims:
        return Consistency(len(samples), round(answer_agreement, 4), None)
    main_vec = embedder(main_claims)
    scores = [pair_similarity(main_vec, embedder(c) if (c := _claims(s.get("steps", []))) else np.empty((0, 1)))
              for s in samples]
    return Consistency(len(samples), round(answer_agreement, 4), round(float(np.mean(scores)), 4))


def sample_seeds(base_seed: int, k: int = N_SAMPLES) -> list[int]:
    """Distinct, reproducible seeds for the k samples of one ticket."""
    return [base_seed * 100 + i + 1 for i in range(k)]
