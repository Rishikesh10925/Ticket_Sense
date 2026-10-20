# Groundedness audit (Week 6)

> **Short version (use this):** `audit_v1_R_short.csv`, `audit_v1_A_short.csv`,
> `audit_v1_S_short.csv`, about 40 claims each instead of about 165. Two automatic
> checkers (NLI and an LLM check) judge every claim first; you label every claim where
> they disagree plus a random sample of the ones where they agree, so the audit still
> measures how often both are wrong together. Same rules as below; label in
> `audit_tool.html`. Which rows are "doubtful" is deliberately not shown.


Why: the NLI claim checker decides which claims count as "supported". Before its
scores feed the confidence model, a human checks it on 100 drafts so its errors are
known (Blueprint V2 §12.3). The Week 6 gate asks that "audit agreement is understood
and acceptable".

## Your file

| Member | Worksheet |
|---|---|
| Rishikesh | `audit_v1_R.csv` |
| Aashritha | `audit_v1_A.csv` |
| Shivaganesh | `audit_v1_S.csv` |

Each row is one claim from a draft, with the passage(s) the draft cited for it.
Open the CSV in Excel or Google Sheets.

## What to fill in

In the `human` column write exactly one of:

- `supported`: everything the claim says is stated in, or directly follows from, the
  cited passage. Rewording is fine.
- `not_supported`: the claim adds a command, setting, value, condition or step the
  cited passage does not contain, or contradicts it.
- `unclear`: you cannot decide (say why in `note`).

Judge **only against the cited passage**, not against what you know is true and not
against other passages. The checker's own score is deliberately hidden so it does not
influence you.

About 160 claims each, roughly 1.5 to 2 hours. Do not edit the other columns.

## After

Commit your filled CSV. `audit_sample_v1.json` holds the checker's scores; agreement
(accuracy, false-supported and false-unsupported rates, per support band) is computed
from it and reported in the Week 6 logbook.
