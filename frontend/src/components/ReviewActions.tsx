import { useEffect, useRef, useState } from "react";
import Button from "./Button";
import FormField from "./FormField";
import { CheckIcon, EditIcon, XIcon, ArrowUpRightIcon, QuestionIcon } from "./icons";
import { useToast } from "./Toast";
import {
  submitTicketFeedback,
  ApiError,
  REASON_CODES,
  type FeedbackAction,
  type ReasonCode,
  type Ticket,
} from "../api/client";

const ACTION_TOAST: Record<FeedbackAction, string> = {
  accept: "Draft accepted and sent to the customer.",
  edit: "Edited reply sent to the customer.",
  reject: "Draft rejected.",
  escalate: "Ticket escalated to admin for approval.",
  doubt: "Sent to admin for a second opinion.",
};

interface ReviewActionsProps {
  token: string;
  ticket: Ticket;
  onDone: () => void;
}

type Mode = "idle" | "editing" | "rejecting" | "doubting";

const REASON_LABEL: Record<ReasonCode, string> = {
  wrong_source: "Wrong source",
  outdated_source: "Outdated source",
  missing_step: "Missing step",
  invented_step: "Invented step",
  did_not_address_question: "Missed the question",
  tone: "Tone",
  formatting: "Formatting",
  other: "Other",
};

function ReasonChips({ value, onChange }: { value: ReasonCode[]; onChange: (v: ReasonCode[]) => void }) {
  return (
    <div className="reason-chips" role="group" aria-label="Reason codes">
      {REASON_CODES.map((code) => {
        const on = value.includes(code);
        return (
          <button
            key={code}
            type="button"
            className={on ? "reason-chip reason-chip-on" : "reason-chip"}
            aria-pressed={on}
            onClick={() => onChange(on ? value.filter((c) => c !== code) : [...value, code])}
          >
            {REASON_LABEL[code]}
          </button>
        );
      })}
    </div>
  );
}

// Time from the draft appearing to the decision: the handling-time outcome of the
// Week 11 user study (Blueprint V2 H4). Shown so the engineer knows it is measured.
function useDecisionTimer() {
  const started = useRef(performance.now());
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setSeconds(Math.floor((performance.now() - started.current) / 1000)), 1000);
    return () => clearInterval(t);
  }, []);
  return { seconds, elapsedMs: () => Math.round(performance.now() - started.current) };
}

// Accept / Edit / Reject / Escalate on a drafted ticket — the primary training signal
// for confidence-model retraining going forward (docs/confidence-labelling-guide.md).
// See app/routers/tickets.py's submit_ticket_feedback: edit/reject never overwrite the
// AI's original draft, so what this component sends is the whole record of "what the
// reviewer actually did", not a replacement for the AI's output.
export default function ReviewActions({ token, ticket, onDone }: ReviewActionsProps) {
  const [mode, setMode] = useState<Mode>("idle");
  const [editedReply, setEditedReply] = useState(ticket.ai_draft_reply ?? "");
  const [rejectReason, setRejectReason] = useState("");
  const [doubtNote, setDoubtNote] = useState("");
  const [reasonCodes, setReasonCodes] = useState<ReasonCode[]>([]);
  const timer = useDecisionTimer();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { notify } = useToast();

  async function act(action: FeedbackAction, details?: { editedReply?: string; rejectReason?: string }) {
    setSubmitting(true);
    setError(null);
    try {
      await submitTicketFeedback(token, ticket.id, action, {
        ...details,
        reasonCodes,
        timeTakenMs: timer.elapsedMs(),
      });
      setMode("idle");
      notify(ACTION_TOAST[action], action === "reject" ? "info" : "success");
      onDone();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not submit feedback";
      setError(message);
      notify(message, "error");
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
        <p className="reason-chips-label">What did you have to fix? (optional)</p>
        <ReasonChips value={reasonCodes} onChange={setReasonCodes} />
        {error && <p className="form-error">{error}</p>}
        <div className="review-actions-buttons">
          <Button
            disabled={submitting || !editedReply.trim()}
            onClick={() => act("edit", { editedReply })}
          >
            <CheckIcon />
            {submitting ? "Saving…" : "Save edit"}
          </Button>
          <Button variant="secondary" disabled={submitting} onClick={() => setMode("idle")}>
            <XIcon />
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  if (mode === "doubting") {
    return (
      <div className="review-actions">
        <FormField
          label="What are you unsure about?"
          htmlFor="doubt-note"
          hint="This goes back to Admin for a second opinion or reassignment, not the customer."
        >
          <textarea
            id="doubt-note"
            rows={3}
            value={doubtNote}
            onChange={(e) => setDoubtNote(e.target.value)}
            placeholder="e.g. Not confident this is the right department for this issue…"
          />
        </FormField>
        {error && <p className="form-error">{error}</p>}
        <div className="review-actions-buttons">
          <Button
            variant="secondary"
            disabled={submitting || !doubtNote.trim()}
            onClick={() => act("doubt", { rejectReason: doubtNote })}
          >
            <QuestionIcon />
            {submitting ? "Sending…" : "Send to admin"}
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
        <FormField label="Rejection reason" htmlFor="reject-reason" hint="Briefly explain why this draft isn't suitable.">
          <textarea
            id="reject-reason"
            rows={3}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="e.g. Incorrect resolution steps, missing context…"
          />
        </FormField>
        <p className="reason-chips-label">Reason codes (at least one)</p>
        <ReasonChips value={reasonCodes} onChange={setReasonCodes} />
        {error && <p className="form-error">{error}</p>}
        <div className="review-actions-buttons">
          <Button
            variant="danger"
            disabled={submitting || !rejectReason.trim() || reasonCodes.length === 0}
            onClick={() => act("reject", { rejectReason })}
          >
            <XIcon />
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
      <p className="decision-timer" aria-live="off" title="Time since the draft opened; recorded with your decision">
        Reviewing for {Math.floor(timer.seconds / 60)}:{String(timer.seconds % 60).padStart(2, "0")}
      </p>
      <div className="review-actions-buttons">
        <Button disabled={submitting} onClick={() => act("accept")}>
          <CheckIcon />
          Accept
        </Button>
        <Button variant="secondary" disabled={submitting} onClick={() => setMode("editing")}>
          <EditIcon />
          Edit
        </Button>
        <Button variant="danger" disabled={submitting} onClick={() => setMode("rejecting")}>
          <XIcon />
          Reject
        </Button>
        <Button variant="secondary" disabled={submitting} onClick={() => act("escalate")}>
          <ArrowUpRightIcon />
          Escalate
        </Button>
        <Button variant="secondary" disabled={submitting} onClick={() => setMode("doubting")}>
          <QuestionIcon />
          Doubt
        </Button>
      </div>
    </div>
  );
}
