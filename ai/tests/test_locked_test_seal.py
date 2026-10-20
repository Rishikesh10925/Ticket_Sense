import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_locked_test_selection_matches_its_seal():
    seal = json.loads((ROOT / "data/annotation/locked_test_seal.json").read_text(encoding="utf-8"))
    selected = json.loads((ROOT / "data/annotation/selection_v1.json").read_text(encoding="utf-8"))["selected"]["test"]
    assert len(selected) == seal["n"] == 250
    assert hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest() == seal["ticket_ids_sha256"]


def test_nobody_has_read_the_locked_test_yet():
    # Until the Week 10 evaluation, the access log must not exist.
    assert not (ROOT / "data/annotation/locked_test_access.log").exists()


def test_training_refuses_a_tampered_selection(tmp_path, monkeypatch):
    import pytest

    import confidence_model.dataset as ds

    fake = tmp_path / "data" / "annotation"
    fake.mkdir(parents=True)
    (fake / "locked_test_seal.json").write_text((ROOT / "data/annotation/locked_test_seal.json").read_text())
    selection = json.loads((ROOT / "data/annotation/selection_v1.json").read_text(encoding="utf-8"))
    selection["selected"]["test"][0] = "T-99999"  # one swapped ticket
    (fake / "selection_v1.json").write_text(json.dumps(selection))
    monkeypatch.setattr(ds, "ROOT", tmp_path)
    monkeypatch.setattr("benchmark.freeze.verify", lambda version: [])
    with pytest.raises(RuntimeError, match="seal"):
        ds.verify_inputs("v1")


def test_untouched_inputs_verify():
    from confidence_model.dataset import verify_inputs

    verify_inputs("v1")
