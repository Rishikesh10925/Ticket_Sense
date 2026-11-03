"""Three-author audit of drafts: agreement and outcomes
("Three-Author Human Annotation Protocol", AUTHOR-v2, 3 November 2026; docs/author-audit/).
No database here, so all of it is unit tested; backend/app/scripts/author_audit.py does
the reading and writing. The sample is the frozen human-audit sample (human_audit.select).

Agreement is computed on the original ratings, before any adjudication: Krippendorff's
alpha across the three authors, ordinal for Q1 (A<M<R<W, U left out) and Q2 (Fully <
Partially < Not supported, Unclear left out), nominal for binary Q1 and for Q3 (Unclear
left out). Every left-out answer is counted and reported.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any

from evaluation.human_audit import Q1, Q2, Q3, QUICK_SECONDS, SIMILAR_REASONS

RUBRIC = "AUTHOR-v2"
Q1_ORDER = ("A", "M", "R", "W")
Q2_ORDER = ("Fully", "Partially", "Not supported")
Q3_ORDER = ("Yes", "No")
BOOTSTRAP = 2000


def alpha(units: list[list[str | None]], order: tuple[str, ...], ordinal: bool) -> float | None:
    """Krippendorff's alpha. `units` holds one list of answers per case, None where a rater
    gave no usable value; cases with fewer than two usable values do not count."""
    coincidence: dict[tuple[str, str], float] = defaultdict(float)
    for unit in units:
        values = [v for v in unit if v is not None]
        m = len(values)
        if m < 2:
            continue
        for i, a in enumerate(values):
            for j, b in enumerate(values):
                if i != j:
                    coincidence[a, b] += 1 / (m - 1)
    totals = {c: sum(coincidence[c, k] for k in order) for c in order}
    n = sum(totals.values())
    if n < 2:
        return None

    def delta(c: str, k: str) -> float:
        if c == k:
            return 0.0
        if not ordinal:
            return 1.0
        lo, hi = sorted((order.index(c), order.index(k)))
        return (sum(totals[order[g]] for g in range(lo, hi + 1)) - (totals[c] + totals[k]) / 2) ** 2

    observed = sum(coincidence[c, k] * delta(c, k) for c in order for k in order)
    expected = sum(totals[c] * totals[k] * delta(c, k) for c in order for k in order) / (n - 1)
    if expected == 0:
        return None  # every usable answer is the same category: alpha is undefined
    return round(1 - observed / expected, 4)


def _usable(value: str, order: tuple[str, ...]) -> str | None:
    return value if value in order else None


def _binary(q1: str) -> str | None:
    return {"A": "ok", "M": "ok", "R": "bad", "W": "bad"}.get(q1)


MEASURES = {
    # name: (how to read one rating, category order, ordinal)
    "q1": (lambda r: _usable(r["q1"], Q1_ORDER), Q1_ORDER, True),
    "q1_binary": (lambda r: _binary(r["q1"]), ("ok", "bad"), False),
    "q2": (lambda r: _usable(r["q2"], Q2_ORDER), Q2_ORDER, True),
    "q3": (lambda r: _usable(r["q3"], Q3_ORDER), Q3_ORDER, False),
}


def _bootstrap(units: list[list[str | None]], order: tuple[str, ...], ordinal: bool, seed: int) -> list[float] | None:
    """95% interval from resampling cases (scenarios), as the protocol suggests."""
    rng = random.Random(seed)
    values = []
    for _ in range(BOOTSTRAP):
        a = alpha([units[rng.randrange(len(units))] for _ in units], order, ordinal)
        if a is not None:
            values.append(a)
    if len(values) < BOOTSTRAP // 2:
        return None
    values.sort()
    return [values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]]


def check_rating(r: dict[str, str]) -> list[str]:
    """What is wrong with one finished row under AUTHOR-v2's reason rule. A/M with Q3 = No
    is allowed but needs a written rationale (the protocol's consistency warning)."""
    problems = []
    for q, allowed in (("q1", Q1), ("q2", Q2), ("q3", Q3)):
        if r[q] not in allowed:
            problems.append(f"{q.upper()} is {r[q]!r}")
    if problems:
        return problems
    needs = r["q1"] in ("R", "W", "U") or r["q2"] != "Fully" or r["q3"] != "Yes"
    if needs and not r["reason"].strip():
        problems.append("a reason is required")
    return problems


def _grounded_unacceptable(r: dict[str, str]) -> bool | None:
    if r["q1"] in ("A", "M") or r["q2"] in ("Partially", "Not supported"):
        return False
    return None if r["q1"] == "U" or r["q2"] == "Unclear" else True


def _wrong_topic(r: dict[str, str]) -> bool | None:
    base = _grounded_unacceptable(r)
    if base is False or r["q3"] == "Yes":
        return False
    return None if base is None or r["q3"] == "Unclear" else True


OUTCOMES = {"grounded_but_unacceptable": _grounded_unacceptable, "wrong_topic": _wrong_topic}


def outcome_status(rows: list[dict[str, str]], rule, authors: int = 3) -> str:
    """'unanimous' needs every author's original rating to meet the rule; 'majority' and the
    rest are reported as such, never as corroborated findings."""
    if len(rows) < authors:
        return "incomplete"
    votes = [rule(r) for r in rows]
    if all(v is True for v in votes):
        return "unanimous_positive"
    if all(v is False for v in votes):
        return "unanimous_negative"
    if sum(v is True for v in votes) * 2 > len(votes):
        return "majority_positive"
    return "unresolved"


def analyse(cases: list[dict], ratings: dict[str, dict[str, dict[str, str]]],
            eligible_scenarios: dict[str, int], seed: int) -> dict[str, Any]:
    """`ratings`: author -> draft id -> finished row. Only cases all authors finished count
    for agreement; every denominator is reported."""
    authors = sorted(ratings)
    complete = [c for c in cases if all(c["draft_id"] in ratings[a] for a in authors)]
    rows_of = {c["draft_id"]: [ratings[a][c["draft_id"]] for a in authors] for c in complete}
    report: dict[str, Any] = {"rubric": RUBRIC, "authors": {}, "selected": len(cases), "complete": len(complete),
                              "agreement": {}, "disagreements": {}, "outcomes": {}}

    for a in authors:
        mine = ratings[a]
        seconds = [float(r["seconds"] or 0) for r in mine.values()]
        report["authors"][a] = {
            "finished": len(mine),
            "median_seconds": round(statistics.median(seconds), 1) if seconds else None,
            "under_quick_limit": sum(s < QUICK_SECONDS for s in seconds),
            "pasted_reasons": sum(r.get("pasted") == "yes" for r in mine.values()),
            "seen_before": sum(r.get("seen_before") == "yes" for r in mine.values()),
            "am_with_q3_no": sum(r["q1"] in ("A", "M") and r["q3"] == "No" for r in mine.values()),
            **{q: dict(sorted(Counter(r[q] for r in mine.values()).items())) for q in ("q1", "q2", "q3")},
        }

    for name, (read, order, ordinal) in MEASURES.items():
        units = [[read(r) for r in rows_of[c["draft_id"]]] for c in complete]
        full = [u for u in units if None not in u]
        report["agreement"][name] = {
            "alpha": alpha(units, order, ordinal),
            "interval_95": _bootstrap(units, order, ordinal, seed) if units else None,
            "metric": "ordinal" if ordinal else "nominal",
            "cases_with_all_usable": len(full),
            "left_out_answers": sum(v is None for u in units for v in u),
            "all_agree": sum(len(set(u)) == 1 for u in full),
            "two_of_three": sum(max(Counter(u).values()) == 2 for u in full) if len(authors) == 3 else None,
        }
        report["disagreements"][name] = sorted(c["draft_id"] for c, u in zip(complete, units)
                                               if len({v for v in u if v is not None}) > 1)

    pairs = {}
    for x, y in combinations(authors, 2):
        shared = [i for i in rows_of]
        same = sum(all(ratings[x][i][q] == ratings[y][i][q] for q in ("q1", "q2", "q3")) for i in shared)
        reasons = [(ratings[x][i]["reason"], ratings[y][i]["reason"]) for i in shared
                   if len(ratings[x][i]["reason"]) > 20 and len(ratings[y][i]["reason"]) > 20]
        pairs[f"{x}+{y}"] = {"identical_q1_q2_q3": same, "cases": len(shared),
                             "near_identical_reasons": sum(SequenceMatcher(None, a, b).ratio() >= SIMILAR_REASONS for a, b in reasons)}
    report["pairs"] = pairs  # independence checks, not agreement statistics

    random_part = [c for c in cases if c["part"] == "I"]
    per_type = Counter(c["type"] for c in random_part)
    total = sum(eligible_scenarios.values())
    for name, rule in OUTCOMES.items():
        table: dict[str, Counter] = defaultdict(Counter)
        status_of = {}
        for c in cases:
            rows = [ratings[a][c["draft_id"]] for a in authors if c["draft_id"] in ratings[a]]
            status_of[c["draft_id"]] = s = outcome_status(rows, rule, len(authors))
            table[f"{c['part']}/{c['group']}"][s] += 1
            table[f"{c['part']}/{c['group']}"]["selected"] += 1
        lower = upper = 0.0
        for t, n in per_type.items():
            of_type = [status_of[c["draft_id"]] for c in random_part if c["type"] == t]
            share = eligible_scenarios[t] / total
            lower += share * sum(s == "unanimous_positive" for s in of_type) / n
            upper += share * sum(s != "unanimous_negative" for s in of_type) / n
        report["outcomes"][name] = {
            "counts": {k: dict(sorted(v.items())) for k, v in sorted(table.items())},
            "unanimous_cases": sorted(i for i, s in status_of.items() if s == "unanimous_positive"),
            # Part I only, weighted by eligible scenarios per type; bounds treat every
            # case short of unanimous negative as possibly positive. Not confidence intervals.
            "part_I_weighted_bounds": [round(lower, 4), round(upper, 4)],
        }
    return report
