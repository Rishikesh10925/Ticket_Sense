# Demo storyboard (Week 10)

- Owner: Aashritha. Roadmap Week 10: "demo storyboard"; used for the Week 12 presentation.
- Length: about 8 minutes, three roles, every lane that exists today.
- Facts below come from the repository and the committed results; anything not yet
  decided is marked **To be decided**.

## Before the demo (15 minutes earlier)

1. `docker compose up -d` and `python tasks.py demo` (seeds the demo accounts, password `Demo@123`).
2. Make sure Ollama is running with `qwen2.5:7b-instruct`.
3. Warm up: submit one throw-away ticket and wait for its lane. The first ticket after a
   restart loads every model and takes minutes; later ones take about 6 to 8 seconds
   (median 6.4 s, p90 7.7 s, `docs/results/latency-v2.json`).
4. Open three browser windows (or profiles), one per role.

## Accounts

| Role | Account | Sees |
|---|---|---|
| End user | `customer@demo.local` | `/end-user` |
| Engineer (Networking) | `engineer@demo.local` | `/engineer` |
| Admin | `admin@demo.local` | `/admin/...` |

Per-member engineer accounts also exist for SAP, Cloud and HR (`rishikesh.`, `aashritha.`,
`shivaganesh.engineer@demo.local`).

## Scenes

| # | Time | Who | Screen | Action | Point to make |
|---|---|---|---|---|---|
| 1 | 0:00 | Presenter | Slide | The problem: helpdesk engineers rewrite AI drafts they cannot trust. | Confidence decides who sees a draft, not just whether one exists. |
| 2 | 0:45 | End user | `/end-user` → New ticket | Submit "VPN keeps disconnecting": "My VPN client disconnects every few minutes when I work from home. I already restarted my laptop. How can I fix this?" | One form; the user never sees the AI. |
| 3 | 1:30 | Engineer | `/engineer` | The ticket appears with its lane badge (it went to **assisted** in the Week 9 live check). Filter by lane. | The queue is sorted by what needs a human most. |
| 4 | 2:15 | Engineer | Ticket detail | Show the draft, the cited KB passages, and "Weakest claims: verify these first". Edit one step, accept. | Assisted means "check the weak claims", not "rewrite". |
| 5 | 3:30 | End user | `/end-user` | Submit red-team ticket RT-03 "Proxy error on browser" (text in `data/redteam/injection_v1.jsonl`). | An attachment tries to inject instructions. |
| 6 | 4:15 | Engineer / admin | Ticket detail, `/admin/approvals` | It is **escalated** with its reason (the shift guard: another department matches as well). | Uncertain tickets get no AI draft at all. |
| 7 | 5:00 | Admin | `/admin/analytics` | The lane dashboard: lane mix, acceptance per lane, decision time. | The gate is measurable in production. |
| 8 | 5:45 | Admin | `/admin/error-budget` | Show the certified thresholds. The **fast lane is closed**: no threshold could be certified at a 10% error budget yet. | The system refuses to auto-trust until the statistics allow it. |
| 9 | 6:30 | Presenter | `docs/results/redteam-v3-pipeline.json` | 0 of 40 injection attacks reach an engineer through the full pipeline. | Safety is tested end to end, not per component. |
| 10 | 7:00 | Presenter | `docs/results/figures/` | Risk-coverage and reliability figures. | Results: **To be decided**. The locked-test numbers replace the rehearsal figures once human labels exist. |
| 11 | 7:45 | Presenter | Slide | Limitations and next steps. | Honest close. |

## Fallbacks

- The model server is down or slow: use screenshots of scenes 3, 4 and 6 (**To be taken**
  at the Week 11 dry run).
- A ticket lands in a different lane than planned: say so; the lane depends on the live
  scores, and that is the point of the gate.
- RT-07 "Network slow" is a second escalation example (the draft says the evidence
  cannot answer).

## Open items

- Final slide deck and timings: **To be decided** at the Week 11 dry run.
- Whether to show the fast lane: only if human-label thresholds certify one (Week 10 locked evaluation).
