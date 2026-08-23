# Usability testing: End User submission flow

Week 4 note (Aashritha) on a first round of usability review for the End User
ticket-submission flow (`/end-user`, `frontend/src/pages/EndUserHome.tsx`).

## Honest note on method

The roadmap task calls for testing "with a few outside testers." No outside testers were
available in this working session, so what's here instead is a structured heuristic
walkthrough — actually operating the real, running app end-to-end (through the live
backend and database, the same way the Week 3/4 integration tests were verified) against
a fixed set of task scenarios, evaluated against standard usability heuristics (visibility
of system status, error prevention, recognition over recall). This is a reasonable
stand-in for a first pass, but it is **not a substitute for real outside testers** —
see "Next round" below for what a proper session needs.

## Task scenarios walked through

1. Submit a ticket with no attachment.
2. Submit a ticket with a `.txt` attachment.
3. Submit a ticket, then immediately check "My tickets" before classification finishes.
4. Try to submit with an empty subject or description.
5. Log in, submit, log out, log back in and check the ticket is still there.

## Findings

| # | Finding | Severity | Heuristic violated |
|---|---|---|---|
| 1 | After submitting, "My tickets" shows the new ticket with status `submitted` and no department/priority yet — correct, but there's no visual cue (spinner, "classifying..." label) that a background process is about to update it. A user has to know to refresh or wait. | Medium | Visibility of system status |
| 2 | The ticket list doesn't auto-refresh — a ticket that gets classified/routed while the page is open stays showing `submitted` until the user navigates away and back. | Medium | Visibility of system status |
| 3 | No confirmation message after a successful submit beyond the form clearing itself — easy to miss, especially if "My tickets" is scrolled out of view. | Low | Visibility of system status |
| 4 | Required-field validation (`subject`, `description`) only shows the browser's native "please fill out this field" tooltip — no in-app styling consistent with the rest of the error states (`.form-error`, used elsewhere for submit failures). | Low | Consistency |
| 5 | The attachment input accepts `image/*,.pdf,.log,.txt` but a user picking an unsupported file only finds out after clicking Submit and getting a 415 error from the backend — the file picker itself doesn't filter as tightly as the accept list suggests on all browsers. | Low | Error prevention |
| 6 | Login and register share one screen with a text-link toggle — functional, but a first-time user landing on `/login` has no visual cue that registration is even possible until they read the small link below the form. | Low | Recognition over recall |

## What's already good

- The static-form → real-API rewrite (Week 3) means the flow now reflects real latency
  and real errors, not a simulated one — testing it means testing the actual system.
- Ticket rows in "My tickets" are clickable through to a detail view (added this week),
  so a user checking on a ticket doesn't have to guess or contact anyone.
- Error messages from the API (e.g. wrong password, unsupported attachment type) surface
  directly rather than being swallowed.

## Recommendations (not implemented this week — findings only)

- Poll or refresh the ticket list a few seconds after submission so classification
  results appear without a manual reload (addresses #1, #2).
- Add a brief inline success confirmation on submit (addresses #3).
- Replace native validation tooltips with the existing `.form-error` styling (addresses #4).
- Client-side file-type check before allowing Submit, not just after the request fails (addresses #5).

## Next round

A real round with outside testers (not team members) is still needed — this pass can
only catch what's inconsistent or missing relative to the app's own stated behavior, not
what's genuinely confusing to someone seeing TicketSense for the first time. Recommend:
3–5 testers unfamiliar with the project, given the task scenarios above plus a cold-start
task ("submit a ticket about a problem you're currently having, without being told what
fields mean"), observed rather than guided.
