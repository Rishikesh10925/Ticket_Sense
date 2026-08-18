# Dataset cleaning and structuring

Week 2 note (Shivaganesh) on cleaning the public dataset identified in
[dataset-research.md](dataset-research.md) into TicketSense's schema
(`department`, `priority`, `sentiment` — matching `backend/app/models/ticket.py`).
Run via `data/clean_dataset.py`.

## What the script does

1. Reads the combined raw file (`aa_dataset-tickets-multi-lang-5-2-50-version.csv`,
   28,587 rows — downloaded by `data/download_dataset.py`).
2. Keeps only `language == "en"` rows (12,249 German rows dropped).
3. Maps the dataset's `queue` field onto a TicketSense department using a fixed table,
   dropping any row whose queue isn't in it.
4. Renames `body` → `description`, keeps `subject` and `priority` as-is (priority values
   already are `low`/`medium`/`high`, matching the `ck_tickets_priority` constraint).
5. Writes the result to `data/processed/tickets_clean.csv` (gitignored — regenerate with
   the script rather than committing it).

## Queue → department mapping

| Dataset `queue` | → | TicketSense department | Confidence |
|---|---|---|---|
| Human Resources | → | HR | High — direct match |
| IT Support | → | Networking | Low — see limitation below |
| Technical Support | → | Networking | Low — see limitation below |
| Service Outages and Maintenance | → | Networking | Low — see limitation below |
| *(Customer Service, Product Support, Billing and Payments, Returns and Exchanges, Sales and Pre-Sales, General Inquiry)* | | dropped | — |

## Result

```
kept 7,691 rows
dropped 12,249 non-English rows, 8,647 unmapped-queue rows
```

| Department | Rows |
|---|---|
| Networking | 7,343 |
| HR | 348 |
| SAP | 0 |
| Cloud | 0 |
| Database | 0 |

## Known limitations (not solved this week)

- **Three of five target departments have zero real examples.** This is a general
  customer-support dataset, not an enterprise SAP/infrastructure helpdesk — it has
  nothing resembling SAP transaction errors, cloud infrastructure tickets, or database
  administration requests. Flagged already in `dataset-research.md`; confirmed here by
  actually running the mapping rather than assumed. SAP/Cloud/Database classifier
  training data will have to come from elsewhere (most plausibly synthetic tickets
  generated alongside the knowledge-base articles, per the project blueprint) — not
  attempted this week.
- **The "Networking" mapping is a rough proxy, not a confident label.** `IT Support`,
  `Technical Support`, and `Service Outages and Maintenance` are generic technical-support
  queues in the source data; they likely contain a mix of what TicketSense would actually
  route to Networking vs. Cloud vs. other departments. Mapping all three to Networking
  was a deliberate simplification to get *a* usable department signal rather than
  discarding 92% of the mappable English rows — worth revisiting once real ticket text
  can be spot-checked against what a Networking engineer vs. a Cloud engineer would
  actually expect to see.
- **`department` is heavily imbalanced** (7,343 Networking vs. 348 HR, nothing else) —
  relevant to [split-strategy.md](split-strategy.md) and to future classifier training,
  where this imbalance needs explicit handling (class weighting or resampling), not
  ignored.
- **`sentiment` remains unset.** As documented in `dataset-research.md`, this dataset has
  no sentiment field; `tickets_clean.csv` carries an empty `sentiment` column as a
  placeholder rather than a fabricated label. Sourcing or deriving sentiment labels is
  unresolved.
