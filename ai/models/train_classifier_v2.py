"""Train classifier v2 on benchmark v1 (Roadmap Week 4).

Candidates per target: embeddings only, and embeddings + TF-IDF. The candidate with the
best validation macro-F1 is kept (model selection on val only; the locked test split is
never loaded). Reports macro-F1, per-class precision/recall, the confusion matrix and the
hard subset (vague, multi-issue or typo tickets), next to the Week 3 TF-IDF baseline.
C1 tickets (unseen topics) are excluded from training like every other model, and the
unseen split is reported separately as a routing stress test.

Usage:
    uv run --project backend python ai/models/train_classifier_v2.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark.splits import file_sha256  # noqa: E402
from classifier_v2 import TargetModel, TicketClassifier, embed, entropy_normalised  # noqa: E402
from train_baseline_v2 import is_hard, load_split, ticket_text  # noqa: E402

TARGETS = ("department", "priority")


def evaluate(model: TargetModel, records: list[dict], target: str, emb: np.ndarray) -> dict:
    texts = [ticket_text(r) for r in records]
    probs = model.predict_proba(texts, emb)
    pred = [model.classes[i] for i in probs.argmax(axis=1)]
    gold = [r[target] for r in records]
    p, r_, f, s = precision_recall_fscore_support(gold, pred, labels=model.classes, zero_division=0)
    hard_idx = [i for i, rec in enumerate(records) if is_hard(rec)]
    correct = np.array([a == b for a, b in zip(pred, gold)])
    ent = entropy_normalised(probs)
    return {
        "macro_f1": round(f1_score(gold, pred, average="macro"), 4),
        "accuracy": round(float(correct.mean()), 4),
        "hard_macro_f1": round(f1_score([gold[i] for i in hard_idx], [pred[i] for i in hard_idx], average="macro"), 4)
        if hard_idx else None,
        "per_class": {c: {"precision": round(float(p[k]), 4), "recall": round(float(r_[k]), 4),
                          "f1": round(float(f[k]), 4), "support": int(s[k])} for k, c in enumerate(model.classes)},
        "confusion": {"labels": model.classes, "matrix": confusion_matrix(gold, pred, labels=model.classes).tolist()},
        # Uncertainty should be higher on mistakes; this checks it is informative at all.
        "mean_max_prob_correct": round(float(probs.max(axis=1)[correct].mean()), 4) if correct.any() else None,
        "mean_max_prob_wrong": round(float(probs.max(axis=1)[~correct].mean()), 4) if (~correct).any() else None,
        "mean_entropy_correct": round(float(ent[correct].mean()), 4) if correct.any() else None,
        "mean_entropy_wrong": round(float(ent[~correct].mean()), 4) if (~correct).any() else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets", type=Path, default=ROOT / "data/benchmark/benchmark_v1.jsonl")
    parser.add_argument("--splits", type=Path, default=ROOT / "data/benchmark/splits_v1.json")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/results/classifier-v2.json")
    args = parser.parse_args()

    splits = load_split(args.tickets, args.splits)  # never contains the locked test split
    train, val, unseen = splits["train"], splits["val"], splits.get("unseen", [])
    emb = {name: embed([ticket_text(r) for r in recs]) for name, recs in (("train", train), ("val", val), ("unseen", unseen)) if recs}

    report: dict = {"data_sha256": file_sha256(args.tickets), "n_train": len(train), "n_val": len(val)}
    chosen: dict[str, TargetModel] = {}
    for target in TARGETS:
        candidates = {}
        for name, use_tfidf in (("embedding", False), ("embedding+tfidf", True)):
            model = TargetModel(use_tfidf).fit([ticket_text(r) for r in train], emb["train"], [r[target] for r in train])
            candidates[name] = (model, evaluate(model, val, target, emb["val"]))
        best = max(candidates, key=lambda k: candidates[k][1]["macro_f1"])
        chosen[target] = candidates[best][0]
        report[target] = {
            "selected": best,
            "val": {name: res for name, (_, res) in candidates.items()},
            "unseen_topics": evaluate(chosen[target], unseen, target, emb["unseen"]) if unseen else None,
        }
        print(f"{target}: selected {best}; val macro-F1 "
              + ", ".join(f"{n} {r['macro_f1']}" for n, (_, r) in candidates.items())
              + (f"; unseen-topic macro-F1 {report[target]['unseen_topics']['macro_f1']}" if unseen else ""))

    TicketClassifier(chosen["department"], chosen["priority"], {"data_sha256": report["data_sha256"]}).save()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
