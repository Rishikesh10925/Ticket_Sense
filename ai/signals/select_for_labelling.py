"""Choose the 600 drafts that outside reviewers label (docs/annotation-tool.md; prereg
"Data and splits"; Roadmap Week 7, Shivaganesh).

    locked test   250   every headline number; read once in Week 10
    calibration   200   fits calibration and the risk-controlled thresholds
    train + val   150   checks the judge against humans and the model on validation

Within each split the quota is spread over (ticket type, department) cells in
proportion to their size (largest-remainder rounding), then drafts are drawn at random
inside each cell with a recorded seed. Ticket ids only: nothing about the drafts'
quality, scores or judge labels is read, so the choice cannot favour any method.

    python ai/signals/select_for_labelling.py --version v1 --out data/annotation/selection_v1.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUOTAS = {"test": 250, "calib": 200, "train+val": 150}
SELECTION_SEED = 2026


def allocate(cell_sizes: dict, total: int) -> dict:
    """Largest-remainder allocation of `total` over cells, capped at each cell's size."""
    size = sum(cell_sizes.values())
    if total >= size:
        return dict(cell_sizes)
    exact = {c: total * n / size for c, n in cell_sizes.items()}
    alloc = {c: int(x) for c, x in exact.items()}
    for c in sorted(exact, key=lambda c: (exact[c] - alloc[c], str(c)), reverse=True)[: total - sum(alloc.values())]:
        alloc[c] += 1
    return alloc


def select(tickets: list[dict], quotas: dict = QUOTAS, seed: int = SELECTION_SEED) -> dict:
    """`tickets`: [{"ticket_id", "split", "type", "department"}]. Returns the selection."""
    rng = random.Random(seed)
    pools: dict[str, list] = defaultdict(list)
    for t in tickets:
        pools["train+val" if t["split"] in ("train", "val") else t["split"]].append(t)
    chosen: dict[str, list[str]] = {}
    for pool, quota in quotas.items():
        cells: dict = defaultdict(list)
        for t in pools.get(pool, []):
            cells[(t["type"], t["department"])].append(t["ticket_id"])
        alloc = allocate({c: len(v) for c, v in cells.items()}, quota)
        picked = []
        for cell in sorted(cells):
            picked += rng.sample(sorted(cells[cell]), alloc[cell])
        chosen[pool] = sorted(picked)
    return {"seed": seed, "quotas": quotas, "selected": chosen, "n": sum(len(v) for v in chosen.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out", type=Path, default=ROOT / "data/annotation/selection_v1.json")
    args = parser.parse_args()
    bench = ROOT / "data" / "benchmark"
    assignment = json.loads((bench / f"splits_{args.version}.json").read_text(encoding="utf-8"))["assignment"]
    tickets = [
        {"ticket_id": t["ticket_id"], "split": assignment[t["ticket_id"]], "type": t["type"], "department": t["department"]}
        for t in map(json.loads, filter(None, (bench / f"benchmark_{args.version}.jsonl").read_text(encoding="utf-8").splitlines()))
    ]
    selection = select(tickets) | {"benchmark_version": args.version}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(selection, indent=1) + "\n", encoding="utf-8")
    print({k: len(v) for k, v in selection["selected"].items()}, "->", args.out)


if __name__ == "__main__":
    main()
