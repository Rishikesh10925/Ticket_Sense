"""Clean and structure the raw Kaggle dataset into TicketSense's schema.

Maps the dataset's `queue` field onto TicketSense's department taxonomy, keeps
`priority` as-is (values already match `low`/`medium`/`high`), and drops rows
that don't map onto a target department or aren't English. See
../docs/dataset-cleaning.md for the mapping rationale and its limitations.

Usage:
    python clean_dataset.py
"""

import csv
from pathlib import Path

RAW_FILE = (
    Path(__file__).resolve().parent
    / "raw"
    / "customer-support-tickets"
    / "aa_dataset-tickets-multi-lang-5-2-50-version.csv"
)
OUT_FILE = Path(__file__).resolve().parent / "processed" / "tickets_clean.csv"

# Only queues with a defensible 1:1 or near-1:1 mapping onto a target department
# are kept. SAP, Cloud, and Database have no matching queue in this dataset at
# all (see docs/dataset-cleaning.md) — every other queue is dropped rather than
# guessed at.
QUEUE_TO_DEPARTMENT = {
    "Human Resources": "HR",
    "IT Support": "Networking",
    "Technical Support": "Networking",
    "Service Outages and Maintenance": "Networking",
}

OUT_FIELDS = ["subject", "description", "department", "priority", "sentiment", "language"]


def main() -> None:
    if not RAW_FILE.exists():
        raise SystemExit(f"{RAW_FILE} not found — run download_dataset.py first")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    kept = 0
    dropped_language = 0
    dropped_queue = 0

    with RAW_FILE.open(encoding="utf-8", newline="") as src, OUT_FILE.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=OUT_FIELDS)
        writer.writeheader()

        for row in reader:
            if row.get("language") != "en":
                dropped_language += 1
                continue

            department = QUEUE_TO_DEPARTMENT.get(row.get("queue", ""))
            if department is None:
                dropped_queue += 1
                continue

            writer.writerow(
                {
                    "subject": row["subject"],
                    "description": row["body"],
                    "department": department,
                    "priority": row["priority"],
                    # Not present in the source dataset — see docs/dataset-cleaning.md.
                    "sentiment": "",
                    "language": row["language"],
                }
            )
            kept += 1

    print(f"kept {kept} rows -> {OUT_FILE}")
    print(f"dropped {dropped_language} non-English rows, {dropped_queue} unmapped-queue rows")


if __name__ == "__main__":
    main()
