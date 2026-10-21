"""Two matched ticket sets for the user study (Blueprint V2 §15.4; Roadmap Week 9,
Aashritha: "two ticket sets of 20").

Participants handle one set without AI help and the other with the three-lane
workbench, in counterbalanced order, so the two sets must be equally hard. Both sets get
the same mix by construction:

    per set: 11 type A, 3 type B, 4 type C1, 2 type C2 (the benchmark's 55/15/20/10)
             and four tickets from each of the five departments

Tickets are drawn with a recorded seed from tickets that nothing else uses: never the
locked test, the 600 selected for labelling, or the rubric pilot. C1 tickets come from
the unseen split (they exist nowhere else outside the test set).

    python ai/study/study_sets.py
"""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 2026
MIX = {"A": 11, "B": 3, "C1": 4, "C2": 2}
DEPARTMENTS = ("SAP", "Cloud", "Database", "HR", "Networking")
PER_DEPARTMENT = 4


def excluded() -> set[str]:
    sel = json.loads((ROOT / "data" / "annotation" / "selection_v1.json").read_text(encoding="utf-8"))
    out = {t for ids in sel["selected"].values() for t in ids}
    # The pilot sheet stores draft ids and the ticket text, not ticket ids: match on the text.
    pilot = ROOT / "docs" / "pilot" / "pilot_v1.csv"
    if pilot.exists():
        texts = {r["ticket"].strip() for r in csv.DictReader(pilot.open(encoding="utf-8-sig"))}
        bench = ROOT / "data" / "benchmark" / "benchmark_v1.jsonl"
        for line in filter(None, bench.read_text(encoding="utf-8").splitlines()):
            t = json.loads(line)
            if f"{t['subject']}\n\n{t['body']}".strip() in texts:
                out.add(t["ticket_id"])
    return out


def build(tickets: list[dict], split_of: dict[str, str], skip: set[str], seed: int = SEED) -> tuple[list, list]:
    """Fill both sets cell by cell (type x department) so they share the same mix."""
    pool: dict = defaultdict(list)
    for t in tickets:
        split = split_of[t["ticket_id"]]
        allowed = split in ("train", "val") or (t["type"] == "C1" and split == "unseen")
        if allowed and t["ticket_id"] not in skip:
            pool[(t["type"], t["department"])].append(t)
    rng = random.Random(seed)
    for v in pool.values():
        v.sort(key=lambda t: t["ticket_id"])
        rng.shuffle(v)

    plan = []  # (type, department) slots per set
    dept_cycle = list(DEPARTMENTS)
    rng.shuffle(dept_cycle)
    k = 0
    for typ, n in MIX.items():
        for _ in range(n):
            plan.append((typ, dept_cycle[k % len(dept_cycle)]))
            k += 1

    set_a, set_b, used_groups = [], [], set()
    for typ, dept in plan:
        for target in (set_a, set_b):
            cell = pool[(typ, dept)]
            # one paraphrase per scenario across both sets, so no participant sees a near-repeat
            while cell and cell[0]["group_id"] in used_groups:
                cell.pop(0)
            if not cell:
                raise SystemExit(f"not enough unused tickets for {typ}/{dept}")
            t = cell.pop(0)
            used_groups.add(t["group_id"])
            target.append(t)
    rng.shuffle(set_a)
    rng.shuffle(set_b)
    return set_a, set_b


def main() -> None:
    bench = ROOT / "data" / "benchmark"
    tickets = [json.loads(x) for x in (bench / "benchmark_v1.jsonl").read_text(encoding="utf-8").splitlines() if x]
    split_of = json.loads((bench / "splits_v1.json").read_text(encoding="utf-8"))["assignment"]
    set_a, set_b = build(tickets, split_of, excluded())
    out = ROOT / "docs" / "study" / "user-study" / "ticket-sets.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    def public(t):
        return {"ticket_id": t["ticket_id"], "subject": t["subject"], "body": t["body"],
                "attachment_text": t.get("attachment_text"), "department": t["department"]}

    key = {s: [{"ticket_id": t["ticket_id"], "type": t["type"], "department": t["department"]} for t in items]
           for s, items in (("set_a", set_a), ("set_b", set_b))}
    out.write_text(json.dumps({"seed": SEED, "mix_per_set": MIX, "set_a": [public(t) for t in set_a],
                               "set_b": [public(t) for t in set_b]}, indent=1) + "\n", encoding="utf-8")
    (out.parent / "ticket-sets-key.json").write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8")
    print(f"set A {len(set_a)} and set B {len(set_b)} tickets -> {out}")


if __name__ == "__main__":
    main()
