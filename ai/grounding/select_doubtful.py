"""Reduced human audit: label the doubtful claims, plus a random check of the rest
(Roadmap Week 6; replaces "every claim of 100 drafts" to cut human effort).

Two automatic checkers judge every audit claim: NLI (`ai/grounding/claims.py`) and the
LLM check (`ai/grounding/llm_check.py`). A human then labels:

- every claim where the two checkers disagree (the doubtful ones), and
- a random sample of claims where they agree, per member.

The random part is not optional. Without it the audit could not estimate how often
both checkers are wrong together, and accuracy on "easy" claims would be assumed rather
than measured. Each row keeps its stratum and inclusion probability in a separate key
file, so the analysis can weight it back to the full 495 claims; the worksheet itself
shows neither, so the auditor is not told which rows are "doubtful".

    python ai/grounding/select_doubtful.py --agree-per-member 15
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMBERS = ("R", "A", "S")
SEED = 2026


def select(claims: list[dict], agree_per_member: int, seed: int = SEED) -> dict[str, list[dict]]:
    """`claims`: rows of llm-groundedness-v1.json (+ cited passages). Drafts are split
    over members as in the full audit (draft i goes to member i mod 3)."""
    rng = random.Random(seed)
    drafts = list(dict.fromkeys(c["draft_id"] for c in claims))
    owner = {d: MEMBERS[i % len(MEMBERS)] for i, d in enumerate(drafts)}
    out: dict[str, list[dict]] = {m: [] for m in MEMBERS}
    for m in MEMBERS:
        mine = [c for c in claims if owner[c["draft_id"]] == m and c["llm_supported"] is not None]
        disagree = [c for c in mine if (c["nli_support"] >= 0.5) != c["llm_supported"]]
        agree = [c for c in mine if (c["nli_support"] >= 0.5) == c["llm_supported"]]
        sampled = rng.sample(agree, min(agree_per_member, len(agree)))
        p_agree = len(sampled) / len(agree) if agree else 0.0
        rows = [c | {"stratum": "disagree", "p_include": 1.0} for c in disagree]
        rows += [c | {"stratum": "agree", "p_include": round(p_agree, 4)} for c in sampled]
        rng.shuffle(rows)  # the auditor sees no grouping
        out[m] = rows
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--checks", type=Path, default=ROOT / "docs/results/llm-groundedness-v1.json")
    parser.add_argument("--sample", type=Path, default=ROOT / "docs/audit/audit_sample_v1.json")
    parser.add_argument("--agree-per-member", type=int, default=15)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs/audit")
    args = parser.parse_args()

    checks = json.loads(args.checks.read_text(encoding="utf-8"))["claims"]
    sample = json.loads(args.sample.read_text(encoding="utf-8"))
    cited = {(d["draft_id"], c["step"], c["claim"]): c["cited"] for d in sample["drafts"] for c in d["claims"]}
    for c in checks:
        c["cited"] = cited[(c["draft_id"], c["step"], c["claim"])]

    chosen = select(checks, args.agree_per_member)
    key = {}
    for m, rows in chosen.items():
        with (args.out_dir / f"audit_v1_{m}_short.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draft_id", "ticket_id", "step", "claim", "cited_passages", "human", "note"])
            for r in rows:
                passages = "\n---\n".join(f"[{p['n']}] {p['title']}\n{p['text']}" for p in r["cited"]) or "(cites nothing)"
                w.writerow([r["draft_id"], r["ticket_id"], r["step"], r["claim"], passages, "", ""])
        key[m] = [{k: r[k] for k in ("draft_id", "step", "claim", "stratum", "p_include", "nli_support", "llm_supported")}
                  for r in rows]
        print(f"{m}: {len(rows)} claims ({sum(r['stratum'] == 'disagree' for r in rows)} doubtful)")
    (args.out_dir / "audit_v1_short_key.json").write_text(
        json.dumps({"seed": SEED, "agree_per_member": args.agree_per_member, "members": key}, indent=1) + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
