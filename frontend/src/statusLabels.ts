// Friendlier status text for ticket screens. The end_user's ticket-status views
// especially benefited from this — "drafted" on its own doesn't tell someone who
// never sees the AI draft (see app/schemas/tickets.py's build_ticket_out) what's
// actually happening; "Draft in review" does.
export const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  classified: "Classifying…",
  routed: "Routed to team",
  drafted: "Draft in review",
  reviewed: "Reviewed",
  closed: "Closed",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}
