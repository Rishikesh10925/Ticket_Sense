"""Baselines B0 to B7 on the validation and unseen-topic splits (Blueprint V2 §14;
Roadmap Weeks 6 to 8, Shivaganesh).

    python ai/signals/report_baselines.py --labels judge

Each baseline ranks drafts by one confidence number; AURC, excess AURC and AUROC (for
catching unacceptable drafts) come with group-aware bootstrap intervals (resampling
scenarios, not tickets). B7 is fitted on the train split only. The locked test split
is never read.

With `--labels judge` the target is the LLM judge's verdict, so these are
**provisional development numbers**: they show the pipeline works and how the signals
behave, and are never reported as results. The same command with `--labels human`
produces the reportable table once reviewers have labelled the selected drafts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from evaluation.bootstrap import bootstrap_ci  # noqa: E402
from evaluation.metrics import aurc, auroc_unacceptable, excess_aurc, risk_coverage_curve  # noqa: E402

CHEAP = ("ret_top1_dense", "rr_top1", "gr_supported_share")  # B4, B5, B6


def baseline_scores(rows) -> dict[str, np.ndarray]:
    """Higher = more confident. A missing signal scores 0 (nothing to trust)."""
    def col(get):
        return np.array([0.0 if (v := get(r)) is None or (isinstance(v, float) and math.isnan(v)) else float(v)
                         for r in rows])

    return {
        "B0 always show": np.ones(len(rows)),
        "B1 verbalised": col(lambda r: r.extra.get("b1_verbalised")),
        "B2 token probability": col(lambda r: r.extra.get("b2_mean_prob")),
        "B4 top-1 similarity": col(lambda r: r.features.get("ret_top1_dense")),
        "B5 reranker": col(lambda r: r.features.get("rr_top1")),
        "B6 entailment share": col(lambda r: r.features.get("gr_supported_share")),
    }


def fit_b7(train) -> object:
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    x = np.array([[r.features.get(k) or 0.0 for k in CHEAP] for r in train])
    y = np.array([r.acceptable for r in train])
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(x, y)


def table(scores: dict, acceptable: np.ndarray, groups: list[str], n_boot: int) -> dict:
    out = {}
    for name, conf in scores.items():
        ci = bootstrap_ci(aurc, conf, acceptable, groups=groups, n_resamples=n_boot, seed=2026)
        rc = risk_coverage_curve(conf, acceptable)
        out[name] = {
            "aurc": round(aurc(conf, acceptable), 4),
            "aurc_ci95": [round(ci.low, 4), round(ci.high, 4)],
            "e_aurc": round(excess_aurc(conf, acceptable), 4),
            "auroc_unacceptable": round(auroc_unacceptable(conf, acceptable), 4),
            "curve": {"coverage": [round(float(c), 4) for c in rc.coverage[::max(1, len(rc.coverage) // 50)]],
                      "risk": [round(float(r), 4) for r in rc.risk[::max(1, len(rc.risk) // 50)]]},
        }
    return out


def main() -> None:
    from confidence_model.dataset import load

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", choices=["judge", "human"], default="judge")
    parser.add_argument("--n-boot", type=int, default=1000)
    args = parser.parse_args()

    rows = [r for r in asyncio.run(load("v1", args.labels)) if r.acceptable is not None]
    train = [r for r in rows if r.split == "train"]
    b7 = fit_b7(train)
    report = {"labels": args.labels,
              "status": "PROVISIONAL (LLM-judge labels), not a result" if args.labels == "judge" else "human labels",
              "splits": {}}
    for split in ("val", "unseen"):
        part = [r for r in rows if r.split == split]
        if not part:
            continue
        y = np.array([r.acceptable for r in part], dtype=float)
        scores = baseline_scores(part)
        scores["B7 LR on B4+B5+B6"] = b7.predict_proba(
            np.array([[r.features.get(k) or 0.0 for k in CHEAP] for r in part]))[:, 1]
        report["splits"][split] = {
            "n": len(part), "acceptable_share": round(float(y.mean()), 4),
            "baselines": table(scores, y, [r.group_id for r in part], args.n_boot),
        }
        b3 = [r for r in part if r.extra.get("b3_claim_agreement") is not None]
        if len(b3) >= 20 and 0 < sum(r.acceptable for r in b3) < len(b3):
            yb = np.array([r.acceptable for r in b3], dtype=float)
            report["splits"][split]["b3_subset"] = {
                "n": len(b3),
                "baselines": table({"B3 self-consistency": np.array([r.extra["b3_claim_agreement"] for r in b3]),
                                    "B6 on the same drafts": np.array([r.features.get("gr_supported_share") or 0.0
                                                                       for r in b3])},
                                   yb, [r.group_id for r in b3], args.n_boot),
            }
    out = ROOT / "docs" / "results" / f"baselines-v1-{args.labels}.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for split, part in report["splits"].items():
        print(f"== {split} (n={part['n']}, acceptable {part['acceptable_share']:.0%})")
        for name, m in part["baselines"].items():
            print(f"  {name:<22} AURC {m['aurc']:.3f} [{m['aurc_ci95'][0]:.3f}, {m['aurc_ci95'][1]:.3f}]"
                  f"  AUROC {m['auroc_unacceptable']:.3f}")
    print("->", out)


if __name__ == "__main__":
    main()
