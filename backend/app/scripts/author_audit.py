"""Three-author audit (rubric AUTHOR-v2): freeze, build each author's pages, collect the
Excel files (docs/author-audit/README.md). Logic is in ai/evaluation/author_audit.py.

    python -m app.scripts.author_audit freeze
    python -m app.scripts.author_audit export --batch 1      # then --batch 2
    python -m app.scripts.author_audit collect ../data/annotation/returned/author_v2/*.xlsx

The sample is the frozen human-audit sample (seed 20261102): a new disjoint sample cannot
fill even N = 20 (no C2 and 2 B scenarios are left). The 80 outside ratings of it stay a
separate pilot and are never shown to the authors. Practice cases come from the training
split; the sealed test split is never read.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import random
import shutil
import sys
from pathlib import Path

from app.scripts import human_audit as ha

sys.path.insert(0, str(ha.ROOT / "ai"))
from evaluation.author_audit import RUBRIC, analyse, check_rating  # noqa: E402
from evaluation.human_audit import NLI_PASS, read_xlsx  # noqa: E402

OUT = ha.ROOT / "data" / "annotation" / "packs" / "author_v2"
RETURNED = ha.ROOT / "data" / "annotation" / "returned" / "author_v2"
MANIFEST = OUT / "manifest_hidden.json"
PLAN = ha.ROOT / "docs" / "author-audit" / "plan_author_v2.json"
TEMPLATE = Path(__file__).with_name("author_audit_template.html")
AUTHORS = {"AUTH-R": "Rishikesh", "AUTH-A": "Aashritha", "AUTH-S": "Shivaganesh"}
SEED = 20261103
# Practice kinds the protocol asks for, picked from stored values on training drafts.
PRACTICE = {
    "irrelevant_but_well_cited": lambda s, j: bool(s) and min(s) >= NLI_PASS and j == "W",
    "relevant_partly_unsupported": lambda s, j: bool(s) and min(s) < NLI_PASS <= max(s) and j == "R",
    "correct_and_supported": lambda s, j: bool(s) and min(s) >= NLI_PASS and j in ("A", "M"),  # judge accepted
}
PER_KIND = 2


def freeze() -> dict:
    if MANIFEST.exists():
        raise SystemExit(f"{MANIFEST.relative_to(ha.ROOT)} exists: the author audit is frozen.")
    base = json.loads(ha.MANIFEST.read_text(encoding="utf-8"))
    pairs = json.loads((ha.OUT / "assignment_hidden.json").read_text(encoding="utf-8"))
    batch1 = sorted(d for d, p in pairs.items() if p == ["HA-01", "HA-02"])  # a balanced half (split_into_pairs)
    rng = random.Random(SEED)
    train = [d for d in asyncio.run(ha.load(("train",))) if d["eligible"]]
    taken: set[str] = set()
    practice = []
    for kind, rule in PRACTICE.items():
        pool = sorted((d for d in train if rule([c["support"] for c in d["claims"]], d["judge"]) and d["group_id"] not in taken),
                      key=lambda d: d["draft_id"])
        for d in rng.sample(pool, PER_KIND):
            taken.add(d["group_id"])
            practice.append({"draft_id": d["draft_id"], "kind": kind})
    manifest = {
        "protocol": "Three-Author Human Annotation Protocol, AUTHOR-v2, 3 November 2026", "rubric": RUBRIC,
        "sample": "human_audit_v1 (mode H, N = 40, seed 20261102), reused: a disjoint sample is infeasible",
        "seed": SEED, "authors": AUTHORS, "eligible_scenarios": base["available_scenarios"],
        "batches": {"1": batch1, "2": sorted(c["draft_id"] for c in base["cases"] if c["draft_id"] not in batch1)},
        "cases": base["cases"], "practice": practice,
        "exposure": {"external_pilot": "all 40 cases were rated by outside reviewers in two pilot rounds (80 ratings); "
                                       "those ratings are not shown to authors and are not pooled",
                     "AUTH-R": "ran the selection and the pilot, and saw pilot agreement summaries; per-case exposure is "
                               "declared on each page",
                     "AUTH-A": "declared per case on each page", "AUTH-S": "declared per case on each page"},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    with (OUT / "01_sampling_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draft_id", "group_id", "split", "type", "department", "part", "group", "batch", "drafts_in_scenario",
                    "nli_pass_suspected_error", "judge_disagreement", "nli_rejected", "seed"])
        for c in base["cases"]:
            batch = "1" if c["draft_id"] in batch1 else "2"
            w.writerow([c["draft_id"], c["group_id"], c["split"], c["type"], c["department"], c["part"], c["group"], batch,
                        c["drafts_in_scenario"], *(c["flags"][k] for k in ("nli_pass_suspected_error", "judge_disagreement", "nli_rejected")),
                        base["seed"]])
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps({k: v for k, v in manifest.items() if k not in ("cases", "batches", "practice")}
                               | {"cases": len(base["cases"]), "batch_sizes": {k: len(v) for k, v in manifest["batches"].items()},
                                  "practice_kinds": {k: PER_KIND for k in PRACTICE},
                                  "manifest_sha256": ha.sha256(MANIFEST), "sample_manifest_sha256": ha.sha256(ha.MANIFEST)},
                               indent=1) + "\n", encoding="utf-8")
    return manifest


def build(code: str, batch: str, items: list[dict], practice: list[dict]) -> Path:
    def show(d: dict) -> dict:
        return {"id": d["draft_id"], **d["packet"]}

    shuffled = sorted(items, key=lambda d: d["draft_id"])
    random.Random(f"{SEED}-{code}-{batch}").shuffle(shuffled)
    practice = sorted(practice, key=lambda d: d["draft_id"])
    pack = {"pack_id": f"{code}-{batch}-{SEED}", "reviewer": code, "author_name": AUTHORS[code], "rubric": RUBRIC,
            "batch": f"batch{batch}", "batch_label": f"batch {batch} of 2",
            "practice": [show(d) for d in practice], "items": [show(d) for d in shuffled]}
    html = TEMPLATE.read_text(encoding="utf-8").replace("__PACK__", json.dumps(pack, ensure_ascii=False).replace("</", "<\\/"))
    path = OUT / f"Author_Audit_{AUTHORS[code]}_batch{batch}.html"
    path.write_text(html, encoding="utf-8")
    return path


def export(batch: str) -> list[Path]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids = manifest["batches"][batch]
    practice_ids = [p["draft_id"] for p in manifest["practice"]] if batch == "1" else []
    packets = asyncio.run(ha._packets(set(ids) | set(practice_ids)))
    return [build(code, batch, [packets[i] for i in ids], [packets[i] for i in practice_ids]) for code in AUTHORS]


def collect(files: list[Path]) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    known = {c["draft_id"] for c in manifest["cases"]}
    RETURNED.mkdir(parents=True, exist_ok=True)
    ratings: dict[str, dict[str, dict]] = {code: {} for code in AUTHORS}
    problems = []
    for f in files:
        rows = read_xlsx(f).get("Ratings", [])
        if not rows or rows[0].get("rubric") != RUBRIC:
            problems.append(f"{f.name}: not an {RUBRIC} author file")
            continue
        if f.resolve().parent != RETURNED.resolve():
            shutil.copy2(f, RETURNED / f.name)  # the original export, kept as it arrived
        code = rows[0]["author"]
        if not all(r["locked_at"] for r in rows):
            problems.append(f"{f.name}: not the final (locked) file")
        for r in rows:
            if r["draft_id"] not in known:
                problems.append(f"{f.name}: case {r['case']} is not in the sample")
            elif r["finished"] == "yes":
                bad = check_rating(r)
                problems += [f"{f.name}: case {r['case']}: {b}" for b in bad]
                if not bad:
                    ratings[code][r["draft_id"]] = r
    rated = set().union(*(set(r) for r in ratings.values()))
    cases = [c for c in manifest["cases"] if c["draft_id"] in rated]  # the batches collected so far
    for code, mine in ratings.items():
        if missing := len(cases) - len(mine):
            problems.append(f"{code} ({AUTHORS[code]}): {missing} of {len(cases)} cases have no finished rating")
    report = analyse(cases, ratings, manifest["eligible_scenarios"], SEED) | {"problems": problems}
    (OUT / "04_agreement_report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    with (OUT / "05_adjudication_log.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draft_id", "question", *[f"{c}_{q}" for c in AUTHORS for q in ("answer", "reason")],
                    "references_consulted", "adjudicated_label", "rationale", "status"])
        for q in ("q1", "q2", "q3"):  # q1 covers the binary disagreements too
            for i in report["disagreements"][q]:
                w.writerow([i, q, *[x for c in AUTHORS for x in (ratings[c][i][q], ratings[c][i]["reason"])], "", "", "", "open"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    sub.add_parser("export").add_argument("--batch", choices=["1", "2"], required=True)
    sub.add_parser("collect").add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    if args.cmd == "freeze":
        m = freeze()
        print(json.dumps({"cases": len(m["cases"]), "batches": {k: len(v) for k, v in m["batches"].items()}, "practice": m["practice"]}, indent=1))
    elif args.cmd == "export":
        for p in export(args.batch):
            print(p.relative_to(ha.ROOT))
    else:
        r = collect(args.files)
        print(json.dumps({k: r[k] for k in ("selected", "complete", "agreement", "problems")}, indent=1))


if __name__ == "__main__":
    main()
