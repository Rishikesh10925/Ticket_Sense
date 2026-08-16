# Dataset research

Week 1 research note (Shivaganesh) identifying the public IT-support ticket dataset used
for training and evaluating the classification model, per
[docs/architecture.md](architecture.md)'s data flow. No classification model exists yet —
this is the dataset identification and acquisition step only.

## Chosen dataset

**[Customer IT Support - Ticket Dataset](https://www.kaggle.com/datasets/tobiasbueck/multilingual-customer-support-tickets)**
by Tobias Bueck, on Kaggle (also mirrored on
[Hugging Face](https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets)).

- **License:** CC-BY-NC-4.0 (non-commercial, attribution required) — acceptable for this
  academic capstone; the raw data must not be redistributed for commercial use.
- **Size:** the combined file (`aa_dataset-tickets-multi-lang-5-2-50-version.csv`) has
  28,587 rows; smaller pre-split files are also included in the same download.
- **Languages:** English (16,338 rows) and German (12,249 rows) in the combined file.
- **Columns:** `subject`, `body`, `answer`, `type`, `queue`, `priority`, `language`,
  `tag_1`…`tag_8`.
- **Verified locally** by downloading the dataset (`data/download_dataset.py`,
  anonymous — no Kaggle API credentials required for this public dataset) and inspecting
  it directly rather than trusting the listing description alone.

### Relevant field distributions (combined file, all languages)

`priority` (3 values):

| Value | Count |
|---|---|
| medium | 11,515 |
| high | 11,178 |
| low | 5,894 |

`queue` (10 values):

| Value | Count |
|---|---|
| Technical Support | 8,362 |
| Product Support | 5,252 |
| Customer Service | 4,268 |
| IT Support | 3,433 |
| Billing and Payments | 2,788 |
| Returns and Exchanges | 1,437 |
| Service Outages and Maintenance | 1,148 |
| Sales and Pre-Sales | 918 |
| Human Resources | 576 |
| General Inquiry | 405 |

## Why this dataset

- It is the only IT-support-flavored dataset found (see "Alternatives considered" below)
  that has **both** a department-style routing field (`queue`) and a `priority` label on
  real ticket text — two of the three classification targets in
  [docs/architecture.md](architecture.md), without needing to stitch together multiple
  sources.
- `Human Resources` maps directly onto TicketSense's HR department; `IT Support`,
  `Technical Support`, and `Service Outages and Maintenance` are reasonable sources of
  Networking/Cloud-flavored tickets.
- It was independently re-derived and cross-checked against an earlier, since-removed
  prototype's `data/README.md` (recovered from git history), which had identified the
  same dataset for the same reason — convergent evidence this is the right choice rather
  than an arbitrary pick.

### Known gaps (deferred, not solved this week)

- **No `sentiment` label.** The classifier's third target (sentiment) isn't present in
  this dataset and will need either a separate labeled source or a lightweight labeling
  pass — not attempted this week.
- **`queue` doesn't map 1:1 onto the project's five departments** (SAP, Networking,
  Cloud, Database, HR — see [knowledge-base-outline.md](knowledge-base-outline.md)).
  There is no SAP or Database category in this dataset at all, since it's a general
  customer-support dataset, not an enterprise SAP/infrastructure helpdesk. The queue →
  department remapping (and how to backfill SAP/Database examples, likely from the
  synthetic knowledge-base-linked tickets described in the project blueprint) is a Week 2
  task, not resolved here.
- Only `language == "en"` rows are likely usable without adding a translation step.

## Alternatives considered

| Dataset | Why not chosen |
|---|---|
| [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) (47.8k rows) | Has enterprise-IT-flavored categories (Hardware, HR Support, Access, Storage, Purchase, Internal Project, Administrative rights) but no `priority` field — would need a second dataset for priority. |
| [IT Support Tickets (synthetic)](https://www.kaggle.com/datasets/ahsanneural/synthetic-it-support-tickets) (100k rows) | Has priority *and* sentiment, but is fully synthetic SaaS-helpdesk data with no real department/routing field — weaker for the classification target that matters most for TicketSense's routing (department). |
| [Support Ticket Priority Dataset (50K)](https://www.kaggle.com/datasets/albertobircoci/support-ticket-priority-dataset-50k) | Priority-only, no department/queue field. |

## How to obtain it

```bash
pip install kagglehub
python data/download_dataset.py
```

Downloads the dataset's CSVs into `data/raw/customer-support-tickets/` (gitignored — the
dataset itself is not committed to the repository, consistent with its license and
normal practice for a 25MB+ third-party dataset). Re-run any time to refresh the local
copy; `kagglehub` caches the download under `~/.cache/kagglehub`.
