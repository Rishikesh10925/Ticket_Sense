import { useState } from "react";
import Button from "./Button";
import FormField from "./FormField";
import { submitTicketFeedback, ApiError, type FeedbackAction, type Ticket } from "../api/client";

interface ReviewActionsProps {
  token: string;
  ticket: Ticket;
  onDone: () => void;
}

type Mode = "idle" | "editing" | "rejecting";

// Accept / Edit / Reject / Escalate on a drafted ticket — the primary training signal
// for confidence-model retraining going forward (docs/confidence-labelling-guide.md).
// See app/routers/tickets.py's submit_ticket_feedback: edit/reject never overwrite the
// AI's original draft, so what this component sends is the whole record of "what the
// reviewer actually did", not a replacement for the AI's output.
export default function ReviewActions({ token, ticket, onDone }: ReviewActionsProps) {
  const [mode, setMode] = useState<Mode>("idle");
  const [editedReply, setEditedReply] = useState(ticket.ai_draft_reply ?? "");
  const [rejectReason, setRejectReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function act(action: FeedbackAction, details?: { editedReply?: string; rejectReason?: string }) {
    setSubmitting(true);
    setError(null);
    try {
      await submitTicketFeedback(token, ticket.id, action, details);
      setMode("idle");
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit feedback");
    } finally {
      setSubmitting(false);
    }
  }

  if (mode === "editing") {
    return (
      <div className="review-actions">
        <FormField label="Edited reply" htmlFor="edited-reply">
          <textarea
            id="edited-reply"
            rows={6}
            value={editedReply}
            onChange={(e) => setEditedReply(e.target.value)}
          />
        </FormField>
        {error && <p className="form-error">{error}</p>}
        <div className="review-actions-buttons">
          <Button
            disabled={submitting || !editedReply.trim()}
            onClick={() => act("edit", { editedReply })}
          >
            {submitting ? "Saving…" : "Save edit"}
          </Button>
          <Button variant="secondary" disabled={submitting} onClick={() => setMode("idle")}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  if (mode === "rejecting") {
    return (
      <div className="review-actions">
        <FormField label="Rejection reason" htmlFor="reject-reason">
          <textarea
            id="reject-reason"
            rows={3}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
        </FormField>
        {error && <p className="form-error">{error}</p>}
        <div className="review-actions-buttons">
          <Button
            variant="danger"
            disabled={submitting || !rejectReason.trim()}
            onClick={() => act("reject", { rejectReason })}
          >
            {submitting ? "Rejecting…" : "Confirm reject"}
          </Button>
          <Button variant="secondary" disabled={submitting} onClick={() => setMode("idle")}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="review-actions">
      {error && <p className="form-error">{error}</p>}
      <div className="review-actions-buttons">
        <Button disabled={submitting} onClick={() => act("accept")}>
          Accept
        </Button>
        <Button variant="secondary" disabled={submitting} onClick={() => setMode("editing")}>
          Edit
        </Button>
        <Button variant="danger" disabled={submitting} onClick={() => setMode("rejecting")}>
          Reject
        </Button>
        <Button variant="secondary" disabled={submitting} onClick={() => act("escalate")}>
          Escalate
        </Button>
      </div>
    </div>
  );
}
