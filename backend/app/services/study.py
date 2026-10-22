"""User study (Roadmap Week 11; docs/study/user-study/README.md).

Every participant does both conditions on the two matched ticket sets. Set A always
comes first; the order of the conditions alternates by sign-up order (P01 manual first,
P02 workbench first, ...), so each condition meets each set equally often. Within a set,
tickets are shuffled per participant with a seed from the participant code.

A workbench task's lane, score and reasons come from the same gate the live pipeline uses
(gate.service.decide on the draft's stored signal vector, with the active thresholds), and
are fixed when the task is created: every participant sees the same stimulus.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parents[3] / "ai"
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

ORDERS = ("manual_first", "workbench_first")
CONDITIONS = ("manual", "workbench")
ACTIONS = {"manual": {"write", "escalate"}, "workbench": {"accept", "edit", "write", "escalate"}}


def order_for(index: int) -> str:
    """Counterbalancing by sign-up order: 0 -> manual first, 1 -> workbench first, ..."""
    return ORDERS[index % 2]


def plan(code: str, order: str, set_a: list[str], set_b: list[str]) -> list[tuple[str, str, str]]:
    """(ticket_id, set, condition) for every task, in the order the participant sees them."""
    if order not in ORDERS:
        raise ValueError(order)
    first, second = CONDITIONS if order == "manual_first" else CONDITIONS[::-1]
    rng = random.Random(f"study-{code}")
    a, b = list(set_a), list(set_b)
    rng.shuffle(a)
    rng.shuffle(b)
    return [(t, "A", first) for t in a] + [(t, "B", second) for t in b]


def fixed_lane(draft, features: dict, department: str | None, thresholds) -> tuple[str, float | None, list[str]]:
    """The lane the live gate would give this draft today."""
    from gate.service import decide
    from security.output_screen import screen

    passages = {e.get("n"): e.get("text", "") for e in draft.evidence or []}
    blocked = screen(draft.steps or [], passages).blocked if draft.steps else False
    shown = bool(draft.schema_valid and draft.can_answer and not blocked)
    top = (draft.evidence or [{}])[0].get("article_key")
    decision = decide(features, department, top, shown, thresholds)
    reasons = (["the output screen blocked this draft"] if blocked else []) + list(decision.reasons)
    return decision.lane, decision.score, reasons[:3]


def search_terms(query: str) -> list[str]:
    """Words of three or more letters, lower-cased, at most eight."""
    words = [w.strip(".,;:!?()[]\"'").lower() for w in query.split()]
    return list(dict.fromkeys(w for w in words if len(w) >= 3))[:8]


def rank_articles(articles: list[tuple[str, str, str]], terms: list[str], limit: int = 8) -> list[tuple[str, str, str]]:
    """Keyword ranking for the study's knowledge-base search: (key, title, content) ordered
    by how many query words appear, title matches counting double. The same search is
    offered in both conditions."""
    def score(article: tuple[str, str, str]) -> int:
        _, title, content = article
        t, c = title.lower(), content.lower()
        return sum(2 * (w in t) + (w in c) for w in terms)

    scored = [(score(a), a) for a in articles]
    return [a for s, a in sorted(scored, key=lambda x: (-x[0], x[1][1])) if s > 0][:limit]
