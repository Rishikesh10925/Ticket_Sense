"""The locked evaluation applies the pre-registered rules exactly (docs/prereg.md).
Synthetic rows only: the locked test is never read here."""

from dataclasses import dataclass, field

import numpy as np
import pytest

from evaluation import locked_eval as le
from evaluation.figures import bar_chart, line_chart


@dataclass
class FakeRow:
    group_id: str
    acceptable: int
    can_answer: bool = True
    type: str = "A"
    department: str = "SAP"
    features: dict = field(default_factory=dict)


def rows_and_scores(n=200, signal=1.0, seed=0):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.8).astype(float)
    p = np.clip(0.5 + signal * (y - 0.5) * 0.8 + rng.normal(0, 0.15, n), 0.001, 0.999)
    rows = [FakeRow(f"g{i // 2}", int(v), type="AB"[i % 2], department=("SAP", "HR")[i % 2]) for i, v in enumerate(y)]
    return rows, p, y


def test_best_baseline_uses_validation_aurc_among_b1_to_b7():
    table = {"splits": {"val": {"baselines": {
        "B0 always show": {"aurc": 0.01},  # never eligible
        "B4 top-1 similarity": {"aurc": 0.20},
        "B7 LR on B4+B5+B6": {"aurc": 0.15},
        "B1 verbalised": {"aurc": 0.30}}}}}
    assert le.best_baseline(table) == "B7 LR on B4+B5+B6"


def test_lanes_follow_thresholds_and_cannot_answer_escalates():
    lanes = le.Lanes(fast=0.9, assisted=0.5)
    assert lanes.of(0.95, True) == "fast"
    assert lanes.of(0.6, True) == "assisted"
    assert lanes.of(0.2, True) == "escalate"
    assert lanes.of(0.99, False) == "escalate"
    assert le.Lanes(None, None).of(0.99, True) == "escalate"


def test_h1_supported_only_when_interval_is_below_zero():
    rows, p, y = rows_and_scores()
    groups = [r.group_id for r in rows]
    noise = np.random.default_rng(1).random(len(y))
    assert le.h1(p, noise, y, groups)["supported"] is True
    same = le.h1(p, p, y, groups)
    assert same["supported"] is False and same["decision"] == "no reliable improvement"


def test_h2_is_not_testable_when_the_fast_lane_never_opens():
    rows, _, y = rows_and_scores()
    useless = np.full(len(y), 0.5)  # no threshold can be certified at alpha 0.10
    out = le.h2(useless, y, [r.group_id for r in rows], 0.5)
    assert out["resplits_with_closed_lane"] == le.N_RESPLITS
    assert out["supported"] is None and out["decision"].startswith("not testable")


def test_h2_supported_with_a_well_separated_score():
    rows, p, y = rows_and_scores(n=600, signal=1.0)
    out = le.h2(p, y, [r.group_id for r in rows], 0.5)
    assert out["resplits_with_closed_lane"] < le.N_RESPLITS // 2
    assert out["supported"] is True and sum(out["histogram"]["counts"]) == le.N_RESPLITS


def test_evaluate_reports_every_preregistered_section():
    rows, p, y = rows_and_scores()
    unseen, p_u, _ = rows_and_scores(n=60, signal=0.0, seed=3)
    baselines = {"B4 top-1 similarity": np.random.default_rng(2).random(len(y)), "B7 LR on B4+B5+B6": p * 0.9}
    report = le.evaluate(rows, rows, unseen, p, p, p_u, baselines, "B4 top-1 similarity",
                         le.Lanes(0.8, 0.4), calib_share=0.5)
    for key in ("H1", "H2", "H3", "lanes", "slices", "proposed", "baselines"):
        assert key in report
    assert set(report["H3"]) >= {"seen", "unseen", "unseen_lanes"}
    assert report["baselines"]["B4 top-1 similarity"]["ece"] is None  # not a probability
    assert report["baselines"]["B7 LR on B4+B5+B6"]["ece"] is not None
    assert set(report["slices"]["type"]) == {"A", "B"}
    lanes = report["lanes"]
    assert sum(lanes[k]["n"] for k in ("fast", "assisted", "escalate")) == len(rows)
    assert "Locked evaluation: rehearsal" in le.summary_md(report, final=False)


def test_final_run_refuses_without_confirmation(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["locked_eval.py", "--final"])
    monkeypatch.setattr(le, "ROOT", tmp_path)  # no artifact here: must stop before any data is read
    with pytest.raises(SystemExit):
        le.main()


def test_figures_are_svg(tmp_path):
    line = line_chart(tmp_path / "a.svg", "t", "x", "y", {"s": ([0, 0.5, 1], [0.1, 0.2, 0.3])}, diagonal=True)
    bars = bar_chart(tmp_path / "b.svg", "t", "x", "y", [0, 0.1, 0.2], [3, 5], marker=0.1)
    for path in (line, bars):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("<svg") and text.rstrip().endswith("</svg>")
