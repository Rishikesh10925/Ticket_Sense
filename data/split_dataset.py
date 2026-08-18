"""Split the cleaned dataset into train/validation/test sets.

70/15/15, stratified by department so both classes currently present (HR,
Networking — see docs/dataset-cleaning.md) are represented proportionally in
every split. See ../docs/split-strategy.md for the full rationale.

Usage:
    python split_dataset.py
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 42
IN_FILE = Path(__file__).resolve().parent / "processed" / "tickets_clean.csv"
OUT_DIR = Path(__file__).resolve().parent / "processed"


def main() -> None:
    if not IN_FILE.exists():
        raise SystemExit(f"{IN_FILE} not found — run clean_dataset.py first")

    df = pd.read_csv(IN_FILE)

    train_df, temp_df = train_test_split(
        df, test_size=0.30, random_state=SEED, stratify=df["department"]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=SEED, stratify=temp_df["department"]
    )

    for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        out_path = OUT_DIR / f"tickets_{name}.csv"
        split_df.to_csv(out_path, index=False)
        print(f"{name}: {len(split_df)} rows -> {out_path}")
        print(split_df["department"].value_counts().to_dict())


if __name__ == "__main__":
    main()
