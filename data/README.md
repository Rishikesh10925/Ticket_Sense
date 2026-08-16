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

No department/priority/sentiment remapping or import-to-database script exists yet —
that's Week 2+ scope once the database schema is defined.
