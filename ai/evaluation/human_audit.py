"""Independent human audit of drafts: selection and analysis
(protocol: docs/human-audit/README.md, "Independent Human Annotation Sampling Protocol",
31 October 2026). No database or model here, so all of it is unit tested;
backend/app/scripts/human_audit.py does the reading and writing.

Selection is by scenario: at most one draft per scenario, random part first without
looking at NLI or judge labels, then three targeted groups from what remains. Analysis
keeps every denominator visible and estimates only from the random part.
"""

from __future__ import annotations

import random
import re
import statistics
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from evaluation.agreement import cohen_kappa

TYPES = ("A", "B", "C1", "C2")
NLI_PASS = 0.5  # the stored rule: a claim passes when its support is at least this
TARGET_SHARE = {20: (4, 3, 1), 40: (8, 5, 3), 80: (16, 11, 5), 100: (20, 13, 7), 160: (32, 21, 11), 200: (40, 27, 13)}
QUICK_SECONDS = 30  # a ticket, a draft, its passages and three answers cannot be read faster
SIMILAR_REASONS = 0.8

Q1 = ("A", "M", "R", "W", "U")
Q2 = ("Fully", "Partially", "Not supported", "Unclear")
Q3 = ("Yes", "No", "Unclear")


def allocate_random(total: int, available: dict[str, int]) -> dict[str, int]:
    """Equal counts per type, capped by what is available. What a capped type cannot take
    is shared equally among the others; a remainder goes to the types with most scenarios."""
    if total > sum(available.values()):
        raise ValueError(f"{total} random cases but only {sum(available.values())} eligible scenarios")
    quota = dict.fromkeys(available, 0)
    left = total
    while left:
        open_types = sorted((t for t in available if quota[t] < available[t]), key=lambda t: (-available[t], t))
        share = max(left // len(open_types), 1)
        for t in open_types:
            take = min(share, available[t] - quota[t], left)
            quota[t] += take
            left -= take
    return quota


def flags(draft: dict, blind: dict[str, str]) -> dict[str, bool]:
    """The protocol's targeted-group rules, from stored values only."""
    supports = [c["support"] for c in draft["claims"]]
    judge = draft.get("judge")
    second = blind.get(draft["draft_id"])
    return {
        "nli_pass_suspected_error": bool(supports) and min(supports) >= NLI_PASS and judge in ("R", "W"),
        "judge_disagreement": judge in ("A", "M", "R", "W") and second in ("A", "M", "R", "W")
        and (judge in ("A", "M")) != (second in ("A", "M")),
        "nli_rejected": bool(supports) and min(supports) < NLI_PASS,
    }


def _by_scenario(drafts: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for d in sorted(drafts, key=lambda d: d["draft_id"]):
        out[d["group_id"]].append(d)
    return out


def _draw(drafts: list[dict], k: int, rng: random.Random, taken: set[str]) -> list[dict]:
    """k distinct scenarios uniformly, then one draft uniformly within each."""
    scenarios = _by_scenario([d for d in drafts if d["group_id"] not in taken])
    if k > len(scenarios):
        raise ValueError(f"need {k} scenarios, {len(scenarios)} qualify")
    chosen = rng.sample(sorted(scenarios), k)
    taken.update(chosen)
    return [rng.choice(scenarios[s]) for s in chosen]


def select(drafts: list[dict], blind: dict[str, str], total: int, seed: int) -> dict[str, Any]:
    """Mode H: 60% random within type, then 40% targeted. `drafts` is the frozen eligible
    pool. Raises rather than moves cases silently when a quota cannot be filled."""
    types: dict[str, set[str]] = defaultdict(set)
    for d in drafts:
        types[d["group_id"]].add(d["type"])
    mixed = [g for g, t in types.items() if len(t) > 1]
    if mixed:
        raise ValueError(f"scenarios with more than one type, e.g. {mixed[0]}")
    available = dict(sorted(Counter(next(iter(t)) for t in types.values()).items()))
    targeted = TARGET_SHARE[total]
    quota = allocate_random(total - sum(targeted), available)

    rng = random.Random(seed)
    taken: set[str] = set()
    cases = []
    for t in sorted(quota):
        for d in _draw([x for x in drafts if x["type"] == t], quota[t], rng, taken):
            cases.append(d | {"part": "I", "group": f"random_{t}"})
    flagged = [d | {"flags": flags(d, blind)} for d in drafts]
    for name, k in (("nli_pass_suspected_error", targeted[0]), ("judge_disagreement", targeted[1])):
        for d in _draw([x for x in flagged if x["flags"][name]], k, rng, taken):
            cases.append(d | {"part": "II", "group": name})
    rejected = [x for x in flagged if x["flags"]["nli_rejected"]]
    judged_ok = (targeted[2] + 1) // 2  # subgroup rule, fixed here before drawing
    for name, pool, k in (("control_judge_accepted", [x for x in rejected if x.get("judge") in ("A", "M")], judged_ok),
                          ("control_judge_rejected", [x for x in rejected if x.get("judge") in ("R", "W")], targeted[2] - judged_ok)):
        for d in _draw(pool, k, rng, taken):
            cases.append(d | {"part": "II", "group": name})
    for c in cases:
        c["flags"] = flags(c, blind)
    return {"available_scenarios": available, "random_quota": quota, "targeted_quota": list(targeted), "cases": cases}


def split_into_pairs(cases: list[dict], pairs: int, seed: int) -> list[list[dict]]:
    """Deal cases to reviewer pairs so each pair gets a similar mix of parts and groups."""
    rng = random.Random(seed)
    ordered = sorted(cases, key=lambda c: (c["group"], rng.random()))
    return [ordered[i::pairs] for i in range(pairs)]


def read_xlsx(path: Path) -> dict[str, list[dict[str, str]]]:
    """Sheets as lists of row dicts. Standard library only; reads both our own file and one
    resaved by Excel (shared strings)."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        targets = {r.get("Id"): r.get("Target", "") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        out: dict[str, list[dict[str, str]]] = {}
        for sheet in ET.fromstring(z.read("xl/workbook.xml")).iter("{%s}sheet" % ns["m"]):
            target = targets[sheet.get(rel)].lstrip("/")
            root = ET.fromstring(z.read(target if target.startswith("xl/") else f"xl/{target}"))
            table = []
            for row in root.iter("{%s}row" % ns["m"]):
                cells: dict[str, str] = {}
                for c in row.findall("m:c", ns):
                    col = re.sub(r"\d", "", c.get("r", ""))
                    v = c.find("m:v", ns)
                    if c.get("t") == "inlineStr":
                        cells[col] = "".join(t.text or "" for t in c.iter("{%s}t" % ns["m"]))
                    elif v is not None and v.text is not None:
                        cells[col] = shared[int(v.text)] if c.get("t") == "s" else v.text
                table.append(cells)
            if table:
                head = table[0]
                out[sheet.get("name", "")] = [{head[k]: r.get(k, "") for k in head} for r in table[1:]]
    return out


def check_rating(r: dict[str, str]) -> list[str]:
    """What is wrong with one finished row, under the protocol's reason rule."""
    problems = []
    if r["q1"] not in Q1:
        problems.append(f"Q1 is {r['q1']!r}")
    if r["q2"] not in Q2:
        problems.append(f"Q2 is {r['q2']!r}")
    if r["q3"] not in Q3:
        problems.append(f"Q3 is {r['q3']!r}")
    if not problems and (r["q1"] in ("R", "W", "U") or r["q2"] != "Fully" or r["q3"] != "Yes") and not r["reason"].strip():
        problems.append("a reason is required")
    return problems


def _supported_unacceptable(r: dict[str, str]) -> bool | None:
    """True, False, or None when this reviewer's answers leave it undetermined."""
    if r["q1"] in ("A", "M") or r["q2"] in ("Partially", "Not supported"):
        return False
    return None if r["q1"] == "U" or r["q2"] == "Unclear" else True


def _wrong_topic(r: dict[str, str]) -> bool | None:
    base = _supported_unacceptable(r)
    if base is False or r["q3"] == "Yes":
        return False
    return None if base is None or r["q3"] == "Unclear" else True


OUTCOMES = {"supported_but_unacceptable": _supported_unacceptable, "wrong_topic": _wrong_topic}


def outcome_status(ratings: list[dict[str, str]], rule, third: dict[str, str] | None = None) -> str:
    """confirmed / negative need both reviewers; a third careful reviewer may settle a
    dispute (reported separately); anything else stays unresolved."""
    if len(ratings) < 2:
        return "incomplete"
    first, second = rule(ratings[0]), rule(ratings[1])
    if first is True and second is True:
        return "confirmed"
    if first is False and second is False:
        return "negative"
    if third is not None and (verdict := rule(third)) is not None and verdict in (first, second):
        return "confirmed_adjudicated" if verdict else "negative_adjudicated"
    return "unresolved"


def _agreement(a: list[str], b: list[str], categories: tuple[str, ...]) -> dict[str, Any]:
    n = len(a)
    return {"n": n, "raw": round(sum(x == y for x, y in zip(a, b)) / n, 4) if n else None,
            "confusion": {f"{x}|{y}": c for (x, y), c in sorted(Counter(zip(a, b)).items())},
            "kappa": _kappa(a, b, categories)}


def _kappa(a: list[str], b: list[str], categories: tuple[str, ...]) -> float | None:
    if len(a) < 10:
        return None  # too few to mean anything, as in agreement.py
    try:
        return cohen_kappa(a, b, categories=categories)
    except ZeroDivisionError:
        return None


def analyse(cases: list[dict], ratings: dict[str, dict[str, dict[str, str]]], pairs: dict[str, list[str]],
            eligible_scenarios: dict[str, int], adjudication: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
    """`ratings`: reviewer -> draft id -> finished row. `pairs`: draft id -> its two reviewers."""
    adjudication = adjudication or {}
    report: dict[str, Any] = {"reviewers": {}, "pairs": {}, "outcomes": {}, "disputed_binary": []}

    for reviewer, mine in sorted(ratings.items()):
        seconds = [float(r["seconds"] or 0) for r in mine.values()]
        report["reviewers"][reviewer] = {
            "finished": len(mine),
            "assigned": sum(reviewer in p for p in pairs.values()),
            "median_seconds": round(statistics.median(seconds), 1) if seconds else None,
            "under_quick_limit": sum(s < QUICK_SECONDS for s in seconds),
            "q1": dict(sorted(Counter(r["q1"] for r in mine.values()).items())),
        }

    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for draft_id, two in pairs.items():
        grouped[tuple(two)].append(draft_id)
    for pair, ids in sorted(grouped.items()):
        both = [i for i in ids if all(i in ratings.get(p, {}) for p in pair)]
        x, y = [[ratings[p][i] for i in both] for p in pair]
        determinate = [(a["q1"], b["q1"]) for a, b in zip(x, y) if a["q1"] != "U" and b["q1"] != "U"]
        binary = [("ok" if a in ("A", "M") else "bad", "ok" if b in ("A", "M") else "bad") for a, b in determinate]
        reasons = [(a["reason"], b["reason"]) for a, b in zip(x, y) if len(a["reason"]) > 20 and len(b["reason"]) > 20]
        report["pairs"]["+".join(pair)] = {
            "double_rated": len(both),
            "q1": _agreement([a["q1"] for a in x], [b["q1"] for b in y], Q1),
            "q2": _agreement([a["q2"] for a in x], [b["q2"] for b in y], Q2),
            "q3": _agreement([a["q3"] for a in x], [b["q3"] for b in y], Q3),
            "binary_acceptable": _agreement([a for a, _ in binary], [b for _, b in binary], ("ok", "bad")),
            "u_ratings": sum(r["q1"] == "U" for r in x + y),
            "near_identical_reasons": sum(SequenceMatcher(None, a, b).ratio() >= SIMILAR_REASONS for a, b in reasons),
            "reasons_compared": len(reasons),
        }
        for i, a, b in zip(both, x, y):
            if (a["q1"] in ("A", "M")) != (b["q1"] in ("A", "M")) and "U" not in (a["q1"], b["q1"]):
                report["disputed_binary"].append(i)

    random_part = [c for c in cases if c["part"] == "I"]
    selected_per_type = Counter(c["type"] for c in random_part)
    total_eligible = sum(eligible_scenarios.values())
    for name, rule in OUTCOMES.items():
        table: dict[str, Counter] = defaultdict(Counter)
        status_of = {}
        for c in cases:
            rows = [ratings[p][c["draft_id"]] for p in pairs[c["draft_id"]] if c["draft_id"] in ratings.get(p, {})]
            status = outcome_status(rows, rule, adjudication.get(c["draft_id"]))
            status_of[c["draft_id"]] = status
            table[f"{c['part']}/{c['group']}"][status] += 1
            table[f"{c['part']}/{c['group']}"]["selected"] += 1
        lower = upper = 0.0
        for t, n in selected_per_type.items():
            of_type = [status_of[c["draft_id"]] for c in random_part if c["type"] == t]
            confirmed = sum(s.startswith("confirmed") for s in of_type)
            open_cases = sum(s in ("unresolved", "incomplete") for s in of_type)
            share = eligible_scenarios[t] / total_eligible
            lower += share * confirmed / n
            upper += share * (confirmed + open_cases) / n
        report["outcomes"][name] = {
            "counts": {k: dict(sorted(v.items())) for k, v in sorted(table.items())},
            # missing-label bounds on the frozen eligible pool, Part I only; not confidence intervals
            "part_I_weighted_bounds": [round(lower, 4), round(upper, 4)],
        }
    return report
