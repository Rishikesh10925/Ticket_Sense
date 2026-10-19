# Annotation tool: data model and flow (v1 design, Week 3)

Owner: Aashritha. Blueprint V2 §11.6 (labelling protocol), §10.1 (`labels`, `annotators`),
Appendix A ([labelling rubric](labelling-rubric.md)), Appendix C.3 (`/annotate` endpoints).
Wireframe: [wireframes-v2.md §4](wireframes-v2.md). Built in Week 4 (v0) and Week 6 (v1).

## Goals

1. **About 600 human labels** on benchmark drafts, from six or more outside reviewers.
2. **150 drafts labelled twice** (the overlap set), so Cohen's kappa can be computed.
3. **Blinding**: reviewers never see the confidence score, lane, signals or model name.
4. **Shuffled order** per reviewer, so position effects average out.
5. Every label is traceable to a rubric version, and labels are never overwritten.

## Tables

```
annotators
  id               uuid pk
  user_id          uuid fk users (role = 'annotator', unique)
  pseudonym        varchar(16) unique      -- REV-01, REV-02 ... (the only name used in data)
  trained_at       timestamptz null        -- set after the 45-minute training
  active           bool default true

annotation_assignments
  id               uuid pk
  draft_id         uuid fk drafts          -- drafts table arrives in Week 5 (R)
  annotator_id     uuid fk annotators
  batch            varchar(16)             -- pilot | sprint1 | sprint2 | adjudication
  overlap          bool                    -- part of the 150 double-labelled set
  position         int                     -- order shown to this annotator (shuffled)
  served_at        timestamptz null
  completed_at     timestamptz null
  unique (draft_id, annotator_id)

labels
  id               uuid pk
  assignment_id    uuid fk annotation_assignments unique
  label            char(1) check in ('A','M','R','W')
  acceptable       bool generated always as (label in ('A','M')) stored
  reason_codes     text[]                  -- wrong_source, outdated_source, missing_step, ...
  note             text null
  skipped_reason   text null               -- "unreadable"; label then null
  time_taken_ms    int
  rubric_version   varchar(8)              -- v1, v2 ...
  created_at       timestamptz
```

Adjudication: when two overlap labels disagree on `acceptable`, a third reviewer gets an
`adjudication` assignment for the same draft. Their label decides the binary target; all
three stay stored.

## Assignment algorithm

1. Select the 600 drafts to label (stratified by ticket type and department; S, Week 7),
   including all 250 locked-test drafts and 200 calibration drafts.
2. Pick 150 of them as the overlap set, spread evenly over strata.
3. Give each overlap draft to two different reviewers, and every other draft to one,
   balancing load to about 100 single plus about 25 overlap per reviewer.
4. Shuffle each reviewer's list with a seed (recorded) and store it as `position`.
5. Reviewers never learn which of their drafts are in the overlap set.

## What the reviewer sees (`GET /annotate/next`)

```json
{
  "assignment_id": "uuid",
  "progress": {"done": 23, "total": 125},
  "rubric_version": "v1",
  "ticket": {"subject": "...", "body": "...", "attachment_text": null},
  "draft": {"steps": [{"text": "...", "citations": [1]}], "can_answer": true},
  "evidence": [{"n": 1, "title": "...", "text": "..."}]
}
```

Never included: confidence score, lane, signal values, model name, ticket type, gold
article, or whether the item is in the overlap set.

`POST /annotate/{assignment_id}` takes `{label, reason_codes, note, skipped_reason,
time_taken_ms}`. The server sets `rubric_version` and rejects a second label for the same
assignment.

## Privacy

Reviewer accounts store an email for login only. Every export and report uses the
pseudonym. Reviewers see synthetic tickets only.

## Reports (S and A)

- Progress per reviewer and per batch.
- Cohen's kappa on the overlap set (target at least 0.6; at least 0.5 at the Week 7 checkpoint).
- Judge-human agreement on the 600 labelled drafts.

## v1 status (Week 6)

- Planner: `backend/app/services/assignments.py` (pure, seeded; tested for two distinct
  reviewers per overlap draft, load balanced within one item, shuffled positions, and
  overlap spread over strata).
- Batches: `python -m app.scripts.assign_annotations plan --batch sprint1 --drafts <ids.txt>
  --overlap 150 --seed 2026`. Later batches queue after a reviewer's existing items. The
  seed and counts are written to `data/annotation/<batch>.json`.
- Adjudication: `python -m app.scripts.assign_annotations adjudicate --batch adjud1`
  sends every overlap draft whose two labels disagree on `acceptable` to a third
  reviewer who has not seen it.
- Migration 0017: one assignment per (draft, annotator), enforced by the database.
- Timer, keyboard labels and blinding were already in v0.
