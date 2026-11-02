"""Independent human audit: freeze the sample, build the reviewer pages, collect the Excel
files (docs/human-audit/README.md). Logic is in ai/evaluation/human_audit.py.

    python -m app.scripts.human_audit count
    python -m app.scripts.human_audit select --n 40 --seed 20261102
    python -m app.scripts.human_audit export --reviewers 2
    python -m app.scripts.human_audit collect data/annotation/returned/human_audit_v1/*.xlsx
    python -m app.scripts.human_audit adjudication --reviewer HA-09

Reads only the validation and unseen-topic splits, plus a few training drafts as practice;
the query never touches the sealed test split. Everything a reviewer must not see (type,
split, flags, group, judge and NLI values) stays in manifest_hidden.json, which is
git-ignored until the ratings are in; docs/human-audit/plan_v1.json records its hash.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import shutil
import sys
import uuid
from collections import Counter
from pathlib import Path

from sqlalchemy import select as sql_select

from app.database import SessionLocal
from app.models import BenchmarkTicket, Draft, DraftClaim, JudgeVerdict

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ai"))
from evaluation.human_audit import Q1, analyse, check_rating, read_xlsx, select, split_into_pairs  # noqa: E402

OUT = ROOT / "data" / "annotation" / "packs" / "human_audit_v1"
RETURNED = ROOT / "data" / "annotation" / "returned" / "human_audit_v1"
MANIFEST = OUT / "manifest_hidden.json"
PLAN = ROOT / "docs" / "human-audit" / "plan_v1.json"
BLIND = ROOT / "paper" / "revision" / "blind_c1_verdicts.jsonl"  # the blinded judge's stored verdicts
TEMPLATE = Path(__file__).with_name("human_audit_template.html")
PROMPT = "draft-v2"
MAIN_SPLITS = ("val", "unseen")
PRACTICE_CASES = 3  # frozen in the manifest
PRACTICE_SHOWN = 1  # pages show one, to keep the review short (second round)


async def load(splits: tuple[str, ...]) -> list[dict]:
    """Answering, schema-valid drafts with an evidence packet, from the given splits."""
    if "test" in splits:
        raise ValueError("the sealed test split is never read here")
    async with SessionLocal() as db:
        rows = (await db.execute(
            sql_select(Draft, BenchmarkTicket)
            .join(BenchmarkTicket, (BenchmarkTicket.id == Draft.benchmark_ticket_id)
                  & (BenchmarkTicket.benchmark_version == Draft.benchmark_version))
            .where(BenchmarkTicket.split.in_(splits), Draft.prompt_version == PROMPT, Draft.benchmark_version == "v1")
        )).all()
        ids = [d.id for d, _ in rows]
        claims: dict[uuid.UUID, list[dict]] = {}
        for c in await db.scalars(sql_select(DraftClaim).where(DraftClaim.draft_id.in_(ids))):
            claims.setdefault(c.draft_id, []).append({"support": c.support})
        judge = {v.draft_id: v.label for v in await db.scalars(sql_select(JudgeVerdict).where(JudgeVerdict.draft_id.in_(ids)))}
    out = []
    for d, t in rows:
        out.append({
            "draft_id": str(d.id), "ticket_id": t.id, "group_id": t.group_id, "type": t.type, "split": t.split,
            "department": t.department, "eligible": bool(d.can_answer and d.schema_valid and d.evidence),
            "claims": claims.get(d.id, []), "judge": judge.get(d.id),
            "packet": {"subject": t.subject, "body": t.body, "attachment": t.attachment_text,
                       "steps": [{"text": s.get("text", ""), "citations": s.get("citations", [])} for s in d.steps],
                       "missing": d.missing_information,
                       "evidence": [{"n": e.get("n"), "title": e.get("title"), "text": e.get("text")} for e in d.evidence]},
        })
    return out


def counts(pool: list[dict]) -> dict:
    eligible = [d for d in pool if d["eligible"]]
    return {
        "drafts_read": len(pool),
        "excluded_not_answering_or_no_evidence": len(pool) - len(eligible),
        "eligible_drafts": len(eligible),
        "eligible_scenarios": len({d["group_id"] for d in eligible}),
        "by_split_type": {f"{s}/{t}": {"drafts": c, "scenarios": len({d["group_id"] for d in eligible if (d["split"], d["type"]) == (s, t)})}
                          for (s, t), c in sorted(Counter((d["split"], d["type"]) for d in eligible).items())},
    }


def blind_verdicts() -> dict[str, str]:
    return {r["draft_id"]: r["label"] for r in map(json.loads, BLIND.read_text(encoding="utf-8").splitlines())}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(n: int, seed: int) -> dict:
    if MANIFEST.exists():
        raise SystemExit(f"{MANIFEST.relative_to(ROOT)} exists: the sample is frozen. A new cohort needs its own protocol.")
    pool = asyncio.run(load(MAIN_SPLITS))
    eligible = [{k: v for k, v in d.items() if k != "packet"} for d in pool if d["eligible"]]
    chosen = select(eligible, blind_verdicts(), n, seed)
    rng = random.Random(seed + 1)
    train = [d for d in asyncio.run(load(("train",))) if d["eligible"]]
    practice = rng.sample(sorted(train, key=lambda d: d["draft_id"]), PRACTICE_CASES)
    per_scenario = Counter(d["group_id"] for d in eligible)
    manifest = {
        "protocol": "Independent Human Annotation Sampling Protocol, 31 October 2026", "mode": "H", "n": n, "seed": seed,
        "nli_pass": 0.5, "prompt_version": PROMPT, "counts": counts(pool),
        "available_scenarios": chosen["available_scenarios"], "random_quota": chosen["random_quota"],
        "targeted_quota": dict(zip(("nli_pass_suspected_error", "judge_disagreement", "other_controls"), chosen["targeted_quota"])),
        "cases": [{**c, "drafts_in_scenario": per_scenario[c["group_id"]]} for c in chosen["cases"]],
        "practice": [d["draft_id"] for d in practice],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps({k: v for k, v in manifest.items() if k not in ("cases", "practice")}
                               | {"selected_cases": len(manifest["cases"]), "manifest_sha256": sha256(MANIFEST),
                                  "blind_verdicts_sha256": sha256(BLIND)}, indent=1) + "\n", encoding="utf-8")
    return manifest


def build_pack(reviewer: str, items: list[dict], practice: list[dict], seed: int) -> Path:
    def show(d: dict) -> dict:
        return {"id": d["draft_id"], **d["packet"]}

    shuffled = sorted(items, key=lambda d: d["draft_id"])
    random.Random(f"{seed}-{reviewer}").shuffle(shuffled)
    pack = {"pack_id": uuid.uuid4().hex[:8], "reviewer": reviewer,
            "practice": [show(d) for d in practice], "items": [show(d) for d in shuffled]}
    html = TEMPLATE.read_text(encoding="utf-8").replace("__PACK__", json.dumps(pack, ensure_ascii=False).replace("</", "<\\/"))
    path = OUT / f"AI_Reply_Review_{reviewer}.html"
    path.write_text(html, encoding="utf-8")
    return path


async def _packets(ids: set[str]) -> dict[str, dict]:
    pool = await load(MAIN_SPLITS + ("train",))
    return {d["draft_id"]: d for d in pool if d["draft_id"] in ids}


def export(reviewers: int) -> list[Path]:
    if reviewers < 2 or reviewers % 2:
        raise SystemExit("--reviewers must be even: each case needs two different reviewers")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    packets = asyncio.run(_packets({c["draft_id"] for c in manifest["cases"]} | set(manifest["practice"])))
    practice = [packets[i] for i in manifest["practice"][:PRACTICE_SHOWN]]
    written, assignment = [], {}
    for p, cases in enumerate(split_into_pairs(manifest["cases"], reviewers // 2, manifest["seed"])):
        pair = [f"HA-{2 * p + 1:02d}", f"HA-{2 * p + 2:02d}"]
        for reviewer in pair:
            written.append(build_pack(reviewer, [packets[c["draft_id"]] for c in cases], practice, manifest["seed"]))
        assignment |= {c["draft_id"]: pair for c in cases}
    (OUT / "assignment_hidden.json").write_text(json.dumps(assignment, indent=1) + "\n", encoding="utf-8")
    return written


def _read(path: Path, known: set[str]) -> tuple[str, dict[str, dict], list[str]]:
    rows = read_xlsx(path).get("Ratings", [])
    problems, finished = [], {}
    if not rows:
        return "", {}, [f"{path.name}: no Ratings sheet"]
    reviewer = rows[0]["reviewer"]
    for r in rows:
        if r["draft_id"] not in known:
            problems.append(f"{path.name}: case {r['case']} is not in this sample")
        elif r["finished"] == "yes":
            bad = check_rating(r)
            problems += [f"{path.name}: case {r['case']}: {b}" for b in bad]
            if not bad:
                finished[r["draft_id"]] = r
    pasted = sum(r.get("pasted") == "yes" for r in rows)
    if pasted:
        problems.append(f"{path.name}: {pasted} reasons were pasted, not typed: check they are the reviewer's own")
    return reviewer, finished, problems


def collect(files: list[Path]) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pairs = json.loads((OUT / "assignment_hidden.json").read_text(encoding="utf-8"))
    known = {c["draft_id"] for c in manifest["cases"]}
    RETURNED.mkdir(parents=True, exist_ok=True)
    ratings, third, problems = {}, {}, []
    for f in files:
        reviewer, finished, bad = _read(f, known)
        problems += bad
        if not reviewer:
            continue
        if f.resolve().parent != RETURNED.resolve():
            shutil.copy2(f, RETURNED / f.name)  # the raw file is kept as it arrived
        if any(reviewer in p for p in pairs.values()):
            ratings[reviewer] = finished
        else:
            third |= finished
    for reviewer in {r for p in pairs.values() for r in p} - set(ratings):
        problems.append(f"no file yet from {reviewer}")
        ratings[reviewer] = {}
    report = analyse(manifest["cases"], ratings, pairs, manifest["available_scenarios"], third)
    report["problems"] = problems
    report["q1_categories"] = list(Q1)
    (OUT / "collect_report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report


def adjudication(reviewer: str) -> Path:
    """A blinded pack for a third reviewer: the cases the two reviewers split on acceptable."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report = json.loads((OUT / "collect_report.json").read_text(encoding="utf-8"))
    ids = set(report["disputed_binary"])
    if not ids:
        raise SystemExit("no disputed cases")
    packets = asyncio.run(_packets(ids))
    return build_pack(reviewer, list(packets.values()), [], manifest["seed"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("count")
    s = sub.add_parser("select")
    s.add_argument("--n", type=int, required=True)
    s.add_argument("--seed", type=int, required=True)
    sub.add_parser("export").add_argument("--reviewers", type=int, default=2)
    sub.add_parser("collect").add_argument("files", nargs="+", type=Path)
    sub.add_parser("adjudication").add_argument("--reviewer", required=True)
    args = parser.parse_args()
    if args.cmd == "count":
        print(json.dumps(counts(asyncio.run(load(MAIN_SPLITS))), indent=1))
    elif args.cmd == "select":
        m = freeze(args.n, args.seed)
        print(json.dumps({k: m[k] for k in ("n", "seed", "available_scenarios", "random_quota", "targeted_quota")}, indent=1))
        print(Counter(c["group"] for c in m["cases"]))
    elif args.cmd == "export":
        for p in export(args.reviewers):
            print(p.relative_to(ROOT))
    elif args.cmd == "collect":
        print(json.dumps(collect(args.files), indent=1))
    else:
        print(adjudication(args.reviewer).relative_to(ROOT))


if __name__ == "__main__":
    main()
