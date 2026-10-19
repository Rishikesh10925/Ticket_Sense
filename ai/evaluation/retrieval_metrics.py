"""Retrieval metrics against gold provenance (Blueprint V2 §15.1): Recall@k, MRR,
nDCG@k with binary relevance. `ranked` is a list of distinct article ids in rank order."""

from __future__ import annotations

import math
from collections.abc import Sequence


def recall_at_k(ranked: Sequence[str], gold: Sequence[str], k: int = 5) -> float:
    if not gold:
        raise ValueError("recall is undefined without gold articles")
    return len(set(ranked[:k]) & set(gold)) / len(set(gold))


def reciprocal_rank(ranked: Sequence[str], gold: Sequence[str]) -> float:
    gold_set = set(gold)
    for position, item in enumerate(ranked, start=1):
        if item in gold_set:
            return 1.0 / position
    return 0.0


def ndcg_at_k(ranked: Sequence[str], gold: Sequence[str], k: int = 10) -> float:
    gold_set = set(gold)
    dcg = sum(1.0 / math.log2(i + 1) for i, item in enumerate(ranked[:k], start=1) if item in gold_set)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(gold_set), k) + 1))
    return dcg / ideal if ideal else 0.0
