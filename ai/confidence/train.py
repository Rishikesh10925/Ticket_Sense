"""Trains the confidence model, preferring real reviewer outcomes over synthetic ones.

Week 8 trained purely on synthetic bootstrap labels (synthetic_labels.py's documented
formula) since no real `feedback` rows existed. Week 9's reviewer UI now populates that
table for real, so this builds two datasets and combines them:

1. **Real** — every non-synthetic-reviewer `feedback` row, labeled via
   `labels.py::label_from_feedback` (the accept/edit/reject/escalate mapping
   docs/confidence-labelling-guide.md proposed), using the exact `confidence_features`
   already stored on the ticket at scoring time — no need to re-run retrieval.
2. **Synthetic fallback** — the same Week 8 approach (real retrieval against the 120
   synthetic historical tickets, synthetic labels), but skipping any ticket that
   already has a real label so real data always wins for a given ticket.

As of Week 9 the real dataset is tiny (see docs/confidence-model.md's refinement
section for the honest count and what it does and doesn't prove) — this is
infrastructure for a signal that grows over time, not a claim that it already
dominates. See docs/confidence-model.md for the full write-up, including limitations
carried over from Week 8 (no attachment-bearing tickets in the synthetic bootstrap set,
so ocr_confidence still has near-zero variance from that half of the data).

Usage (from backend/): uv run python ../ai/confidence/train.py
Requires the `ai` extra and a running, migrated, seeded database (departments, the 120
synthetic historical tickets, and their embeddings — see data/README.md).
"""

import asyncio
import json
import random
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
AI_EMBEDDINGS_DIR = Path(__file__).resolve().parents[1] / "embeddings"
if str(AI_EMBEDDINGS_DIR) not in sys.path:
    sys.path.insert(0, str(AI_EMBEDDINGS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.models import Department, Feedback, Ticket, User  # noqa: E402

from retrieve import retrieve_evidence  # noqa: E402
from features import FEATURE_NAMES, compute_features  # noqa: E402
from synthetic_labels import simulate_outcome  # noqa: E402
from labels import SYNTHETIC_REVIEWER_EMAIL, label_from_feedback  # noqa: E402

SEED = 42
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
METRICS_FILE = Path(__file__).resolve().parents[2] / "docs" / "confidence-metrics.md"


async def _build_real_dataset(db) -> tuple[list[tuple[list[float], bool]], set, list[dict]]:
    """Real `feedback` rows -> labeled examples. Returns (rows, covered ticket ids,
    skipped-row details for the metrics report)."""
    stmt = (
        select(Feedback, Ticket)
        .join(Ticket, Feedback.ticket_id == Ticket.id)
        .join(User, Feedback.reviewer_id == User.id)
        .where(User.email != SYNTHETIC_REVIEWER_EMAIL)
    )
    rows: list[tuple[list[float], bool]] = []
    covered_ticket_ids = set()
    skipped: list[dict] = []

    for feedback, ticket in (await db.execute(stmt)).all():
        covered_ticket_ids.add(ticket.id)
        if ticket.confidence_features is None:
            skipped.append({"ticket": ticket.subject, "reason": "no confidence_features stored"})
            continue
        label = label_from_feedback(feedback.action, ticket.ai_draft_reply, feedback.edited_reply)
        if label is None:
            skipped.append({"ticket": ticket.subject, "reason": f"'{feedback.action}' excluded from training"})
            continue
        vector = [ticket.confidence_features[name] for name in FEATURE_NAMES]
        rows.append((vector, label))

    return rows, covered_ticket_ids, skipped


async def _build_synthetic_dataset(db, exclude_ticket_ids: set) -> list[tuple[list[float], bool]]:
    rng = random.Random(SEED)
    rows: list[tuple[list[float], bool]] = []

    departments = {d.id: d.name for d in await db.scalars(select(Department))}
    tickets = list(
        await db.scalars(select(Ticket).where(Ticket.status == "closed", Ticket.department_id.is_not(None)))
    )

    for ticket in tickets:
        if ticket.id in exclude_ticket_ids:
            continue  # a real label already covers this ticket -- real wins
        department_name = departments.get(ticket.department_id)
        query_text = f"{ticket.subject}\n\n{ticket.description}"
        # k=6, then drop the ticket's own embedding row (it's in the same table
        # it's being embedded against, so it would otherwise match itself at
        # distance ~0 — an unrealistic freebie no live ticket ever gets).
        evidence = await retrieve_evidence(db, query_text, ticket.department_id, k=6)
        evidence = [item for item in evidence if item.source_id != ticket.id][:5]

        features = compute_features(evidence, ocr_confidence=None, department_name=department_name)
        label = simulate_outcome(features, rng)
        rows.append((features.to_vector(), label))

    return rows


async def _build_dataset() -> tuple[list[tuple[list[float], bool]], int, int, list[dict]]:
    """Returns (all rows, n_real, n_synthetic, skipped real rows)."""
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        real_rows, covered_ticket_ids, skipped = await _build_real_dataset(db)
        synthetic_rows = await _build_synthetic_dataset(db, covered_ticket_ids)

    await engine.dispose()
    return real_rows + synthetic_rows, len(real_rows), len(synthetic_rows), skipped


def _report_to_markdown(
    report: dict, auc: float, n_train: int, n_test: int, n_real: int, n_synthetic: int, coefficients: dict
) -> str:
    lines = [
        "# Confidence model — evaluation",
        "",
        "Generated by `ai/confidence/train.py`. See "
        "[confidence-model.md](confidence-model.md) for the feature engineering "
        "rationale and what these numbers do and don't mean.",
        "",
        f"Trained on {n_train} examples, evaluated on {n_test} held-out examples — "
        f"{n_real} real (from actual reviewer `feedback` rows, labeled per "
        f"[confidence-labelling-guide.md](confidence-labelling-guide.md)) and "
        f"{n_synthetic} synthetic bootstrap labels for tickets with no real feedback "
        "yet (see confidence-model.md).",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for label, stats in report.items():
        if label in ("accuracy", "macro avg", "weighted avg"):
            continue
        name = "success" if label == "1" else "failure"
        lines.append(
            f"| {name} | {stats['precision']:.2f} | {stats['recall']:.2f} | "
            f"{stats['f1-score']:.2f} | {int(stats['support'])} |"
        )
    macro = report["macro avg"]
    lines.append(
        f"| **macro avg** | {macro['precision']:.2f} | {macro['recall']:.2f} | "
        f"{macro['f1-score']:.2f} | {int(macro['support'])} |"
    )
    lines.append(f"\n**Accuracy:** {report['accuracy']:.2f}  \n**ROC-AUC:** {auc:.3f}")

    lines.append("\n## Learned feature coefficients\n")
    lines.append("| Feature | Coefficient |")
    lines.append("|---|---|")
    for name, coef in coefficients.items():
        lines.append(f"| `{name}` | {coef:+.3f} |")

    return "\n".join(lines)


def main() -> None:
    rows, n_real, n_synthetic, skipped = asyncio.run(_build_dataset())
    X = np.array([r[0] for r in rows])
    y = np.array([int(r[1]) for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    auc = roc_auc_score(y_test, probabilities)

    print(f"=== Confidence model ({len(X_train)} train / {len(X_test)} test, {n_real} real / {n_synthetic} synthetic) ===")
    print(classification_report(y_test, predictions, zero_division=0))
    print(f"ROC-AUC: {auc:.3f}")
    if skipped:
        print(f"\nSkipped {len(skipped)} real feedback row(s):")
        for item in skipped:
            print(f"  - {item['ticket']}: {item['reason']}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACTS_DIR / "confidence_model.joblib")

    coefficients = dict(zip(FEATURE_NAMES, model.coef_[0].tolist()))
    with (ARTIFACTS_DIR / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "n_train": len(X_train),
                "n_test": len(X_test),
                "n_real": n_real,
                "n_synthetic": n_synthetic,
                "skipped_real_rows": skipped,
                "report": report,
                "roc_auc": auc,
                "coefficients": coefficients,
            },
            f,
            indent=2,
        )

    METRICS_FILE.write_text(
        _report_to_markdown(report, auc, len(X_train), len(X_test), n_real, n_synthetic, coefficients) + "\n",
        encoding="utf-8",
    )
    print(f"\nSaved model to {ARTIFACTS_DIR}/confidence_model.joblib, metrics to {METRICS_FILE}")


if __name__ == "__main__":
    main()
