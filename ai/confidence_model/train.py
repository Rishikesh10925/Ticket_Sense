"""Train, select, calibrate and evaluate the confidence model, then prototype the
risk-controlled lane thresholds (Roadmap Week 8; Blueprint V2 §13.3 to §13.4).

    python ai/confidence_model/train.py --labels judge     # development (provisional)
    python ai/confidence_model/train.py --labels human     # the real model, once labelled

Train split: fit and group-aware cross-validation. Validation split: choose between
logistic regression and XGBoost (AURC), compare with the best baseline. Calibration
split: Platt calibration (model.py: isotonic was tried and rejected for its ties), then
Learn-then-Test thresholds for the fast (alpha 0.10) and assisted (alpha 0.40) lanes with
delta 0.10, certified on the calibration drafts that can answer: a draft that says it
cannot answer always escalates, so it is never in the population a lane shows (Week 12).
The locked test split is never read.

With judge labels everything is marked PROVISIONAL: it proves the pipeline and gives
development numbers, never a result.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from confidence_model.dataset import load  # noqa: E402
from confidence_model.model import FEATURES, MODEL_VERSION, fit  # noqa: E402
from evaluation.metrics import (aurc, auroc_unacceptable, brier_score, excess_aurc,  # noqa: E402
                                expected_calibration_error, reliability_bins)
from evaluation.risk_control import DEFAULT_GRID, learn_then_test, select_lane_thresholds  # noqa: E402

ARTIFACT_DIR = ROOT / "ai" / "confidence_model" / "artifacts"


def metrics(p: np.ndarray, y: np.ndarray) -> dict:
    return {"aurc": round(aurc(p, y), 4), "e_aurc": round(excess_aurc(p, y), 4),
            "auroc_unacceptable": round(auroc_unacceptable(p, y), 4),
            "ece": round(expected_calibration_error(p, y), 4), "brier": round(brier_score(p, y), 4)}


def lane_report(lanes, p: np.ndarray, y: np.ndarray, can_answer: list) -> dict:
    assigned = [lanes.lane(float(s), bool(c) if c is not None else False) for s, c in zip(p, can_answer)]
    out = {}
    for lane in ("fast", "assisted", "escalate"):
        idx = [i for i, a in enumerate(assigned) if a == lane]
        out[lane] = {"share": round(len(idx) / len(p), 4),
                     "unacceptable_rate": round(float(1 - y[idx].mean()), 4) if idx else None, "n": len(idx)}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", choices=["judge", "human"], default="judge")
    args = parser.parse_args()

    rows = [r for r in asyncio.run(load("v1", args.labels)) if r.acceptable is not None]
    by = {s: [r for r in rows if r.split == s] for s in ("train", "val", "calib", "unseen")}
    if len(by["train"]) < 50 or len(by["val"]) < 20 or len(by["calib"]) < 50:
        raise SystemExit(f"not enough {args.labels}-labelled rows: { {k: len(v) for k, v in by.items()} }")
    y = {s: np.array([r.acceptable for r in v], dtype=float) for s, v in by.items()}

    candidates, report = {}, {"labels": args.labels, "model_version": MODEL_VERSION, "features": FEATURES,
                              "status": "PROVISIONAL (LLM-judge labels)" if args.labels == "judge" else "human labels",
                              "n": {k: len(v) for k, v in by.items()}, "candidates": {}}
    for kind in ("logreg", "xgboost"):
        model, trials = fit(kind, by["train"], args.labels)
        candidates[kind] = model
        report["candidates"][kind] = {"chosen_params": model.params, "cv": trials,
                                      "val_uncalibrated": metrics(model.raw(by["val"]), y["val"])}
        print(f"{kind}: params {model.params}  val AURC {report['candidates'][kind]['val_uncalibrated']['aurc']}")

    chosen = min(candidates, key=lambda k: report["candidates"][k]["val_uncalibrated"]["aurc"])
    model = candidates[chosen].calibrate(by["calib"])
    p_val = model.predict(by["val"])
    report["chosen"] = chosen
    report["val"] = metrics(p_val, y["val"])
    rel = reliability_bins(p_val, y["val"])
    report["val_reliability"] = {
        name: [None if np.isnan(v) else round(float(v), 4) for v in np.asarray(getattr(rel, name), dtype=float)]
        for name in ("bin_edges", "mean_confidence", "accuracy", "counts")
    }

    p_cal = model.predict(by["calib"])
    answering = np.array([bool(r.can_answer) for r in by["calib"]])
    report["n_calib_answering"] = int(answering.sum())
    lanes = select_lane_thresholds(p_cal[answering], y["calib"][answering], alpha_fast=0.10, alpha_assisted=0.40,
                                   delta=0.10, candidates=DEFAULT_GRID)
    report["thresholds"] = {name: {"threshold": t.threshold, "n_shown": t.n_shown, "n_unacceptable": t.n_unacceptable,
                                   "coverage": round(t.coverage, 4)}
                            for name, t in (("fast", lanes.fast), ("assisted", lanes.assisted))}
    # Admin screen (§13.4): the certified coverage for any chosen error budget.
    report["alpha_curve"] = []
    for a in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50):
        t = learn_then_test(p_cal[answering], y["calib"][answering], alpha=a, delta=0.10, candidates=DEFAULT_GRID)
        report["alpha_curve"].append({"alpha": a, "threshold": t.threshold, "coverage": round(t.coverage, 4)})
    for split in ("val", "unseen"):
        p = model.predict(by[split])
        report[f"lanes_{split}"] = lane_report(lanes, p, y[split], [r.can_answer for r in by[split]])
    report["example_reasons"] = [{"ticket_id": r.ticket_id, "score": round(float(s), 3), "reasons": reasons}
                                 for r, s, reasons in zip(by["val"][:5], p_val[:5], model.top_reasons(by["val"][:5]))]

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = ARTIFACT_DIR / f"{MODEL_VERSION}-{args.labels}.joblib"
    joblib.dump({"model": model, "thresholds": report["thresholds"], "labels": args.labels}, artifact)
    out = ROOT / "docs" / "results" / f"{MODEL_VERSION}-{args.labels}.json"
    out.write_text(json.dumps(report, indent=1, default=float) + "\n", encoding="utf-8")
    print(f"chosen {chosen}; val {report['val']}")
    print(f"thresholds {report['thresholds']}")
    print(f"val lanes {report['lanes_val']}")
    print(f"unseen lanes {report['lanes_unseen']}")
    print("->", out, "and", artifact.name)


if __name__ == "__main__":
    main()
