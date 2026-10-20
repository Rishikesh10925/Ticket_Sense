"""Feature-group ablations (Blueprint V2 §14: "Ablations remove one feature group at a
time ... and report the change in AURC. A further ablation drops the cross-department
probe"; Roadmap Week 8, Shivaganesh).

    python ai/confidence_model/ablate.py --labels judge

Each ablation refits the chosen model type with the full model's hyperparameters on the
train split, minus one group's features, and is scored on validation. The change in
AURC (ablated minus full; positive = the group helped) comes with a paired, group-aware
bootstrap interval over the same resampled scenarios. Ranking only: calibration does
not change AURC, so it is skipped here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from confidence_model.dataset import load  # noqa: E402
from confidence_model.model import FEATURES, CategoryHistory, make_estimator, matrix  # noqa: E402
from evaluation.bootstrap import paired_bootstrap_diff  # noqa: E402
from evaluation.metrics import aurc  # noqa: E402

GROUPS = {
    "retrieval": "ret_",
    "reranker": "rr_",
    "grounding": "gr_",
    "consistency": "cs_",
    "routing": "rt_",
    "evidence quality": "ev_",
    "ticket": "tk_",
    "category history": "cat_",
}
EXTRA = {"cross-department probe": ("rt_probe_top1", "rt_probe_margin")}


def columns_without(names: set[str]) -> list[int]:
    return [i for i, f in enumerate(FEATURES) if f not in names]


def fit_score(kind: str, params: dict, train, val, keep: list[int]) -> np.ndarray:
    history = CategoryHistory.fit(train)
    y = np.array([r.acceptable for r in train], dtype=float)
    est = make_estimator(kind, params).fit(matrix(train, history)[:, keep], y)
    return est.predict_proba(matrix(val, history)[:, keep])[:, 1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", choices=["judge", "human"], default="judge")
    parser.add_argument("--n-boot", type=int, default=1000)
    args = parser.parse_args()

    report_path = ROOT / "docs" / "results" / f"confidence-v1-{args.labels}.json"
    chosen = json.loads(report_path.read_text(encoding="utf-8"))
    kind = chosen["chosen"]
    params = chosen["candidates"][kind]["chosen_params"]

    rows = [r for r in asyncio.run(load("v1", args.labels)) if r.acceptable is not None]
    train = [r for r in rows if r.split == "train"]
    val = [r for r in rows if r.split == "val"]
    y = np.array([r.acceptable for r in val], dtype=float)
    groups = [r.group_id for r in val]

    full = fit_score(kind, params, train, val, list(range(len(FEATURES))))
    out = {"labels": args.labels, "model": kind, "params": params, "full_val_aurc": round(aurc(full, y), 4),
           "status": "PROVISIONAL (LLM-judge labels)" if args.labels == "judge" else "human labels",
           "ablations": []}
    plans = [(name, {f for f in FEATURES if f.startswith(prefix)}) for name, prefix in GROUPS.items()]
    plans += [(name, set(cols)) for name, cols in EXTRA.items()]
    for name, drop in plans:
        ablated = fit_score(kind, params, train, val, columns_without(drop))
        ci = paired_bootstrap_diff(aurc, ablated, full, y, groups=groups, n_resamples=args.n_boot, seed=2026)
        out["ablations"].append({
            "dropped": name, "n_features": len(drop), "val_aurc": round(aurc(ablated, y), 4),
            "delta_aurc": round(ci.estimate, 4), "delta_ci95": [round(ci.low, 4), round(ci.high, 4)],
            "helps": bool(ci.low > 0), "hurts": bool(ci.high < 0),
        })
        a = out["ablations"][-1]
        print(f"- {name:<24} AURC {a['val_aurc']:.4f}  delta {a['delta_aurc']:+.4f} "
              f"[{a['delta_ci95'][0]:+.4f}, {a['delta_ci95'][1]:+.4f}]")
    dest = ROOT / "docs" / "results" / f"ablations-v1-{args.labels}.json"
    dest.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"full model val AURC {out['full_val_aurc']} -> {dest}")


if __name__ == "__main__":
    main()
