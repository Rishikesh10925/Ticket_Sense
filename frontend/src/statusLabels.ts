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
  escalated: "Escalated",
  closed: "Closed",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

// pages.css has per-status accent colors (status-drafted, status-reviewed, ...) so the
// queue/list reads at a glance instead of every status looking the same neutral gray.
export function statusBadgeClass(status: string): string {
  return `status-badge status-${status}`;
}
