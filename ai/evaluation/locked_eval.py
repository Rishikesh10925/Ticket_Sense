"""Locked-test evaluation: one command, run exactly once (Roadmap Week 10, Shivaganesh;
decision rules in docs/prereg.md).

    python ai/evaluation/locked_eval.py --rehearse
    python ai/evaluation/locked_eval.py --final --confirm "run the locked test once"

`--rehearse` runs the identical code on the validation split with the LLM-judge model.
It never reads the locked test; it exists so the command, tables and figures are proven
before the one real run. Its numbers are development numbers, not results.

`--final` reads the locked test through `dataset.load(include_test=True)` (which logs
the access) and refuses to start unless:

- human labels exist and the human-label model artifact and baseline table were
  produced beforehand by `python ai/evaluation/reproduce.py --labels human`;
- the access log records no earlier final run (the test is evaluated once; any later
  change is a new, separately reported evaluation).

What it reports (all from the pre-registration, nothing chosen after seeing results):

- H1: paired group-aware bootstrap (1,000 resamples) of AURC(proposed) minus AURC(best
  baseline). The best baseline is the lowest *validation* AURC among B1 to B7 in the
  baseline table written before this run. Supported if the 95% interval is below zero.
- H2: 1,000 random group-aware calibration/test resplits of the labelled pool; Learn-
  then-Test (alpha 0.10, delta 0.10) on the calibration side; supported if the test-side
  fast-lane risk is <= alpha in at least 90% of resplits.
- H3: AURC and fast-lane risk with 95% intervals for seen versus unseen topics.
- Secondary: AUROC, ECE, Brier, risk at 50/70/90% coverage, lane shares, the share of
  unacceptable drafts kept out of the fast lane, false escalations, and slices by ticket
  type, department and seen/unseen. All baselines, none dropped.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from evaluation.bootstrap import bootstrap_ci, paired_bootstrap_diff  # noqa: E402
from evaluation.metrics import (aurc, auroc_unacceptable, brier_score, excess_aurc,  # noqa: E402
                                expected_calibration_error, reliability_bins, risk_at_coverage,
                                risk_coverage_curve)
from evaluation.risk_control import DEFAULT_GRID, learn_then_test  # noqa: E402

ALPHA, DELTA = 0.10, 0.10
N_BOOT, N_RESPLITS, SEED = 1000, 1000, 2026
H2_SHARE = 0.90
MIN_CLASS = 10  # below this many drafts in one class, AURC and e-AURC describe the base rate
FINAL_MARK = "locked evaluation (final)"
PROBABILITIES = ("B1 verbalised", "B2 token probability", "B7 LR on B4+B5+B6")
BASELINES = ("B1 verbalised", "B2 token probability", "B3 self-consistency", "B4 top-1 similarity",
             "B5 reranker", "B6 entailment share", "B7 LR on B4+B5+B6")
B3_MIN_COVERAGE = 0.95  # B3 competes for "best baseline" only if it covers the answering validation drafts


@dataclass(frozen=True)
class Lanes:
    fast: float | None
    assisted: float | None

    def of(self, score: float, can_answer: bool | None) -> str:
        if not can_answer:
            return "escalate"
        if self.fast is not None and score >= self.fast:
            return "fast"
        if self.assisted is not None and score >= self.assisted:
            return "assisted"
        return "escalate"


def best_baseline(baseline_table: dict) -> str:
    """Lowest validation AURC among B1 to B7, read from the table written beforehand. B3 is a
    candidate only when it covers at least B3_MIN_COVERAGE of the answering validation drafts
    (amendment 2026-10-25): on sparse coverage its AURC measures what was computed, not B3."""
    val_split = baseline_table["splits"]["val"]
    candidates = {name: m["aurc"] for name, m in val_split["baselines"].items() if name in BASELINES}
    if (val_split.get("b3_coverage") or 0.0) < B3_MIN_COVERAGE:
        candidates.pop("B3 self-consistency", None)
    return min(candidates, key=lambda name: candidates[name])


def _r(x: float | None, nd: int = 4) -> float | None:
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def _interval(ci) -> dict:
    return {"estimate": _r(ci.estimate), "ci95": [_r(ci.low), _r(ci.high)], "resamples": ci.n_resamples}


def fast_risk(threshold: float | None):
    """Metric: share of unacceptable drafts among those at or above the fast threshold."""
    def metric(conf, y) -> float:
        if threshold is None:
            return float("nan")
        shown = conf >= threshold
        return float(1 - y[shown].mean()) if shown.any() else float("nan")
    return metric


def h1(p_model: np.ndarray, p_best: np.ndarray, y: np.ndarray, groups: list[str]) -> dict:
    ci = paired_bootstrap_diff(aurc, p_model, p_best, y, groups=groups, n_resamples=N_BOOT, seed=SEED)
    supported = ci.high < 0
    return {"rule": "paired bootstrap 95% interval of AURC(proposed) - AURC(best baseline) entirely below zero",
            "aurc_difference": _interval(ci), "supported": bool(supported),
            "decision": "supported" if supported else "no reliable improvement"}


def h2(p: np.ndarray, y: np.ndarray, groups: list[str], calib_share: float) -> dict:
    """Resplit the labelled pool by group; certify on one side, measure on the other."""
    rng = np.random.default_rng(SEED)
    unique = sorted(set(groups))
    g = np.array(groups)
    risks, closed = [], 0
    for _ in range(N_RESPLITS):
        order = rng.permutation(len(unique))
        cal_groups = {unique[i] for i in order[: round(len(unique) * calib_share)]}
        cal = np.isin(g, list(cal_groups))
        t = learn_then_test(p[cal], y[cal], alpha=ALPHA, delta=DELTA, candidates=DEFAULT_GRID)
        shown = (~cal) & (p >= t.threshold) if t.threshold is not None else np.zeros(len(p), bool)
        if not shown.any():
            closed += 1  # the lane shows nothing on the test side, so it cannot exceed alpha
            risks.append(0.0)
            continue
        risks.append(float(1 - y[shown].mean()))
    risks_a = np.array(risks)
    share = float((risks_a <= ALPHA).mean())
    testable = closed <= N_RESPLITS // 2
    if not testable:
        decision = f"not testable: the fast lane could not be certified in {closed} of {N_RESPLITS} resplits"
    else:
        decision = "supported" if share >= H2_SHARE else "not supported"
    edges = np.linspace(0, max(0.5, float(risks_a.max())), 21)
    counts, _ = np.histogram(risks_a, bins=edges)
    return {"rule": f"test-side fast-lane risk <= {ALPHA} in at least {H2_SHARE:.0%} of {N_RESPLITS} resplits",
            "share_within_alpha": _r(share), "resplits_with_closed_lane": closed,
            "median_test_risk": _r(float(np.median(risks_a))),
            "supported": bool(share >= H2_SHARE) if testable else None, "decision": decision,
            "histogram": {"edges": [_r(e) for e in edges], "counts": counts.tolist()}}


def exposure(rows, p: np.ndarray, y: np.ndarray, lanes: Lanes, guard=None) -> dict:
    """How many drafts an engineer would see, and how many of those are unacceptable.
    `guard`: a gate.service.Thresholds carrying the shift guard, or None for no guard."""
    from gate.service import guard_reasons

    shown = np.array([lanes.of(float(s), r.can_answer) != "escalate" for s, r in zip(p, rows)])
    if guard is not None:
        shown &= np.array([not guard_reasons(r.features, guard) for r in rows])
    bad = shown & (y == 0)
    return {"n_shown": int(shown.sum()), "shown_share": _r(float(shown.mean())),
            "unacceptable_shown": int(bad.sum()), "unacceptable_shown_share_of_all": _r(float(bad.mean())),
            "unacceptable_rate_among_shown": _r(float(1 - y[shown].mean())) if shown.any() else None}


def topic_block(rows, p: np.ndarray, y: np.ndarray, lanes: Lanes, guard=None) -> dict:
    """Pre-registered H3 numbers (AURC, fast-lane risk) plus, from the 2026-10-25 amendment,
    e-AURC, the class counts, and exposure with and without the shift guard. With very few
    acceptable (or unacceptable) drafts AURC reflects the base rate, not the ranking."""
    groups = [r.group_id for r in rows]
    n_ok = int(y.sum())
    return {"n": int(len(y)), "acceptable_share": _r(float(y.mean())),
            "n_acceptable": n_ok, "n_unacceptable": int(len(y) - n_ok),
            "ranking_informative": bool(min(n_ok, len(y) - n_ok) >= MIN_CLASS),
            "aurc": _interval(bootstrap_ci(aurc, p, y, groups=groups, n_resamples=N_BOOT, seed=SEED)),
            "e_aurc": _interval(bootstrap_ci(excess_aurc, p, y, groups=groups, n_resamples=N_BOOT, seed=SEED)),
            "fast_lane_risk": _interval(bootstrap_ci(fast_risk(lanes.fast), p, y, groups=groups,
                                                     n_resamples=N_BOOT, seed=SEED))
            if lanes.fast is not None and (p >= lanes.fast).any() else None,
            "exposure": {"without_guard": exposure(rows, p, y, lanes),
                         "with_guard": exposure(rows, p, y, lanes, guard) if guard is not None else None}}


def lane_block(p: np.ndarray, y: np.ndarray, can_answer: list, lanes: Lanes) -> dict:
    assigned = np.array([lanes.of(float(s), c) for s, c in zip(p, can_answer)])
    out: dict[str, object] = {}
    for lane in ("fast", "assisted", "escalate"):
        idx = assigned == lane
        out[lane] = {"n": int(idx.sum()), "share": _r(float(idx.mean())),
                     "unacceptable_rate": _r(float(1 - y[idx].mean())) if idx.any() else None}
    bad, good = y == 0, y == 1
    out["unacceptable_kept_out_of_fast"] = _r(float((assigned[bad] != "fast").mean())) if bad.any() else None
    out["false_escalation_rate"] = _r(float((assigned[good] == "escalate").mean())) if good.any() else None
    return out


def secondary(p: np.ndarray, y: np.ndarray, probability: bool = True) -> dict:
    """ECE and Brier only for scores meant as probabilities; a similarity score has none."""
    out = {"aurc": _r(aurc(p, y)), "auroc_unacceptable": _r(auroc_unacceptable(p, y)),
           "ece": _r(expected_calibration_error(p, y)) if probability else None,
           "brier": _r(brier_score(p, y)) if probability else None}
    for c in (0.5, 0.7, 0.9):
        out[f"risk_at_{int(c * 100)}"] = _r(risk_at_coverage(p, y, c))
    return out


def slices(rows, p: np.ndarray, y: np.ndarray) -> dict:
    out: dict[str, dict] = {}
    for key in ("type", "department"):
        out[key] = {}
        for value in sorted({getattr(r, key) for r in rows}):
            idx = np.array([getattr(r, key) == value for r in rows])
            y_s = y[idx]
            out[key][value] = {"n": int(idx.sum()), "acceptable_share": _r(float(y_s.mean())),
                               "aurc": _r(aurc(p[idx], y_s)) if 0 < y_s.sum() < len(y_s) else None}
    return out


def _b3_coverage(rows) -> float | None:
    answering = [r for r in rows if r.can_answer]
    extra = [getattr(r, "extra", {}) or {} for r in answering]
    return _r(sum(e.get("b3_claim_agreement") is not None for e in extra) / len(extra)) if extra else None


def b3_subset(rows, p: np.ndarray, y: np.ndarray) -> dict | None:
    """Descriptive, not H1: the proposed model against B3 on the drafts that have B3, so a
    draft without claims cannot decide the comparison either way."""
    idx = np.array([(getattr(r, "extra", {}) or {}).get("b3_claim_agreement") is not None for r in rows])
    if idx.sum() < 20 or not 0 < y[idx].sum() < idx.sum():
        return None
    b3 = np.array([r.extra["b3_claim_agreement"] for r, keep in zip(rows, idx) if keep], dtype=float)
    groups = [r.group_id for r, keep in zip(rows, idx) if keep]
    diff = paired_bootstrap_diff(aurc, p[idx], b3, y[idx], groups=groups, n_resamples=N_BOOT, seed=SEED)
    return {"n": int(idx.sum()), "proposed_aurc": _r(aurc(p[idx], y[idx])), "b3_aurc": _r(aurc(b3, y[idx])),
            "aurc_difference": _interval(diff)}


def evaluate(eval_rows, pool_rows, unseen_rows, p_eval, p_pool, p_unseen, baseline_scores: dict,
             best: str, lanes: Lanes, calib_share: float, guard=None) -> dict:
    """Everything the pre-registration asks for, from scores already computed."""
    y = np.array([r.acceptable for r in eval_rows], dtype=float)
    groups = [r.group_id for r in eval_rows]
    report: dict = {
        "n": len(eval_rows), "acceptable_share": _r(float(y.mean())), "best_baseline": best,
        "proposed": secondary(p_eval, y),
        "baselines": {name: {**secondary(s, y, probability=name in PROBABILITIES),
                             "aurc_ci95": _interval(bootstrap_ci(aurc, s, y, groups=groups, n_resamples=N_BOOT,
                                                                seed=SEED))["ci95"]}
                      for name, s in baseline_scores.items()},
        "b3_coverage": _b3_coverage(eval_rows),
        "b3_subset": b3_subset(eval_rows, p_eval, y),
        "H1": h1(p_eval, baseline_scores[best], y, groups),
        "H2": h2(p_pool, np.array([r.acceptable for r in pool_rows], dtype=float),
                 [r.group_id for r in pool_rows], calib_share),
        "lanes": lane_block(p_eval, y, [r.can_answer for r in eval_rows], lanes),
        "slices": slices(eval_rows, p_eval, y),
    }
    report["proposed"]["aurc_ci95"] = _interval(bootstrap_ci(aurc, p_eval, y, groups=groups, n_resamples=N_BOOT,
                                                             seed=SEED))["ci95"]
    h3 = {"seen": topic_block(eval_rows, p_eval, y, lanes, guard)}
    if unseen_rows:
        y_u = np.array([r.acceptable for r in unseen_rows], dtype=float)
        h3["unseen"] = topic_block(unseen_rows, p_unseen, y_u, lanes, guard)
        h3["unseen_lanes"] = lane_block(p_unseen, y_u, [r.can_answer for r in unseen_rows], lanes)
    report["H3"] = {"rule": "report seen vs unseen AURC and fast-lane risk with 95% intervals; "
                            "degradation is an expected finding", **h3}
    return report


def figures(report: dict, p_eval, y, baseline_scores: dict, out_dir: Path) -> list[str]:
    from evaluation.figures import bar_chart, line_chart

    def curve(conf):
        rc = risk_coverage_curve(conf, y)
        step = max(1, len(rc.coverage) // 100)
        return [float(c) for c in rc.coverage[::step]], [float(r) for r in rc.risk[::step]]

    series = {"proposed": curve(p_eval)} | {name: curve(s) for name, s in baseline_scores.items()}
    rel = reliability_bins(p_eval, y)
    centres = [(a + b) / 2 for a, b in zip(rel.bin_edges[:-1], rel.bin_edges[1:])]
    acc = [None if np.isnan(v) else float(v) for v in rel.accuracy]
    h2_hist = report["H2"]["histogram"]
    return [str(p.relative_to(ROOT)) for p in (
        line_chart(out_dir / "risk-coverage.svg", "Risk-coverage: proposed vs baselines", "coverage",
                   "risk (unacceptable share shown)", series),
        line_chart(out_dir / "reliability.svg", "Reliability of the calibrated score", "predicted probability",
                   "observed acceptable share", {"proposed": (centres, acc)}, y_range=(0.0, 1.0), diagonal=True),
        bar_chart(out_dir / "h2-resplits.svg", "H2: test-side fast-lane risk over resplits", "fast-lane risk",
                  "resplits", h2_hist["edges"], h2_hist["counts"], marker=ALPHA),
    )]


def summary_md(report: dict, final: bool) -> str:
    lines = [f"# Locked evaluation: {'final' if final else 'rehearsal'}", "",
             "Generated by `ai/evaluation/locked_eval.py`. "
             + ("Final run on the locked test with human labels." if final else
                "REHEARSAL on the validation split with LLM-judge labels: development numbers, not results."), "",
             "| Hypothesis | Decision | Detail |", "|---|---|---|"]
    d = report["H1"]["aurc_difference"]
    lines.append(f"| H1 | {report['H1']['decision']} | AURC difference vs {report['best_baseline']}: "
                 f"{d['estimate']} [{d['ci95'][0]}, {d['ci95'][1]}] |")
    lines.append(f"| H2 | {report['H2']['decision']} | fast-lane risk <= {ALPHA} in "
                 f"{report['H2']['share_within_alpha']:.0%} of resplits (needs {H2_SHARE:.0%}); lane closed in "
                 f"{report['H2']['resplits_with_closed_lane']} |")
    seen, unseen = report["H3"]["seen"], report["H3"].get("unseen")
    lines.append(f"| H3 | reported | AURC seen {seen['aurc']['estimate']} {seen['aurc']['ci95']}"
                 + (f", unseen {unseen['aurc']['estimate']} {unseen['aurc']['ci95']}" if unseen else "") + " |")
    if unseen:
        def shown(block, key):
            e = block["exposure"][key]
            return "n/a" if e is None else f"{e['n_shown']} of {block['n']} shown, {e['unacceptable_shown']} unacceptable"
        lines += ["", "| H3 detail | Seen | Unseen |", "|---|---|---|",
                  f"| Acceptable / unacceptable drafts | {seen['n_acceptable']} / {seen['n_unacceptable']} | "
                  f"{unseen['n_acceptable']} / {unseen['n_unacceptable']} |",
                  f"| e-AURC | {seen['e_aurc']['estimate']} {seen['e_aurc']['ci95']} | "
                  f"{unseen['e_aurc']['estimate']} {unseen['e_aurc']['ci95']}"
                  + ("" if unseen["ranking_informative"] else " (not informative: under "
                     f"{MIN_CLASS} drafts in one class)") + " |",
                  f"| Shown without the shift guard | {shown(seen, 'without_guard')} | {shown(unseen, 'without_guard')} |",
                  f"| Shown with the shift guard | {shown(seen, 'with_guard')} | {shown(unseen, 'with_guard')} |"]
    lines += ["", f"B3 covers {report['b3_coverage']} of the answering drafts here (a draft with no claims scores 0).",
              "", "| Method | AURC | 95% interval | AUROC (unacceptable) | ECE | Brier |", "|---|---|---|---|---|---|"]
    rows = [("Proposed", report["proposed"])] + list(report["baselines"].items())
    for name, m in rows:
        lines.append(f"| {name} | {m['aurc']} | {m['aurc_ci95']} | {m['auroc_unacceptable']} | {m['ece']} | {m['brier']} |")
    lines += ["", "Lanes: " + ", ".join(f"{k} {v['share']:.0%}" for k, v in report["lanes"].items()
                                         if isinstance(v, dict)), ""]
    return "\n".join(lines) + "\n"


def _already_final() -> bool:
    from confidence_model.dataset import ACCESS_LOG

    return ACCESS_LOG.exists() and FINAL_MARK in ACCESS_LOG.read_text(encoding="utf-8")


def main() -> None:
    import joblib

    from confidence_model.dataset import load
    from signals.report_baselines import CHEAP, baseline_scores, fit_b7

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--rehearse", action="store_true")
    mode.add_argument("--final", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    labels = "human" if args.final else "judge"
    artifact = ROOT / "ai" / "confidence_model" / "artifacts" / f"confidence-v1-{labels}.joblib"
    table = ROOT / "docs" / "results" / f"baselines-v1-{labels}.json"
    for need in (artifact, table):
        if not need.exists():
            sys.exit(f"missing {need.relative_to(ROOT)}: run `python ai/evaluation/reproduce.py --labels {labels}` first")
    if args.final:
        if args.confirm != "run the locked test once":
            sys.exit('the final run needs --confirm "run the locked test once"')
        if _already_final():
            sys.exit("the locked test was already evaluated; a new evaluation must be reported separately")

    bundle = joblib.load(artifact)
    model, th = bundle["model"], bundle["thresholds"]
    lanes = Lanes(th["fast"]["threshold"], th["assisted"]["threshold"])
    best = best_baseline(json.loads(table.read_text(encoding="utf-8")))
    guard = None
    shift = ROOT / "docs" / "results" / f"shift-v1-{labels}.json"
    if shift.exists():  # the shift guard chosen for these labels (Week 9); without it, exposure is reported unguarded
        from gate.service import Thresholds

        g = json.loads(shift.read_text(encoding="utf-8"))["guard"]
        guard = Thresholds("guard", lanes.fast, lanes.assisted, g["min_dept_prob"], g["min_probe_margin"])

    rows = asyncio.run(load("v1", labels, include_test=args.final, reason=FINAL_MARK if args.final else None))
    rows = [r for r in rows if r.acceptable is not None]
    eval_split = "test" if args.final else "val"
    by = {s: [r for r in rows if r.split == s] for s in ("train", "calib", eval_split, "unseen")}
    pool = by["calib"] + by[eval_split]
    b7 = fit_b7(by["train"])

    def scores(part):
        s = baseline_scores(part)
        s.pop("B0 always show")
        s["B7 LR on B4+B5+B6"] = b7.predict_proba(np.array([[r.features.get(k) or 0.0 for k in CHEAP]
                                                            for r in part]))[:, 1]
        return s

    p_eval = model.predict(by[eval_split])
    report = evaluate(by[eval_split], pool, by["unseen"], p_eval, model.predict(pool),
                      model.predict(by["unseen"]) if by["unseen"] else np.array([]), scores(by[eval_split]), best,
                      lanes, len(by["calib"]) / len(pool), guard)
    name = "locked-final" if args.final else "locked-rehearsal-judge"
    report = {"mode": "final" if args.final else "rehearsal (validation split, judge labels; not a result)",
              "labels": labels, "evaluated_split": eval_split, "model": artifact.name,
              "thresholds": {"fast": lanes.fast, "assisted": lanes.assisted}, **report}
    y = np.array([r.acceptable for r in by[eval_split]], dtype=float)
    report["figures"] = figures(report, p_eval, y, scores(by[eval_split]),
                                ROOT / "docs" / "results" / "figures" / name)
    out = ROOT / "docs" / "results" / f"{name}.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    (ROOT / "docs" / "results" / f"{name}.md").write_text(summary_md(report, args.final), encoding="utf-8")
    print(summary_md(report, args.final))
    print("->", out)


if __name__ == "__main__":
    main()
