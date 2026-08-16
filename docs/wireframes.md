# Low-fidelity wireframes

Week 1 wireframe sketches (Aashritha) for the three TicketSense screens, informed by the
patterns in [ui-research.md](ui-research.md). These are layout sketches only — no visual
design, styling, or component implementation yet.

## End User — submit a ticket

```text
┌─────────────────────────────────────────────────────────┐
│ TicketSense                                    [Logout]  │
├─────────────────────────────────────────────────────────┤
│  New ticket                                               │
│                                                             │
│  Subject       [_______________________________________]  │
│                                                             │
│  Description   [_______________________________________]  │
│                [_______________________________________]  │
│                [_______________________________________]  │
│                                                             │
│  Attachment    [ 📎 Drag a file here or click to upload ]  │
│                                                             │
│  Department    ( suggested once submitted — override ▾ )  │
│                                                             │
│                                        [ Submit ticket ]   │
├─────────────────────────────────────────────────────────┤
│  My tickets                                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ #1042  ME023 error on PO creation      [In review]  │  │
│  │ #1039  VPN not connecting from home    [Resolved]   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Department Engineer — review workspace

```text
┌───────────────┬─────────────────────────────────────────┐
│ Queue          │ Ticket #1042                             │
│ [Priority ▾]   │ ME023 error on PO creation                │
│ [Status ▾]     │ From: user@company.com · SAP · High        │
│                │                                            │
│ ● #1042  High  │ ── Ticket ─────────────────────────────── │
│   #1044  Med   │ "Unable to generate a purchase order..."   │
│   #1051  Low   │                                            │
│   #1053  Med   │ ── Retrieved evidence (internal) ────────  │
│                │ [1] KB: me023-error-goods-receipt.md        │
│                │ [2] Resolved ticket #872 (similar)          │
│                │                                            │
│                │ ── AI draft (internal) ───────────────────  │
│                │ Confidence: 0.81  [above threshold]         │
│                │ "This error occurs when... [1][2]"          │
│                │                                            │
│                │ [ Accept ] [ Edit ] [ Reject ] [ Escalate ] │
└───────────────┴─────────────────────────────────────────┘
```

## Admin — manage

```text
┌───────────────┬─────────────────────────────────────────┐
│ Sections       │ Users                                    │
│                │                                            │
│ ● Users        │ ┌────────────────────────────────────┐   │
│   Departments  │ │ Name       Role       Department    │   │
│   Knowledge    │ │ A. Reddy   Engineer   SAP            │   │
│   base         │ │ S. Ganesh  Engineer   Cloud          │   │
│   Analytics    │ │ R. K.      Admin      —              │   │
│   Settings     │ └────────────────────────────────────┘   │
│                │                                            │
│                │                          [ + Add user ]   │
└───────────────┴─────────────────────────────────────────┘
```

## Notes

- All three screens share the same left-nav/header shell — the app frame is common,
  only the content area changes per role, matching a single role-aware `Shell` component
  rather than three separate layouts.
- The Engineer and Admin screens both use the list+detail split identified in
  [ui-research.md](ui-research.md); the End User screen is single-column since there is
  no queue to triage, only a submission form and a personal ticket history.
- Confidence score and retrieved evidence are explicitly marked "internal" in the
  Engineer view — they must never render on the End User screen.
