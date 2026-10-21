"""Unseen-topic shift experiment and the shift guard (Blueprint V2 RQ3 and H3; Roadmap
Week 9, Shivaganesh).

Thresholds certified on known topics do not hold for topics the knowledge base does not
cover: the Week 8 model let unseen-topic failures into the assisted lane. The gate's
shift guard escalates drafts whose routing looks unlike the calibration data:

    rt_dept_max_prob  < min_dept_prob      the classifier is unsure which department
    rt_probe_margin   < min_probe_margin   another department matches the ticket as well

Protocol (fixed before looking at results):

- The six withheld topics are split at random (seed 2026) into three tuning topics and
  three evaluation topics. The guard is chosen on the tuning topics only and reported on
  the evaluation topics, so it is never measured on what it was tuned on.
- Cost is measured on the validation split (known topics): the share of acceptable drafts
  that the gate would have shown but the guard escalates.
- Choice rule: the guard that blocks the most shown-but-unacceptable unseen drafts on the
  tuning topics, subject to cost <= 10%; ties go to the lower cost.
- Two lanes versus three: the same evaluation with the fast lane merged into assisted.

    python ai/confidence_model/shift.py --labels judge
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from confidence_model.dataset import load  # noqa: E402
from gate.service import Thresholds, guard_reasons, lane_for  # noqa: E402

SEED = 2026
MAX_COST = 0.10
PROB_GRID = (None, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
MARGIN_GRID = (None, -0.10, -0.05, 0.0, 0.05, 0.10)


def split_topics(topics: list[str], seed: int = SEED) -> tuple[list[str], list[str]]:
    ordered = sorted(topics)
    random.Random(seed).shuffle(ordered)
    half = len(ordered) // 2
    return sorted(ordered[:half]), sorted(ordered[half:])


def lanes(rows, scores, thresholds: Thresholds) -> list[str]:
    out = []
    for r, s in zip(rows, scores):
        guarded = bool(guard_reasons(r.features, thresholds))
        out.append(lane_for(float(s), bool(r.can_answer), thresholds, guarded))
    return out


def outcome(rows, scores, thresholds: Thresholds, base: Thresholds) -> dict:
    """Effect of `thresholds` (with guard) against `base` (same thresholds, no guard)."""
    with_guard, without = lanes(rows, scores, thresholds), lanes(rows, scores, base)
    y = np.array([r.acceptable for r in rows])
    shown_before = np.array([lane != "escalate" for lane in without])
    shown_after = np.array([lane != "escalate" for lane in with_guard])
    bad_shown = shown_before & (y == 0)
    good_shown = shown_before & (y == 1)
    return {
        "n": len(rows),
        "shown_without_guard": int(shown_before.sum()),
        "shown_with_guard": int(shown_after.sum()),
        "unacceptable_shown_without_guard": int(bad_shown.sum()),
        "unacceptable_shown_with_guard": int((shown_after & (y == 0)).sum()),
        "unacceptable_blocked_share": round(float((bad_shown & ~shown_after).sum() / bad_shown.sum()), 4)
        if bad_shown.sum() else None,
        "acceptable_blocked_share": round(float((good_shown & ~shown_after).sum() / good_shown.sum()), 4)
        if good_shown.sum() else None,
        "risk_shown_without_guard": round(float(1 - y[shown_before].mean()), 4) if shown_before.sum() else None,
        "risk_shown_with_guard": round(float(1 - y[shown_after].mean()), 4) if shown_after.sum() else None,
    }


def choose_guard(tune_rows, tune_scores, val_rows, val_scores, base: Thresholds) -> tuple[dict, list[dict]]:
    trials = []
    for prob, margin in itertools.product(PROB_GRID, MARGIN_GRID):
        t = Thresholds(base.version, base.fast, base.assisted, prob, margin)
        tune = outcome(tune_rows, tune_scores, t, base)
        cost = outcome(val_rows, val_scores, t, base)["acceptable_blocked_share"] or 0.0
        trials.append({"min_dept_prob": prob, "min_probe_margin": margin,
                       "tune_unacceptable_blocked": tune["unacceptable_blocked_share"] or 0.0, "val_cost": cost})
    feasible = [t for t in trials if t["val_cost"] <= MAX_COST]
    best = max(feasible, key=lambda t: (t["tune_unacceptable_blocked"], -t["val_cost"]))
    return best, trials


def main() -> None:
    import joblib

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", choices=["judge", "human"], default="judge")
    args = parser.parse_args()

    bundle = joblib.load(ROOT / "ai" / "confidence_model" / "artifacts" / f"confidence-v1-{args.labels}.joblib")
    model, th = bundle["model"], bundle["thresholds"]
    base = Thresholds(f"{args.labels}-calib", th["fast"]["threshold"], th["assisted"]["threshold"])

    rows = [r for r in asyncio.run(load("v1", args.labels)) if r.acceptable is not None]
    val = [r for r in rows if r.split == "val"]
    unseen = [r for r in rows if r.split == "unseen"]
    tune_topics, eval_topics = split_topics(sorted({r.topic for r in unseen}))
    tune = [r for r in unseen if r.topic in tune_topics]
    held = [r for r in unseen if r.topic in eval_topics]
    scores = {id(r): s for r, s in zip(val + unseen, model.predict(val + unseen))}

    def sc(part):
        return [scores[id(r)] for r in part]

    best, trials = choose_guard(tune, sc(tune), val, sc(val), base)
    guard = Thresholds(base.version, base.fast, base.assisted, best["min_dept_prob"], best["min_probe_margin"])
    two_lane = Thresholds(base.version, None, base.assisted if base.fast is None else min(base.fast, base.assisted),
                          best["min_dept_prob"], best["min_probe_margin"])
    report = {
        "labels": args.labels,
        "status": "PROVISIONAL (LLM-judge labels)" if args.labels == "judge" else "human labels",
        "thresholds": {"fast": base.fast, "assisted": base.assisted},
        "tuning_topics": tune_topics,
        "evaluation_topics": eval_topics,
        "rule": f"max unacceptable blocked on tuning topics s.t. validation cost <= {MAX_COST:.0%}",
        "guard": {"min_dept_prob": best["min_dept_prob"], "min_probe_margin": best["min_probe_margin"]},
        "tuning": outcome(tune, sc(tune), guard, base),
        "evaluation_unseen": outcome(held, sc(held), guard, base),
        "validation_known_topics": outcome(val, sc(val), guard, base),
        "two_lanes_vs_three": {
            "three_lane_shown_val": outcome(val, sc(val), guard, base)["shown_with_guard"],
            "two_lane_shown_val": outcome(val, sc(val), two_lane, base)["shown_with_guard"],
            "note": "identical while no fast-lane threshold is certified" if base.fast is None else "",
        },
        "grid": trials,
    }
    out = ROOT / "docs" / "results" / f"shift-v1-{args.labels}.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("tuning topics:", tune_topics, "| evaluation topics:", eval_topics)
    print("chosen guard:", report["guard"])
    for k in ("tuning", "evaluation_unseen", "validation_known_topics"):
        o = report[k]
        print(f"{k:<24} shown {o['shown_without_guard']:>3} -> {o['shown_with_guard']:>3}  "
              f"bad shown {o['unacceptable_shown_without_guard']:>3} -> {o['unacceptable_shown_with_guard']:>3}  "
              f"good blocked {o['acceptable_blocked_share']}")
    print("->", out)


if __name__ == "__main__":
    main()
