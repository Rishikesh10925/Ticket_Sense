import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "models"))

from train_baseline_v2 import is_hard, load_split, train_and_report  # noqa: E402

VOCAB = {
    "SAP": "transaction posting purchase order sap gui material",
    "Networking": "vpn wifi dns proxy switch port network",
    "HR": "leave payslip benefits salary holiday manager",
}


def _records(n=150):
    rng = random.Random(0)
    out = []
    for i in range(n):
        dept = list(VOCAB)[i % 3]
        words = rng.sample(VOCAB[dept].split(), 4)
        out.append({"ticket_id": f"T{i}", "text": " ".join(words), "attachment_text": None, "department": dept,
                    "priority": ("low", "high")[i % 2], "difficulty": {"typos": i % 5 == 0}})
    return out


def test_baseline_learns_departments_and_never_loads_test(tmp_path):
    recs = _records()
    tickets = tmp_path / "t.jsonl"
    tickets.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    assignment = {r["ticket_id"]: ("train", "train", "val", "test")[i % 4] for i, r in enumerate(recs)}
    splits_file = tmp_path / "s.json"
    splits_file.write_text(json.dumps({"assignment": assignment}), encoding="utf-8")

    splits = load_split(tickets, splits_file)
    assert "test" not in splits
    _, report = train_and_report(splits)
    assert report["department"]["val_macro_f1"] > 0.9
    assert report["n_val_hard"] == sum(is_hard(r) for r in splits["val"])
