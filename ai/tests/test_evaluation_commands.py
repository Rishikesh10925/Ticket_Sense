"""The evaluation commands run end to end on synthetic rows (Roadmap Week 10: "all tables
and figures regenerated from one command"). The database, the benchmark and the locked
test are never touched: `load` is replaced and every output goes to a temp folder."""

import json
import subprocess

import numpy as np
import pytest

from confidence_model import ablate, shift, train
from confidence_model import dataset as ds
from evaluation import locked_eval, reproduce
from signals import report_baselines


def synthetic_rows() -> list[ds.Row]:
    rng = np.random.default_rng(7)
    rows = []
    for split, n, p_ok in (("train", 240, 0.75), ("val", 90, 0.75), ("calib", 150, 0.75), ("unseen", 72, 0.3)):
        for i in range(n):
            y = int(rng.random() < p_ok)
            s = float(np.clip(0.5 + 0.35 * (y - 0.5) + rng.normal(0, 0.12), 0.01, 0.99))
            features = {"ret_top1_dense": s, "rr_top1": s + rng.normal(0, 0.05), "gr_supported_share": s,
                        "rt_dept_max_prob": float(rng.uniform(0.4, 1.0)), "rt_probe_margin": float(rng.uniform(-0.2, 0.3))}
            topic = f"u{i % 6}" if split == "unseen" else f"t{i % 4}"
            rows.append(ds.Row(f"d-{split}-{i}", f"T-{split}-{i}", f"g-{split}-{i // 3}", "AB"[i % 2],
                               ("SAP", "HR", "Cloud")[i % 3], topic, split, True, features, y,
                               {"b1_verbalised": s, "b2_mean_prob": s}))
    return rows


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    rows = synthetic_rows()

    async def fake_load(version="v1", label_source="judge", include_test=False, reason=None):
        assert not include_test, "the locked test must never be read in tests"
        return rows

    (tmp_path / "docs" / "results").mkdir(parents=True)
    artifacts = tmp_path / "ai" / "confidence_model" / "artifacts"
    for module in (train, ablate, shift, report_baselines, locked_eval):
        monkeypatch.setattr(module, "ROOT", tmp_path)
    for module in (train, ablate, shift):
        monkeypatch.setattr(module, "load", fake_load)
    monkeypatch.setattr(ds, "load", fake_load)
    monkeypatch.setattr(train, "ARTIFACT_DIR", artifacts)
    return tmp_path


def run(module, monkeypatch, *argv):
    monkeypatch.setattr("sys.argv", [module.__name__, *argv])
    module.main()


def test_every_evaluation_command_runs_on_synthetic_rows(sandbox, monkeypatch):
    results = sandbox / "docs" / "results"
    run(train, monkeypatch, "--labels", "judge")
    run(report_baselines, monkeypatch, "--labels", "judge", "--n-boot", "50")
    run(ablate, monkeypatch, "--labels", "judge", "--n-boot", "50")
    run(shift, monkeypatch, "--labels", "judge")
    run(locked_eval, monkeypatch, "--rehearse")

    model = json.loads((results / "confidence-v1-judge.json").read_text(encoding="utf-8"))
    assert model["chosen"] in ("logreg", "xgboost") and set(model["thresholds"]) == {"fast", "assisted"}
    baselines = json.loads((results / "baselines-v1-judge.json").read_text(encoding="utf-8"))
    assert "B7 LR on B4+B5+B6" in baselines["splits"]["val"]["baselines"]
    assert json.loads((results / "ablations-v1-judge.json").read_text(encoding="utf-8"))["ablations"]
    assert "guard" in json.loads((results / "shift-v1-judge.json").read_text(encoding="utf-8"))
    rehearsal = json.loads((results / "locked-rehearsal-judge.json").read_text(encoding="utf-8"))
    assert rehearsal["evaluated_split"] == "val" and {"H1", "H2", "H3"} <= set(rehearsal)
    assert len(rehearsal["figures"]) == 3
    assert (results / "locked-rehearsal-judge.md").read_text(encoding="utf-8").startswith("# Locked evaluation: rehearsal")


def test_reproduce_runs_each_step_and_stops_on_failure(monkeypatch, capsys):
    calls = []

    def fake_run(cmd, **_):
        calls.append(cmd[1])
        return subprocess.CompletedProcess(cmd, 1 if "ablate.py" in cmd[1] else 0, "", "boom")

    monkeypatch.setattr(ds, "verify_inputs", lambda version: None)
    monkeypatch.setattr(reproduce.subprocess, "run", fake_run)
    monkeypatch.setattr("sys.argv", ["reproduce.py", "--skip", "retrieval"])
    with pytest.raises(SystemExit, match="ablations FAILED"):
        reproduce.main()
    assert calls == ["ai/signals/report_baselines.py", "ai/confidence_model/train.py", "ai/confidence_model/ablate.py"]


def test_reproduce_never_runs_the_final_locked_evaluation():
    for labels in ("judge", "human"):
        commands = [" ".join(cmd) for _, cmd in reproduce.steps(labels)]
        assert not any("--final" in c for c in commands)
    assert any("--rehearse" in " ".join(cmd) for _, cmd in reproduce.steps("judge"))
    assert not any("locked_eval" in " ".join(cmd) for _, cmd in reproduce.steps("human"))
