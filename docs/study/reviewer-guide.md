# Reviewer guide (for outside reviewers)

Owner: Aashritha. Hand this to every reviewer before the 45-minute training session.
It summarises the [labelling rubric](../labelling-rubric.md) (v1 after the Week 5 pilot).

## What you are doing

You will read short IT or HR support tickets and an AI-written reply (a "draft") for
each. Your job is to judge whether a support engineer could send that draft. You are not
grading the AI's writing style. You are deciding whether it would actually help the
person, and whether it could do harm.

Everything you see is synthetic: invented tickets, an invented company, invented
policies. There is no real personal data.

## How long it takes

About two minutes per draft; about 125 drafts in total over two weeks, at your own pace.
Stop whenever you like; your place is saved.

## Logging in

You will receive an account for the labelling tool. Open it, sign in, and you land
straight on the next draft. You cannot see anything else in the system, and you don't
need to.

## The screen

1. **Ticket**: what the user wrote, sometimes with a pasted log.
2. **AI draft**: numbered steps. `[1]`, `[2]` point to the evidence passages.
3. **Cited evidence**: the passages the AI was given. Judge the draft against these.
4. **Your label**, optional reasons and note, then **Save & next**.

The timer is just for us to know how long labelling takes. Do not rush because of it.

## The four labels

| Key | Label | Use it when |
|---|---|---|
| 1 | **A: Acceptable** | It is correct, and you would send it as is |
| 2 | **M: Minor edit** | It is correct, but needs under two minutes of fixes to wording, order or formatting |
| 3 | **R: Major rework** | Key steps are missing or wrong; rewriting would be faster than fixing |
| 4 | **W: Wrong or unsafe** | It could mislead or cause harm, or it is based on an irrelevant source |

### Four things that always mean R or W

1. A risky command or setting (data loss, outage, security) that is not in the evidence.
2. A policy statement (leave, access, approvals) that contradicts or is missing from the evidence.
3. An invented meaning for an error code or message.
4. A confident answer when the information needed to answer is missing.

### When the evidence cannot answer the ticket

Sometimes the evidence simply does not cover the question. Then the **right** draft says
so, asks for more information, or hands over to an engineer. Such a draft is **A** or
**M**. A draft that answers anyway is **R** or **W**.

## A good habit, in five steps

1. Read the ticket. What does the person actually need?
2. Read the draft. Does it address *that*?
3. Check each step against the cited evidence.
4. Any of the four "always R or W" problems? Then choose R or W.
5. Otherwise: send as is (A), two-minute touch-up (M), or rewrite (R).

## What you will never see, on purpose

The AI's own confidence, which system produced the draft, or how other reviewers
labelled it. Please don't try to guess; label what is in front of you.

## Skipping

If a ticket is unreadable or makes no sense, press **Skip: unreadable**. That is a
valid answer, not a failure.

## Questions

Ask in the reviewers' chat at any time. If the rubric seems unclear on a case, add a
note. We review notes daily and may clarify the rubric (changes are versioned and
announced).

Thank you for helping. You will be acknowledged in the project report if you wish.
