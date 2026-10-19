"""TF-IDF + logistic regression baseline for department and priority on benchmark v1
(Roadmap Week 3). The Week 4 classifier (embeddings, uncertainty output) must beat it.

Trains on the `train` split and reports on `val` only. The locked `test` split is never
read here (docs/prereg.md: no tuning or model selection on it). The "hard subset" is
validation tickets flagged vague, multi-issue or with typos (Blueprint §15.1).

Usage:
    uv run --project backend python ai/models/train_baseline_v2.py \
        --tickets data/benchmark/benchmark_v1.jsonl --splits data/benchmark/splits_v1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))

from benchmark.splits import file_sha256  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parent / "artifacts" / "v2"
SEED = 2026
TARGETS = ("department", "priority")


def ticket_text(r: dict) -> str:
    return f"{r['text']}\n{r.get('attachment_text') or ''}".strip()


def is_hard(r: dict) -> bool:
    d = r.get("difficulty", {})
    return bool(d.get("vague") or d.get("multi_issue") or d.get("typos"))


def make_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)),
        ]
    )


def load_split(tickets_path: Path, splits_path: Path) -> dict[str, list[dict]]:
    records = [json.loads(x) for x in tickets_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assignment = json.loads(splits_path.read_text(encoding="utf-8"))["assignment"]
    out: dict[str, list[dict]] = {}
    for r in records:
        out.setdefault(assignment[r["ticket_id"]], []).append(r)
    out.pop("test", None)  # locked: never loaded by training or model selection
    return out


def train_and_report(splits: dict[str, list[dict]]) -> tuple[dict, dict]:
    train, val = splits["train"], splits["val"]
    hard = [r for r in val if is_hard(r)]
    models, report = {}, {"n_train": len(train), "n_val": len(val), "n_val_hard": len(hard)}
    for target in TARGETS:
        model = make_pipeline().fit([ticket_text(r) for r in train], [r[target] for r in train])
        pred = model.predict([ticket_text(r) for r in val])
        gold = [r[target] for r in val]
        hard_pred = model.predict([ticket_text(r) for r in hard]) if hard else []
        report[target] = {
            "val_macro_f1": round(f1_score(gold, pred, average="macro"), 4),
            "val_accuracy": round(sum(p == g for p, g in zip(pred, gold)) / len(gold), 4),
            "val_hard_macro_f1": round(f1_score([r[target] for r in hard], hard_pred, average="macro"), 4)
            if hard else None,
            "per_class": {
                k: {m: round(v, 4) for m, v in d.items()}
                for k, d in classification_report(gold, pred, output_dict=True, zero_division=0).items()
                if isinstance(d, dict) and k not in ("macro avg", "weighted avg")
            },
        }
        models[target] = model
    return models, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets", type=Path, default=ROOT / "data/benchmark/benchmark_v1.jsonl")
    parser.add_argument("--splits", type=Path, default=ROOT / "data/benchmark/splits_v1.json")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/results/classifier-baseline-v1.json")
    args = parser.parse_args()

    models, report = train_and_report(load_split(args.tickets, args.splits))
    report["data_sha256"] = file_sha256(args.tickets)
    report["model"] = "tfidf(1,2)+logreg(balanced)"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for target, model in models.items():
        joblib.dump(model, ARTIFACTS / f"baseline_{target}.joblib")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for target in TARGETS:
        r = report[target]
        print(f"{target}: val macro-F1 {r['val_macro_f1']}  accuracy {r['val_accuracy']}  "
              f"hard-subset macro-F1 {r['val_hard_macro_f1']}")


if __name__ == "__main__":
    main()
