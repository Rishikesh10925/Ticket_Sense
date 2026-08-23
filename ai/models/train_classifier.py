"""Train the department, priority, and sentiment classifiers.

Three independent scikit-learn pipelines (TF-IDF + LogisticRegression), matching
docs/architecture.md's "3 independent scikit-learn pipelines, not one multi-output
model" decision, since the three targets have unrelated label spaces.

Training data is the union of:
- data/processed/tickets_{train,val,test}.csv — the cleaned public dataset (real
  examples, but only Networking/HR have any, and it has no sentiment label at all;
  see docs/dataset-cleaning.md).
- data/processed/synthetic_tickets.csv — the hand-authored set covering all 5
  departments and all 3 targets (see synthetic_labeled_tickets.py), split 70/15/15
  the same way (stratified by department, seed 42) so it contributes to train/val/test
  in the same proportions rather than only padding the training set.

The sentiment classifier is trained on the synthetic split alone, since the public
dataset has no sentiment labels to contribute.

Requires the `ai` extra: `uv sync --extra ai` (from backend/).

Usage (from repo root):
    uv run --project backend --extra ai python ai/models/train_classifier.py
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

SEED = 42
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
METRICS_FILE = Path(__file__).resolve().parents[2] / "docs" / "classification-metrics.md"


def _text(df: pd.DataFrame) -> pd.Series:
    return (df["subject"].fillna("") + " " + df["description"].fillna("")).str.strip()


def _split_synthetic(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train, temp = train_test_split(df, test_size=0.30, random_state=SEED, stratify=df["department"])
    val, test = train_test_split(temp, test_size=0.50, random_state=SEED, stratify=temp["department"])
    return train, val, test


def _train_and_evaluate(
    name: str, train_df: pd.DataFrame, test_df: pd.DataFrame, label_col: str
) -> tuple[Pipeline, dict]:
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(_text(train_df), train_df[label_col])

    predictions = pipeline.predict(_text(test_df))
    report = classification_report(test_df[label_col], predictions, output_dict=True, zero_division=0)

    print(f"\n=== {name} ({len(train_df)} train / {len(test_df)} test) ===")
    print(classification_report(test_df[label_col], predictions, zero_division=0))

    return pipeline, report


def _report_to_markdown(name: str, report: dict, n_train: int, n_test: int) -> str:
    lines = [
        f"## {name}",
        "",
        f"Trained on {n_train} examples, evaluated on {n_test} held-out examples.",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for label, stats in report.items():
        if label in ("accuracy", "macro avg", "weighted avg"):
            continue
        lines.append(
            f"| {label} | {stats['precision']:.2f} | {stats['recall']:.2f} | "
            f"{stats['f1-score']:.2f} | {int(stats['support'])} |"
        )
    macro = report["macro avg"]
    lines.append(
        f"| **macro avg** | {macro['precision']:.2f} | {macro['recall']:.2f} | "
        f"{macro['f1-score']:.2f} | {int(macro['support'])} |"
    )
    lines.append(f"\n**Accuracy:** {report['accuracy']:.2f}")
    return "\n".join(lines)


def main() -> None:
    train_public = pd.read_csv(DATA_DIR / "tickets_train.csv")
    val_public = pd.read_csv(DATA_DIR / "tickets_val.csv")
    test_public = pd.read_csv(DATA_DIR / "tickets_test.csv")

    synthetic = pd.read_csv(DATA_DIR / "synthetic_tickets.csv")
    synth_train, synth_val, synth_test = _split_synthetic(synthetic)

    # Department + priority: public data contributes real volume where it has it
    # (Networking/HR), synthetic data contributes coverage of the other 3 departments.
    dept_priority_train = pd.concat([train_public, synth_train], ignore_index=True)
    dept_priority_test = pd.concat([test_public, synth_test], ignore_index=True)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    sections = []

    dept_model, dept_report = _train_and_evaluate(
        "Department classifier", dept_priority_train, dept_priority_test, "department"
    )
    joblib.dump(dept_model, ARTIFACTS_DIR / "department_classifier.joblib")
    sections.append(
        _report_to_markdown(
            "Department classifier", dept_report, len(dept_priority_train), len(dept_priority_test)
        )
    )

    priority_model, priority_report = _train_and_evaluate(
        "Priority classifier", dept_priority_train, dept_priority_test, "priority"
    )
    joblib.dump(priority_model, ARTIFACTS_DIR / "priority_classifier.joblib")
    sections.append(
        _report_to_markdown(
            "Priority classifier", priority_report, len(dept_priority_train), len(dept_priority_test)
        )
    )

    # Sentiment: synthetic-only, the public dataset has no sentiment label to contribute.
    sentiment_model, sentiment_report = _train_and_evaluate(
        "Sentiment classifier", synth_train, synth_test, "sentiment"
    )
    joblib.dump(sentiment_model, ARTIFACTS_DIR / "sentiment_classifier.joblib")
    sections.append(
        _report_to_markdown(
            "Sentiment classifier", sentiment_report, len(synth_train), len(synth_test)
        )
    )

    with (ARTIFACTS_DIR / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(
            {"department": dept_report, "priority": priority_report, "sentiment": sentiment_report},
            f,
            indent=2,
        )

    METRICS_FILE.write_text(
        "# Classification metrics\n\n"
        "Generated by `ai/models/train_classifier.py`. See "
        "[dataset-cleaning.md](dataset-cleaning.md) and [split-strategy.md](split-strategy.md) "
        "for what the training data does and doesn't cover.\n\n" + "\n\n".join(sections) + "\n",
        encoding="utf-8",
    )
    print(f"\nSaved models to {ARTIFACTS_DIR}/ and metrics to {METRICS_FILE}")


if __name__ == "__main__":
    main()
