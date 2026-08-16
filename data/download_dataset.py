"""Download the public IT-support ticket dataset identified for classification.

See ../docs/dataset-research.md for why this dataset was chosen. Requires the
`kagglehub` package (`pip install kagglehub`); downloads anonymously for this
public dataset, no Kaggle API credentials needed.

Usage:
    python download_dataset.py
"""

import shutil
from pathlib import Path

import kagglehub

DATASET = "tobiasbueck/multilingual-customer-support-tickets"
DEST = Path(__file__).resolve().parent / "raw" / "customer-support-tickets"


def main() -> None:
    cache_path = Path(kagglehub.dataset_download(DATASET))
    DEST.mkdir(parents=True, exist_ok=True)
    for file in cache_path.glob("*.csv"):
        shutil.copy(file, DEST / file.name)
        print(f"copied {file.name} -> {DEST / file.name}")


if __name__ == "__main__":
    main()
