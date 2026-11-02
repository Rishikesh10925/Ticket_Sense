# Independent human audit (v1)

Outside reviewers rate AI drafts for acceptability, citation support and relevance. This
follows the "Independent Human Annotation Sampling Protocol" of 31 October 2026. It is
development evidence: it does not replace the 600-draft labelling plan or the sealed test,
and the sealed test is not read.

## Frozen plan

Mode H (hybrid), N = 40, seed 20261102, NLI pass threshold 0.5, drafts `draft-v2`. Counts
and the hash of the hidden manifest are in [plan_v1.json](plan_v1.json), committed before
any rating exists. The manifest itself stays git-ignored until the ratings are in, because
it holds what reviewers must not see; `select` reproduces it from the same seed.

**Eligible pool.** Answering, schema-valid drafts with an evidence packet, from the
validation and unseen-topic splits: 268 drafts in 110 scenarios (A 30, B 9, C1 69, C2 2).
150 drafts were excluded as not answering. Estimates describe this pool only, with type
standing in for its split: all A, B and C2 are validation and all C1 are unseen-topic.

**Why N = 40 with a revised allocation.** The protocol's options use equal counts per type,
and none can be filled, because only 2 C2 scenarios are eligible (even N = 20 needs 3). The
protocol asks for a documented revised allocation before annotation:

| Part | Group | Protocol N = 40 | Used | Eligible scenarios |
|---|---|---|---|---|
| I, random | Type A | 6 | 7 | 30 |
| I, random | Type B | 6 | 7 | 9 |
| I, random | Type C1 | 6 | 8 | 69 |
| I, random | Type C2 | 6 | 2 | 2 |
| II, targeted | NLI-pass suspected errors | 8 | 8 | 14 |
| II, targeted | Judge disagreements | 5 | 5 | 41 |
| II, targeted | Other controls (NLI-rejected) | 3 | 3 (2 judge-accepted, 1 judge-rejected) | 107 |

Rule: equal counts capped at what is available; a capped type's shortfall is shared equally
among the others, and a remainder goes to the type with most scenarios. Population estimates
weight each type by its eligible share, so unequal counts do not bias them, but C2 rests on
2 cases and is not estimated separately. N = 80 is not possible: it needs 16 NLI-pass
suspected errors and only 14 scenarios qualify, before Part I removes any.

Judge disagreements come from a blinded re-grade run only on unseen-topic C1 drafts, so that
group contains only C1. Shortfall rule: none is expected for N = 40; a new case needs a
separately frozen extension.

## Running it

From `backend/`, with the database running:

```bash
python -m app.scripts.human_audit export --reviewers 2     # or 4: two pairs, 20 cases each
python -m app.scripts.human_audit collect ../data/annotation/returned/human_audit_v1/*.xlsx
python -m app.scripts.human_audit adjudication --reviewer HA-09   # blinded pack of disputed cases
```

`export` writes one HTML page per reviewer to `data/annotation/packs/human_audit_v1/`
(git-ignored). The page works offline, shows the ticket, draft, cited passages and rules,
hides type, split, scores, judge labels and sampling group, shuffles the order per reviewer,
and downloads an Excel file. Re-export only before sending: each export gets new pack ids.

`collect` keeps each file as it arrived in `data/annotation/returned/human_audit_v1/`, checks
every answer and required reason, and writes `collect_report.json`: agreement and confusion
counts per pair (Q1, Q2, Q3, binary with its denominator and U count), confirmed findings by
part and group, Part I weighted missing-label bounds, and warnings for very quick answers and
near-identical reasons between a pair's reviewers. Those warnings need a human look before a
file is accepted.

## Reporting limits

Report Part I and Part II separately; Part II is exploratory case evidence and gives no
pooled error rate. With 24 random cases, the type-level numbers are very imprecise. Validation
was involved in developing the model and guard, so it is not an untouched test. Peer review is
not expert certification, and the synthetic references are not all independently fact-checked.
