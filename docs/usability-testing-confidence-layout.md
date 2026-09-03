# Usability testing: evidence + draft + confidence combined layout

Week 8 note (Aashritha) — first usability pass on the Department Engineer's ticket
detail screen now that it shows retrieved evidence, the AI draft, and the confidence
indicator together (`frontend/src/pages/TicketDetail.tsx`). Same honest method as
[usability-testing.md](usability-testing.md): no outside testers were available this
session, so this is a structured heuristic walkthrough of the real, running app — not
a substitute for a real outside-tester round (still open, see that doc's "Next round").

## Task scenarios walked through

1. Log in as `engineer@demo.local`, open a routed+drafted ticket, read the combined
   evidence/draft/confidence layout cold (no prior context).
2. Compare a high-confidence ticket (Networking, well above its department's threshold)
   against a deliberately misrouted one (see [team-integration-week6.md](team-integration-week6.md)'s
   finding) to see whether the layout communicates the difference.
3. As Admin, open the Departments tab and change a threshold, with no other context
   about what effect it has.

## Findings

| # | Finding | Severity | Heuristic violated |
|---|---|---|---|
| 1 | The confidence panel sits above the draft text, inside the same card — a reviewer sees "how much to trust this" before "what it says," which is the right order, and wasn't a deliberate layout decision worth re-litigating, just confirming it reads correctly. | — (positive finding) | — |
| 2 | Nothing in the confidence feature breakdown links back to *which* evidence item drove `ticket_resolution_similarity` or `retrieval_relevance` — a reviewer sees "Resolution similarity: 92%" but has to infer which of the 5 evidence cards on the left that corresponds to, since the evidence panel doesn't highlight or rank-order to match. | Medium | Recognition over recall |
| 3 | `category_risk` is the one feature bar where a *full* bar is bad news (it's a risk score, not a confidence score) and every other bar reads the opposite way — the bar is colored differently (amber vs. indigo) to signal this, but there's no label or tooltip saying so explicitly. A reviewer unfamiliar with the feature set could misread a low, amber-colored bar as a problem when it's actually the good outcome (low risk). | Medium | Recognition over recall / consistency |
| 4 | The score badge and "Above/Below threshold" label communicate the gate outcome, but nothing explains *why* in plain language — a reviewer has to read all 5 raw feature percentages and reconstruct the reasoning themselves. No synthesized explanation ("scored low mainly because this department's classifier is unreliable") exists yet. | Low | Visibility of system status |
| 5 | The admin threshold editor's Save button has no confirmation message on success — it simply goes from enabled back to disabled, the same "did that actually work?" gap already flagged for ticket submission in Week 4's finding #3. | Low | Visibility of system status |
| 6 | Once an admin starts editing a threshold, there's no explicit "cancel" — reverting an accidental edit means reloading the whole page, not just that row. | Low | User control and freedom |
| 7 | The Departments tab explains what the threshold *will* do ("tickets... are escalated... once the Week 9 gate is wired in") directly under the table, which is honest about current scope — but it's easy to miss since it's a small note below a table, not near the input itself. | Low | Visibility of system status |

## What's already good

- The side-by-side evidence/draft layout (Week 6) held up under this heavier load —
  adding the confidence panel didn't require restructuring it, just inserting a section
  inside the existing draft card.
- Hiding the confidence panel entirely for the end_user role (rather than showing a
  disabled/placeholder version) avoids a "why can't I see this" dead end — there's
  simply nothing there to be confused about, consistent with how the draft panel itself
  is already hidden.
- The amber vs. indigo bar-color distinction for `category_risk` (finding #3) is at
  least a real signal, not purely decorative — a reviewer who does know the convention
  can tell the inverted feature apart at a glance without reading labels.

## Recommendations (not implemented this week — findings only)

- Rank or number the evidence list to match citation order, and consider a subtle
  visual tie between `ticket_resolution_similarity` and whichever evidence card it came
  from (addresses #2).
- A one-line legend or hover tooltip on the `category_risk` bar clarifying "lower is
  better" (addresses #3).
- A short synthesized reason string alongside the score once there's a real (not stub)
  LLM available to generate one cheaply (addresses #4) — out of scope while
  `StubLLMProvider` is the only provider.
- A brief "Saved" confirmation and a "Cancel" affordance in the threshold editor
  (addresses #5, #6).

## Next round

Still needs real outside testers, per [usability-testing.md](usability-testing.md)'s
existing "Next round" note — this pass, like that one, can only catch what's
inconsistent relative to the app's own stated behavior, not what's genuinely confusing
to someone seeing the confidence panel for the first time with no context on what a
confidence model even is.
