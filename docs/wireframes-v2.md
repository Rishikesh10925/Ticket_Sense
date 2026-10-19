# Wireframes v2 (Week 1)

Owner: Aashritha. Supersedes [wireframes.md](wireframes.md) for the V2 screens. Built
against the [API contract](api-contract.md). Low fidelity on purpose: these fix *what* is
on each screen and *where*, not the styling (that stays on the existing design tokens,
ADR 004).

Design rules that come from the blueprint, not taste:

- A human always decides. No screen sends anything to a customer without an engineer's action.
- End users never see drafts, evidence, scores or lanes (Week 9 leak fix stays).
- Annotators never see the score, lane or signals (blinding, Blueprint §11.6).
- The lane controls **how** a draft is shown, not **whether** a human looks.

## 1. Ticket form (end user)

```
+---------------------------------------------------------------+
| New ticket                                                    |
|                                                               |
| Subject     [ VPN stuck on "Connecting" at the hotel        ] |
| Description [ Since this morning the client hangs...         ]|
|             [                                                ]|
| Attachment  [ Choose .txt or .log file ]  app_error.log (4 KB)|
|             Plain text and logs only. Max 10 MB.              |
|                                                               |
|                                         [ Submit ticket ]     |
+---------------------------------------------------------------+
| My tickets                                                    |
|  T-1042  VPN stuck on "Connecting"   In review     2 min ago  |
|  T-1037  Payslip not visible         Replied       yesterday  |
+---------------------------------------------------------------+
```

States: submitting, validation error (empty subject, bad file type), submitted.

## 2. Engineer queue

```
+----------------------------------------------------------------------------+
| Networking queue           Lane: [All v]  Status: [Open v]  Sort: [Age v]  |
+------+-------------------------------+-----------+----------+--------------+
| ID   | Subject                       | Lane      | Priority | Waiting      |
+------+-------------------------------+-----------+----------+--------------+
| 1042 | VPN stuck on "Connecting"     | ● FAST    | high     | 2 min        |
| 1040 | DNS fails for intranet names  | ◐ ASSIST  | medium   | 9 min        |
| 1039 | Something wrong with network  | ○ ESCAL.  | low      | 15 min       |
+------+-------------------------------+-----------+----------+--------------+
```

Lane badges use shape **and** colour (●, ◐, ○) so they work for colour-blind users.

## 3. Review workbench, one layout per lane

### Fast lane: pre-filled draft, one-click accept

```
+-------------------------------------------+--------------------------------+
| T-1042  VPN stuck on "Connecting"  ● FAST | Evidence                        |
| Ticket text ...                           | [1] NET-VPN-001 §Resolution     |
|-------------------------------------------|     "...try a mobile hotspot..."|
| Draft reply (editable)                    | [2] NET-VPN-002 §Cause          |
| 1. Load a public website to check... [1]  |                                 |
| 2. Retry from a mobile hotspot...    [1]  | Why this lane                   |
|                                           |  strong retrieval match         |
| [ Accept & send ]  [ Edit ]  [ Reject ]   |  all claims supported           |
|                          [ Escalate v ]   |                                 |
| timer 00:41                               |                                 |
+-------------------------------------------+--------------------------------+
```

### Assisted lane: draft marked "verify", weakest claims highlighted

```
+-------------------------------------------+--------------------------------+
| T-1040  DNS fails...             ◐ ASSIST | Evidence                        |
| ⚠ Verify before sending                   | [1] NET-DNS-001 ...             |
|-------------------------------------------| [2] NET-DNS-003 ...             |
| Draft reply (editable)                    |                                 |
| 1. Flush the DNS cache...            [1]  | Weakest claims                  |
| 2. ░Check the split-DNS rule░        [2]  |  ░ "split-DNS rule" 0.31        |
|    ↑ low support, check against [2]       |  ░ step 4           0.44        |
| [ Accept & send ] [ Edit ] [ Reject ]     |  ░ step 5           0.52        |
|            [ Escalate v ]  reasons [v]    |                                 |
+-------------------------------------------+--------------------------------+
```

### Escalation lane: no AI draft at all

```
+-------------------------------------------+--------------------------------+
| T-1039  Something wrong with... ○ ESCAL.  | Ranked evidence (no draft)      |
| No AI draft: not enough reliable evidence | [1] NET-WIFI-002 ...            |
| (the model said it cannot answer)         | Similar resolved tickets        |
|-------------------------------------------|  T-0871 "Wi-Fi drops in B2"     |
| Your reply                                |                                 |
| [                                       ] |                                 |
| [ Send reply ]   [ Ask user for info ]    |                                 |
+-------------------------------------------+--------------------------------+
```

Every action records the action, final text, reason codes and time taken
(`POST /tickets/{id}/review`).

## 4. Annotation tool (outside reviewers, blinded)

```
+--------------------------------------------------------------------------+
| Labelling   23 / 100 done        rubric v1 (open in new tab)    ⏱ 01:12  |
+--------------------------------------------------------------------------+
| Ticket                                                                   |
|   "SAP shows ME023 when I post goods receipt for PO 4500012"             |
| AI draft                                                                 |
|   1. ME023 means ... [1]                                                 |
| Cited evidence                                                           |
|   [1] SAP-PO-002 §Cause "..."                                            |
+--------------------------------------------------------------------------+
| Label   ( ) A Acceptable  ( ) M Minor edit  ( ) R Major rework  ( ) W Wrong |
| Reasons [ ] wrong source [ ] missing step [ ] invented step [ ] other ... |
| [ Skip: unreadable ]                                 [ Save & next → ]   |
+--------------------------------------------------------------------------+
```

No score, lane, model name or signal anywhere on this screen. Drafts arrive shuffled.
Double-annotation assignments look identical to the reviewer.

## 5. Admin: error budgets and expected coverage

```
+--------------------------------------------------------------------------+
| Error budgets                                     threshold version v3   |
|                                                                          |
| Fast lane    α  [ 0.10 ]  →  threshold 0.87   expected coverage 38%      |
| Assisted     α  [ 0.40 ]  →  threshold 0.52   expected coverage 71%      |
| Confidence   δ  [ 0.10 ]  (chance the guarantee fails)                   |
|                                                                          |
| Coverage vs α (calibration split)                                        |
|   cov │        ____-----                                                 |
|       │    __--                                                          |
|       │__--                                                              |
|       └──────────────── α                                                |
| ⓘ Holds only while new tickets resemble the calibration set.             |
|                                     [ Recompute ]  [ Apply as v4 ]       |
+--------------------------------------------------------------------------+
```

Thresholds are never typed in by hand: the admin picks α and δ, and the Learn-then-Test
step (`ai/evaluation/risk_control.py`) sets the thresholds.
