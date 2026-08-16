# UI research: ticket-submission forms and reviewer dashboards

Week 1 research note (Aashritha) on UI patterns from existing ITSM tools, to inform the
End User submission flow and Department Engineer review dashboard. No frontend screens
are built from this yet — this is the pattern research that the wireframes and later
weeks' component work will draw from.

## Tools reviewed

Freshservice, Zendesk (Support + native ticket forms), Jira Service Management, and
ServiceNow's native request/incident forms — all widely used enterprise ITSM products
with public documentation and demo/trial screens.

## Ticket-submission form patterns

- **Single-field-first, progressive disclosure.** Every tool reviewed leads with a short
  subject/summary field and a free-text description, then reveals category-specific
  fields (department, priority, affected system) only after the requester starts typing
  or picks a category — rather than showing a long form upfront. Reduces abandonment on
  a first-touch support form.
- **Category/department picker drives the rest of the form.** Zendesk and Jira Service
  Management both branch the visible fields off an initial "what is this about" choice.
  This maps directly onto TicketSense's department-routing model: the End User form
  should let classification (once built) suggest a department, with the user able to
  override it, rather than forcing a manual picker as the very first step.
- **Attachment upload is a first-class, low-friction control** — drag-and-drop with
  inline thumbnails for images and file-type icons otherwise — never buried behind an
  "Advanced options" toggle. TicketSense's optional image/PDF/log attachment should sit
  directly under the description field, not on a second screen.
- **Immediate confirmation with a ticket reference number**, plus a visible "what happens
  next" line (e.g., expected response time), closes the submission loop and reduces
  duplicate submissions from anxious requesters.

## Reviewer/engineer dashboard patterns

- **List + detail split view**, not a full-page-per-ticket flow. A left-hand queue
  (filterable by status/priority/assignee) next to a detail pane is the dominant layout
  across all four tools — it lets an engineer triage many tickets without a page reload
  per ticket, which matters for TicketSense's Department Engineer role reviewing a queue
  of AI-drafted responses.
- **Status and priority are always visible as compact badges** in the list, colour-coded
  and consistent between list and detail view — never text-only.
- **The response/action area is anchored at the bottom or side of the detail pane**,
  separate from the ticket's historical thread, so the reviewer's in-progress reply is
  never confused with prior conversation. This maps onto TicketSense's
  accept/edit/reject/escalate action being visually distinct from the retrieved-evidence
  and draft-history sections.
- **Internal notes are visually distinguished from customer-facing replies** (typically a
  different background colour) — relevant to TicketSense because the AI-generated draft,
  its citations, and its confidence score are all "internal" context the engineer sees
  but the end user never does.

## Implications for TicketSense wireframes

The patterns above directly informed the three low-fidelity wireframes in
[wireframes.md](wireframes.md):

1. The **End User submission screen** uses progressive disclosure (description first,
   attachment inline, department shown as a suggestion once classification exists).
2. The **Department Engineer workspace** uses the list+detail split, with retrieved
   evidence/citations and the confidence score rendered as internal-only panels distinct
   from the draft reply and the accept/edit/reject/escalate action bar.
3. The **Admin screen** follows the same list+detail convention for consistency, applied
   to users/departments/knowledge-base management instead of tickets.

## References

- Freshservice, Zendesk, Jira Service Management, and ServiceNow product documentation
  and public demo instances (reviewed for layout and interaction patterns only; no
  screenshots or proprietary content reproduced here).
