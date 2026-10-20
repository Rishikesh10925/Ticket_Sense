# Rubric pilot (Week 5): the team labels 30 drafts

Purpose: find where the rubric ([labelling-rubric.md](../labelling-rubric.md)) is
ambiguous *before* outside reviewers see it. These are **pilot labels**: they are never
used as training or evaluation labels, and the 30 items are outside the 600-draft
labelling selection.

## How

1. Open `pilot_v1.csv`. Each row is a ticket, the AI draft (steps with their cited
   passage numbers) and the evidence passages.
2. **Each of you labels every row independently**, without discussing: fill your own
   column (`label_R`, `label_A`, `label_S`) with A, M, R or W.
3. Add reason codes if you used R or W (wrong_source, outdated_source, missing_step,
   invented_step, did_not_address_question, tone, formatting, other).
4. If the rubric did not tell you what to do, write what was unclear in `rubric_problem`.

About 2 minutes per draft, so about an hour each.

## After

Meet for 30 minutes and go through every row where your labels differ. For each
disagreement, decide whether the rubric needs a clearer rule, and record changes as
rubric v1.1 in `docs/labelling-rubric.md` before the reviewer training session.
Agreement on these 30 (and on 30 more labelled the same way) also gives the 60
human-labelled pilot drafts the Week 6 judge check needs.
