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

## synthetic_labeled_tickets.py

Writes `processed/synthetic_tickets.csv` — 120 hand-authored tickets, 24 per department,
covering all 5 departments and all 3 classification targets (department/priority/
sentiment), since the public dataset only covers 2 departments and has no sentiment
label at all. See [../docs/classification-model.md](../docs/classification-model.md).

```bash
python synthetic_labeled_tickets.py
```

## seed_synthetic_tickets.py

Inserts the same 120 tickets (from `synthetic_labeled_tickets.py`) into the `tickets`
table as `closed` historical tickets, attributed to a placeholder account
(`synthetic-tickets@ticketsense.local`) — a stand-in resolved-ticket history for the
retrieval pipeline to embed, since no real one exists yet. See
[../docs/retrieval.md](../docs/retrieval.md).

```bash
uv run --project ../backend python seed_synthetic_tickets.py
uv run --project ../backend python seed_synthetic_tickets.py --reset  # replace existing
```

Requires the five departments to already exist
(`backend/app/scripts/seed_demo_users.py`) and `DATABASE_URL` configured.

## make_sample_screenshots.py

Writes the hand-crafted sample "screenshots" in `sample_screenshots/` (five PNGs, one
PDF, one log file) used by `docs/ocr-evaluation.md` and
`backend/tests/test_ocr_extract.py`. No real user screenshots exist for this project,
so these are built with Pillow to resemble real failure modes per department — the
same honest-substitute approach as `synthetic_labeled_tickets.py`. The committed files
in `sample_screenshots/` are the actual test fixtures; re-run this only to regenerate
them.

```bash
pip install fpdf2   # only needed to regenerate the PDF sample
uv run --project ../backend python make_sample_screenshots.py
```

Requires Windows fonts (Segoe UI, Consolas) at the path hardcoded in the script —
adjust `FONT_DIR` if regenerating elsewhere.
