"""Labelling assignment planner (docs/annotation-tool.md, "Assignment algorithm";
Roadmap Week 6, annotation tool v1).

Pure functions, so the plan is testable and reproducible from its seed:

1. Pick the overlap set, spread evenly over strata (ticket type x department).
2. Give each overlap draft to two different reviewers and every other draft to one,
   always to the least-loaded reviewer (ties broken by the seeded RNG), so loads differ
   by at most one item.
3. Shuffle each reviewer's list with the same seeded RNG and store it as `position`.

Reviewers never learn which items are in the overlap set: `overlap` is stored on the
assignment but never returned by the /annotate endpoints.

`plan_adjudications` gives a disagreeing overlap draft (the two labels differ on
`acceptable`) to a third reviewer who has not seen it.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass(frozen=True)
class PlannedAssignment:
    draft_id: Hashable
    annotator_id: Hashable
    overlap: bool
    position: int


def choose_overlap(drafts: Sequence[tuple[Hashable, str]], n_overlap: int, rng: random.Random) -> set:
    """`drafts` is [(draft_id, stratum)]. Round-robin over shuffled strata, so every
    stratum contributes in proportion until it runs out."""
    by_stratum: dict[str, list] = defaultdict(list)
    for draft_id, stratum in drafts:
        by_stratum[stratum].append(draft_id)
    queues = []
    for stratum in sorted(by_stratum):
        ids = sorted(by_stratum[stratum], key=str)
        rng.shuffle(ids)
        queues.append(ids)
    chosen: list = []
    while len(chosen) < min(n_overlap, len(drafts)):
        for queue in queues:
            if queue and len(chosen) < n_overlap:
                chosen.append(queue.pop())
    return set(chosen)


def _least_loaded(load: dict, exclude: set, rng: random.Random):
    candidates = [a for a in load if a not in exclude]
    if not candidates:
        raise ValueError("not enough annotators for this assignment")
    lowest = min(load[a] for a in candidates)
    return rng.choice(sorted((a for a in candidates if load[a] == lowest), key=str))


def plan_assignments(
    drafts: Sequence[tuple[Hashable, str]],
    annotators: Sequence[Hashable],
    n_overlap: int,
    seed: int,
) -> list[PlannedAssignment]:
    if len(annotators) < 2 and n_overlap > 0:
        raise ValueError("double annotation needs at least two annotators")
    if len({d for d, _ in drafts}) != len(drafts):
        raise ValueError("duplicate draft ids")
    rng = random.Random(seed)
    overlap = choose_overlap(drafts, n_overlap, rng)

    load = {a: 0 for a in annotators}
    items: dict = defaultdict(list)  # annotator -> [(draft_id, overlap)]
    ordered = sorted((d for d, _ in drafts), key=str)
    for draft_id in [d for d in ordered if d in overlap] + [d for d in ordered if d not in overlap]:
        given: set = set()
        for _ in range(2 if draft_id in overlap else 1):
            annotator = _least_loaded(load, given, rng)
            given.add(annotator)
            load[annotator] += 1
            items[annotator].append((draft_id, draft_id in overlap))

    plan = []
    for annotator in sorted(items, key=str):
        own = items[annotator]
        rng.shuffle(own)
        plan.extend(PlannedAssignment(d, annotator, o, i) for i, (d, o) in enumerate(own, start=1))
    return plan


def plan_adjudications(
    disagreements: Sequence[tuple[Hashable, Sequence[Hashable]]],
    annotators: Sequence[Hashable],
    current_load: dict,
    next_position: dict,
    seed: int,
) -> list[PlannedAssignment]:
    """`disagreements` is [(draft_id, [annotators who already labelled it])]. Each draft
    goes to the least-loaded reviewer who has not seen it, after their existing items."""
    rng = random.Random(seed)
    load = {a: current_load.get(a, 0) for a in annotators}
    position = {a: next_position.get(a, 1) for a in annotators}
    plan = []
    for draft_id, seen in sorted(disagreements, key=lambda x: str(x[0])):
        annotator = _least_loaded(load, set(seen), rng)
        load[annotator] += 1
        plan.append(PlannedAssignment(draft_id, annotator, True, position[annotator]))
        position[annotator] += 1
    return plan
