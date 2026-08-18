# data/

## download_dataset.py

Downloads the public IT-support ticket dataset identified for the classification model.
See [../docs/dataset-research.md](../docs/dataset-research.md) for why this dataset was
chosen, its structure, license, and known gaps.

```bash
pip install kagglehub
python download_dataset.py
```

Saves CSVs to `raw/customer-support-tickets/` (gitignored — not committed, per the
dataset's CC-BY-NC-4.0 license and its size). Re-run any time to refresh.

## clean_dataset.py

Maps the raw dataset's `queue` field onto TicketSense's department taxonomy and writes
`processed/tickets_clean.csv` (gitignored — reproducible from the raw data). See
[../docs/dataset-cleaning.md](../docs/dataset-cleaning.md) for the mapping and its
limitations (only 2 of 5 departments currently have real examples).

```bash
python clean_dataset.py
```

## split_dataset.py

Splits `processed/tickets_clean.csv` into stratified 70/15/15 train/val/test CSVs. See
[../docs/split-strategy.md](../docs/split-strategy.md).

```bash
python split_dataset.py
```

No import-to-database script exists yet — that's later scope once ticket ingestion is
wired up.
