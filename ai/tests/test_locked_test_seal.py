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
