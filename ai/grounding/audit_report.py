"""Groundedness audit results: how often each automatic claim checker agrees with the
human auditors (Roadmap Week 6 gate "audit agreement is understood and acceptable";
design in `select_doubtful.py`).

Each member labelled every claim where NLI and the LLM check disagree, plus a random
sample of the claims where they agree. A sampled claim stands for 1 / p_include claims
of its member's stratum, so the rates below are weighted back to all 495 audit claims.
Claims a human marked `unclear` are counted but left out of the rates.

    python ai/grounding/audit_report.py
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NLI_THRESHOLD = 0.5
BANDS = ((0.0, 0.2), (0.2, 0.5), (0.5, 0.8), (0.8, 1.01))
BOOTSTRAP = 2000
SEED = 2026


def load_labels(audit_dir: Path, key: dict) -> list[dict]:
    """Join each member's worksheet to the hidden key (stratum, weight, checker verdicts)."""
    rows = []
    for member, keyed in key["members"].items():
        sheet = audit_dir / f"audit_v1_{member}_short.csv"
        with sheet.open(encoding="utf-8-sig", newline="") as f:
            human = {(r["draft_id"], int(r["step"]), r["claim"]): r["human"].strip() for r in csv.DictReader(f)}
        for k in keyed:
            label = human.get((k["draft_id"], k["step"], k["claim"]), "")
            rows.append(k | {"member": member, "human": label})
    return rows


def _rate(rows: list[dict], hit) -> float | None:
    total = sum(1 / r["p_include"] for r in rows)
    return round(sum(1 / r["p_include"] for r in rows if hit(r)) / total, 4) if total else None


def checker_scores(rows: list[dict], says_supported) -> dict:
    """Weighted accuracy, and the two error rates that matter for the gate: a false
    'supported' lets an ungrounded step through; a false 'not supported' costs coverage."""
    judged = [r for r in rows if r["human"] in ("supported", "not_supported")]
    truly_not = [r for r in judged if r["human"] == "not_supported"]
    truly_yes = [r for r in judged if r["human"] == "supported"]
    return {
        "accuracy": _rate(judged, lambda r: says_supported(r) == (r["human"] == "supported")),
        "false_supported_rate": _rate(truly_not, says_supported),
        "false_unsupported_rate": _rate(truly_yes, lambda r: not says_supported(r)),
    }


def bootstrap_ci(rows: list[dict], metric, n: int = BOOTSTRAP, seed: int = SEED) -> list[float] | None:
    """95% interval, resampling within each member's stratum so the weights stay valid."""
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault((r["member"], r["stratum"]), []).append(r)
    rng = random.Random(seed)
    values = []
    for _ in range(n):
        sample = [rng.choice(g) for g in groups.values() for _ in g]
        v = metric(sample)
        if v is not None:
            values.append(v)
    if not values:
        return None
    values.sort()
    return [values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]]


def report(rows: list[dict]) -> dict:
    labelled = [r for r in rows if r["human"]]
    judged = [r for r in labelled if r["human"] != "unclear"]
    doubtful = [r for r in judged if r["stratum"] == "disagree"]
    agreed = [r for r in judged if r["stratum"] == "agree"]

    def nli(r):
        return r["nli_support"] >= NLI_THRESHOLD

    def llm(r):
        return bool(r["llm_supported"])

    return {
        "claims_in_audit": len(rows),
        "labelled": len(labelled),
        "unclear": len(labelled) - len(judged),
        "per_member": {m: sum(r["member"] == m for r in labelled) for m in sorted({r["member"] for r in rows})},
        "human_supported_rate": _rate(judged, lambda r: r["human"] == "supported"),
        "nli": checker_scores(judged, nli)
        | {f"{k}_ci95": bootstrap_ci(judged, lambda x, k=k: checker_scores(x, nli)[k])
           for k in ("accuracy", "false_supported_rate")},
        "llm_check": checker_scores(judged, llm)
        | {f"{k}_ci95": bootstrap_ci(judged, lambda x, k=k: checker_scores(x, llm)[k])
           for k in ("accuracy", "false_supported_rate")},
        "when_checkers_disagree": {
            "n": len(doubtful),
            "nli_right": sum(nli(r) == (r["human"] == "supported") for r in doubtful),
            "llm_right": sum(llm(r) == (r["human"] == "supported") for r in doubtful),
        },
        "both_wrong_when_they_agree": {
            "n": len(agreed),
            "n_wrong": sum(nli(r) != (r["human"] == "supported") for r in agreed),
            "weighted_rate": _rate(agreed, lambda r: nli(r) != (r["human"] == "supported")),
        },
        "human_supported_by_nli_band": {
            f"{lo:.1f}-{min(hi, 1.0):.1f}": {
                "n": sum(lo <= r["nli_support"] < hi for r in judged),
                "supported_rate": _rate([r for r in judged if lo <= r["nli_support"] < hi],
                                        lambda r: r["human"] == "supported"),
            }
            for lo, hi in BANDS
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audit-dir", type=Path, default=ROOT / "docs/audit")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/results/audit-v1.json")
    args = parser.parse_args()

    key = json.loads((args.audit_dir / "audit_v1_short_key.json").read_text(encoding="utf-8"))
    result = report(load_labels(args.audit_dir, key))
    args.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
