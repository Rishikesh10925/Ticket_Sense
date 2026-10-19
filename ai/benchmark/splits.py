"""Split assignment for the benchmark (docs/split-manifest.md, Blueprint V2 §11.5).

The unit of assignment is the *leakage group*: the gold article for A, B and C1 tickets
(every paraphrase and every scenario written from one article lands in one split), and
the scenario `group_id` for C2 tickets, which have no article. Groups are assigned
greedily within strata of (type, department) so each split keeps the overall mix.

C1 (unseen-topic) tickets never enter train, validation or calibration: a slice goes to
the locked test, so the test is "sampled across all four types", and the rest form the
unseen-topic set for H3.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

# Shares of tickets per split, from the §11.5 sizes on an 1,800-ticket benchmark:
# seen-topic tickets (A, B, C2: ~1,440) -> train 840, val 150, calib 250, test 200;
# C1 (~360) -> test 50, unseen 310.
SEEN_TARGETS = {"train": 0.583, "val": 0.104, "calib": 0.174, "test": 0.139}
C1_TARGETS = {"test": 0.139, "unseen": 0.861}


def leakage_group(record: dict) -> str:
    if record["gold_articles"]:
        return "ART:" + "+".join(sorted(record["gold_articles"]))
    return "GRP:" + record["group_id"]


def assign_splits(records: list[dict], seed: int = 2026) -> dict[str, str]:
    """ticket_id -> split. Deterministic for a given seed and record set."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        groups[leakage_group(r)].append(r)

    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for key, members in groups.items():
        first = members[0]
        strata[(first["type"] if first["type"] == "C1" else "seen:" + first["type"], first["department"])].append(key)

    rng = random.Random(seed)
    assignment: dict[str, str] = {}
    for stratum in sorted(strata):
        keys = sorted(strata[stratum])
        rng.shuffle(keys)
        targets = C1_TARGETS if stratum[0] == "C1" else SEEN_TARGETS
        total = sum(len(groups[k]) for k in keys)
        filled = dict.fromkeys(targets, 0)
        # Largest groups first, so the greedy fill lands close to the targets.
        for key in sorted(keys, key=lambda k: -len(groups[k])):
            split = max(targets, key=lambda s: targets[s] * total - filled[s])
            filled[split] += len(groups[key])
            for r in groups[key]:
                assignment[r["ticket_id"]] = split
    return assignment


def check_manifest(records: Iterable[dict], assignment: dict[str, str]) -> list[str]:
    """Leakage and placement problems; empty means valid."""
    problems = []
    seen_split: dict[str, str] = {}
    for r in records:
        split = assignment.get(r["ticket_id"])
        if split is None:
            problems.append(f"{r['ticket_id']} has no split")
            continue
        g = leakage_group(r)
        if seen_split.setdefault(g, split) != split:
            problems.append(f"leakage group {g} spans {seen_split[g]} and {split}")
        if r["type"] == "C1" and split not in ("test", "unseen"):
            problems.append(f"{r['ticket_id']} is C1 but in {split}")
        if r["type"] != "C1" and split == "unseen":
            problems.append(f"{r['ticket_id']} is {r['type']} but in unseen")
    return sorted(set(problems))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(tickets_path: Path, out_path: Path, seed: int = 2026) -> dict:
    records = [json.loads(line) for line in tickets_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assignment = assign_splits(records, seed)
    problems = check_manifest(records, assignment)
    if problems:
        raise ValueError("invalid split manifest:\n" + "\n".join(problems))
    counts: dict[str, int] = defaultdict(int)
    for split in assignment.values():
        counts[split] += 1
    manifest = {
        "tickets_file": tickets_path.as_posix(),
        "tickets_sha256": file_sha256(tickets_path),
        "seed": seed,
        "counts": dict(sorted(counts.items())),
        "assignment": dict(sorted(assignment.items())),
    }
    out_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest
