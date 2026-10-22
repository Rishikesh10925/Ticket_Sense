"""User-study analysis (Roadmap Week 11, Aashritha and Shivaganesh; pre-registration H4).

    python ai/study/analyse.py

H4: the AI-assisted workflow cuts median handling time by at least 20% with no increase
in accepted major errors. Reported descriptively with paired intervals, as pre-registered
(small sample). Inputs in data/study/:

    tasks.csv          from `python -m app.scripts.export_study`
    grading_sheet.csv  the same export, with `grade` filled in blind (A/M/R/W, rubric)
    grading_key.csv    grade_id -> task_id
    sus.csv            participant,q1..q10 (answers 1 to 5), typed in from the SUS forms

Measures:

- Handling time: each participant's median seconds per ticket in each condition; the
  reduction is 1 - workbench/manual per participant, summarised by its median and a
  bootstrap interval over participants.
- Accepted major errors: sent replies graded R or W (escalations send nothing). Rates per
  condition and the paired difference.
- SUS: the standard score (0 to 100) per participant.

Writes docs/results/study-v1.json and study-v1.md.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "study"
SEED = 2026
N_BOOT = 2000
MAJOR = {"R", "W"}


def sus_score(answers: list[int]) -> float:
    """Brooke (1996): odd items answer - 1, even items 5 - answer, sum times 2.5."""
    if len(answers) != 10 or any(a not in (1, 2, 3, 4, 5) for a in answers):
        raise ValueError("SUS needs ten answers from 1 to 5")
    return 2.5 * sum((a - 1) if i % 2 == 0 else (5 - a) for i, a in enumerate(answers))


def _ci(values: list[float], stat=np.median) -> list[float] | None:
    if len(values) < 2:
        return None
    rng = np.random.default_rng(SEED)
    arr = np.array(values, dtype=float)
    boots = [float(stat(rng.choice(arr, size=len(arr), replace=True))) for _ in range(N_BOOT)]
    return [round(float(np.quantile(boots, 0.025)), 4), round(float(np.quantile(boots, 0.975)), 4)]


def analyse(tasks: list[dict], grades: dict[str, str], sus: dict[str, list[int]]) -> dict:
    """tasks: rows of tasks.csv; grades: task_id -> A/M/R/W; sus: participant -> answers."""
    by: dict[str, dict[str, list[dict]]] = {}
    for t in tasks:
        by.setdefault(t["participant"], {"manual": [], "workbench": []})[t["condition"]].append(t)
    participants = sorted(p for p, c in by.items() if c["manual"] and c["workbench"])

    per = {}
    for p in participants:
        row = {}
        for cond in ("manual", "workbench"):
            ts = by[p][cond]
            sent = [t for t in ts if t["action"] != "escalate"]
            graded = [grades[t["task_id"]] for t in sent if grades.get(t["task_id"])]
            row[cond] = {
                "n": len(ts), "median_s": round(statistics.median(int(t["time_ms"]) for t in ts) / 1000, 1),
                "escalated": len(ts) - len(sent), "sent": len(sent), "graded": len(graded),
                "major_errors": sum(g in MAJOR for g in graded),
                "major_error_rate": round(sum(g in MAJOR for g in graded) / len(graded), 4) if graded else None,
            }
        row["time_reduction"] = round(1 - row["workbench"]["median_s"] / row["manual"]["median_s"], 4) \
            if row["manual"]["median_s"] else None
        if p in sus:
            row["sus"] = sus_score(sus[p])
        per[p] = row

    reductions = [r["time_reduction"] for r in per.values() if r["time_reduction"] is not None]
    err_diff = [r["workbench"]["major_error_rate"] - r["manual"]["major_error_rate"] for r in per.values()
                if r["workbench"]["major_error_rate"] is not None and r["manual"]["major_error_rate"] is not None]
    sus_scores = [r["sus"] for r in per.values() if "sus" in r]
    actions = {}
    for t in tasks:
        if t["condition"] == "workbench":
            key = f"{t['lane']}:{t['action']}"
            actions[key] = actions.get(key, 0) + 1
    median_red = round(statistics.median(reductions), 4) if reductions else None
    median_err = round(statistics.median(err_diff), 4) if err_diff else None
    return {
        "n_participants": len(participants),
        "per_participant": per,
        "handling_time": {
            "median_manual_s": round(statistics.median(r["manual"]["median_s"] for r in per.values()), 1)
            if per else None,
            "median_workbench_s": round(statistics.median(r["workbench"]["median_s"] for r in per.values()), 1)
            if per else None,
            "median_reduction": median_red, "reduction_ci95": _ci(reductions),
        },
        "major_errors": {
            "manual": sum(r["manual"]["major_errors"] for r in per.values()),
            "workbench": sum(r["workbench"]["major_errors"] for r in per.values()),
            "median_rate_difference": median_err, "difference_ci95": _ci(err_diff),
            "ungraded_replies": sum(r[c]["sent"] - r[c]["graded"] for r in per.values() for c in ("manual", "workbench")),
        },
        "sus": {"n": len(sus_scores), "mean": round(statistics.mean(sus_scores), 1) if sus_scores else None,
                "ci95": _ci(sus_scores, stat=np.mean)},
        "workbench_lane_actions": dict(sorted(actions.items())),
        "H4": {
            "rule": "median handling time reduced by at least 20% with no increase in accepted major errors; "
                    "descriptive, small sample",
            "time_target_met": None if median_red is None else bool(median_red >= 0.20),
            "no_increase_in_major_errors": None if median_err is None else bool(median_err <= 0),
        },
    }


def _read(name: str) -> list[dict]:
    path = DATA / name
    if not path.exists():
        sys.exit(f"missing {path.relative_to(ROOT)}: see the docstring")
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def summary_md(r: dict) -> str:
    ht, me, sus = r["handling_time"], r["major_errors"], r["sus"]
    lines = ["# User study results", "", f"Participants with both conditions: {r['n_participants']}.", "",
             "| Measure | Manual | Workbench | Paired |", "|---|---|---|---|",
             f"| Median handling time (s) | {ht['median_manual_s']} | {ht['median_workbench_s']} | "
             f"reduction {ht['median_reduction']} {ht['reduction_ci95']} |",
             f"| Accepted major errors (R or W) | {me['manual']} | {me['workbench']} | "
             f"rate difference {me['median_rate_difference']} {me['difference_ci95']} |",
             f"| SUS (workbench) | | {sus['mean']} {sus['ci95']} | n = {sus['n']} |", "",
             f"H4: time target met: {r['H4']['time_target_met']}; no increase in major errors: "
             f"{r['H4']['no_increase_in_major_errors']}. Descriptive only (small sample).", ""]
    return "\n".join(lines) + "\n"


def main() -> None:
    tasks = _read("tasks.csv")
    sheet = {row["grade_id"]: row["grade"].strip().upper() for row in _read("grading_sheet.csv")}
    grades = {row["task_id"]: sheet.get(row["grade_id"], "") for row in _read("grading_key.csv")}
    if any(g and g not in "AMRW" for g in grades.values()):
        sys.exit("grades must be A, M, R or W")
    sus = {row["participant"]: [int(row[f"q{i}"]) for i in range(1, 11)] for row in _read("sus.csv")}
    report = analyse(tasks, grades, sus)
    out = ROOT / "docs" / "results" / "study-v1.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    out.with_suffix(".md").write_text(summary_md(report), encoding="utf-8")
    print(summary_md(report))
    print("->", out)


if __name__ == "__main__":
    main()
