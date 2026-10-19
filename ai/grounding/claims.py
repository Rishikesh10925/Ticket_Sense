"""Claim-level grounding check (Blueprint V2 §12.3; Roadmap Week 5).

Each draft step is split into atomic claims. An NLI cross-encoder scores whether the
passage(s) the step cites entail each claim. Support for a claim is the best entailment
probability over its cited passages, also checking short sentence windows of long
passages so one relevant sentence is not diluted by the rest. Groundedness is the share
of claims with support >= SUPPORTED. The weakest claims are kept for the assisted lane.

The checker itself is validated against a 100-draft manual audit (Week 6) so its errors
are known; see docs/groundedness-audit.md.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache

NLI_MODEL = "cross-encoder/nli-deberta-v3-base"
ENTAILMENT_INDEX = 1  # id2label {0: contradiction, 1: entailment, 2: neutral}
SUPPORTED = 0.5
WINDOW_SENTENCES = 3
LONG_PASSAGE_WORDS = 80

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
_CLAUSE = re.compile(r";\s+|,?\s+and then\s+|,\s+then\s+", re.IGNORECASE)
_MIN_WORDS = 3

# (premise, hypothesis) pairs -> entailment probabilities
Scorer = Callable[[list[tuple[str, str]]], list[float]]


@dataclass(frozen=True)
class ClaimScore:
    step_index: int
    claim_index: int
    text: str
    cited: tuple[int, ...]
    support: float


@dataclass(frozen=True)
class Grounding:
    claims: tuple[ClaimScore, ...]
    groundedness: float | None  # share of supported claims; None when there are no claims
    min_support: float | None
    mean_support: float | None

    def weakest(self, k: int = 3) -> list[ClaimScore]:
        return sorted(self.claims, key=lambda c: c.support)[:k]


def split_claims(step_text: str) -> list[str]:
    """Sentences, then clauses joined by ';' or 'then'. Fragments shorter than three words
    are merged into the previous claim so a claim always says something checkable."""
    pieces: list[str] = []
    for sentence in _SENTENCE.split(" ".join(step_text.split())):
        for clause in _CLAUSE.split(sentence):
            clause = clause.strip(" ,;")
            if not clause:
                continue
            if pieces and len(clause.split()) < _MIN_WORDS:
                pieces[-1] = f"{pieces[-1]} {clause}"
            else:
                pieces.append(clause)
    return pieces


def _windows(passage: str) -> list[str]:
    if len(passage.split()) <= LONG_PASSAGE_WORDS:
        return [passage]
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n+", passage) if s.strip()]
    step = max(1, WINDOW_SENTENCES - 1)
    windows = [" ".join(sentences[i:i + WINDOW_SENTENCES]) for i in range(0, len(sentences), step)]
    return [passage, *windows]


@lru_cache(maxsize=1)
def _cross_encoder():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(NLI_MODEL)


def nli_scorer(pairs: list[tuple[str, str]]) -> list[float]:
    if not pairs:
        return []
    probs = _cross_encoder().predict(pairs, apply_softmax=True, batch_size=32, show_progress_bar=False)
    return [float(p[ENTAILMENT_INDEX]) for p in probs]


def check_draft(steps: Sequence[dict], passages: dict[int, str], scorer: Scorer = nli_scorer) -> Grounding:
    """`steps` as produced by generation.drafting ({"text", "citations"}); `passages` maps
    passage number -> passage text. A claim citing no existing passage gets support 0."""
    claims: list[tuple[int, int, str, tuple[int, ...]]] = []
    for si, step in enumerate(steps):
        cited = tuple(c for c in step.get("citations", []) if c in passages)
        for ci, claim in enumerate(split_claims(step.get("text", ""))):
            claims.append((si, ci, claim, cited))

    pairs: list[tuple[str, str]] = []
    owners: list[int] = []
    for idx, (_, _, claim, cited) in enumerate(claims):
        for n in cited:
            for window in _windows(passages[n]):
                pairs.append((window, claim))
                owners.append(idx)
    scores = scorer(pairs)
    best = [0.0] * len(claims)
    for owner, score in zip(owners, scores):
        best[owner] = max(best[owner], score)

    scored = tuple(ClaimScore(si, ci, text, cited, round(best[i], 4)) for i, (si, ci, text, cited) in enumerate(claims))
    if not scored:
        return Grounding((), None, None, None)
    supports = [c.support for c in scored]
    return Grounding(
        claims=scored,
        groundedness=round(sum(s >= SUPPORTED for s in supports) / len(supports), 4),
        min_support=min(supports),
        mean_support=round(sum(supports) / len(supports), 4),
    )
