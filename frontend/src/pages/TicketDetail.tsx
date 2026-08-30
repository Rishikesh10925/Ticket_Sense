import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card } from "../components";
import {
  getTicket,
  getTicketEvidence,
  listDepartments,
  ApiError,
  type Ticket,
  type Evidence,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

const UNROUTED_STATUSES = ["submitted", "classified"];
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 15; // ~30s — classification normally finishes in a few seconds

const SOURCE_LABEL: Record<Evidence["source_type"], string> = {
  knowledge_base: "Knowledge Base",
  resolved_ticket: "Resolved Ticket",
};

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [departmentNames, setDepartmentNames] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(true);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  const pollCount = useRef(0);

  async function loadTicket() {
    if (!token || !id) return;
    try {
      const [ticketData, departments] = await Promise.all([
        getTicket(token, id),
        listDepartments(token),
      ]);
      setTicket(ticketData);
      setDepartmentNames(Object.fromEntries(departments.map((d) => [d.id, d.name])));
      return ticketData;
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 403
            ? "You don't have access to this ticket."
            : err.message
          : "Could not load ticket"
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadEvidence() {
    if (!token || !id) return;
    setEvidenceLoading(true);
    setEvidenceError(null);
    try {
      setEvidence(await getTicketEvidence(token, id));
    } catch (err) {
      setEvidenceError(err instanceof ApiError ? err.message : "Could not load evidence");
    } finally {
      setEvidenceLoading(false);
    }
  }

  // Classification runs as a backend background task (see docs/ticket-routing.md) —
  // this screen didn't show that anything was happening while it ran (Week 4
  // usability finding #1/#2, docs/usability-testing.md). Poll briefly while the
  // ticket is still submitted/classified, stop once it's routed or a max attempt
  // count is hit, so this never polls forever if something goes wrong.
  useEffect(() => {
    loadTicket().then((t) => {
      if (t) loadEvidence();
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, id]);

  useEffect(() => {
    if (!ticket || !UNROUTED_STATUSES.includes(ticket.status)) return;
    if (pollCount.current >= MAX_POLLS) return;

    const timer = setTimeout(async () => {
      pollCount.current += 1;
      const updated = await loadTicket();
      if (updated && !UNROUTED_STATUSES.includes(updated.status)) {
        await loadEvidence();
      }
    }, POLL_INTERVAL_MS);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticket]);

  if (loading) return <p className="placeholder-note">Loading...</p>;
  if (error) return <p className="form-error">{error}</p>;
  if (!ticket) return null;

  const isClassifying = UNROUTED_STATUSES.includes(ticket.status);

  return (
    <div className="ticket-detail-layout">
      <Card
        title={ticket.subject}
        actions={
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Back
          </Button>
        }
      >
        <div className="ticket-detail-badges">
          <span className="status-badge">{ticket.status}</span>
          {ticket.priority && (
            <span className={`priority-badge priority-${ticket.priority}`}>{ticket.priority}</span>
          )}
          {ticket.sentiment && <span className="status-badge">{ticket.sentiment}</span>}
          {isClassifying && <span className="status-badge status-pending">classifying…</span>}
        </div>

        <dl className="ticket-detail-fields">
          <dt>Description</dt>
          <dd>{ticket.description}</dd>

          <dt>Department</dt>
          <dd>
            {ticket.department_id
              ? departmentNames[ticket.department_id] ?? ticket.department_id
              : "Not yet routed"}
          </dd>

          <dt>Priority</dt>
          <dd>{ticket.priority ?? "Not yet classified"}</dd>

          <dt>Sentiment</dt>
          <dd>{ticket.sentiment ?? "Not yet classified"}</dd>

          {ticket.attachment_path && (
            <>
              <dt>Attachment</dt>
              <dd>
                {ticket.attachment_type} — {ticket.attachment_path.split("/").pop()}
              </dd>
            </>
          )}

          <dt>Submitted</dt>
          <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
        </dl>

        <p className="placeholder-note">
          The AI draft reply, confidence score, and accept/edit/reject/escalate actions
          are not built yet.
        </p>
      </Card>

      <Card
        title="Retrieved evidence"
        actions={
          <Button variant="secondary" onClick={loadEvidence} disabled={evidenceLoading}>
            Refresh
          </Button>
        }
      >
        {evidenceLoading && <p className="placeholder-note">Loading evidence...</p>}
        {evidenceError && <p className="form-error">{evidenceError}</p>}
        {!evidenceLoading && !evidenceError && isClassifying && (
          <p className="placeholder-note">
            This ticket hasn't been routed to a department yet, so there's no evidence
            to show. It updates automatically once classification finishes.
          </p>
        )}
        {!evidenceLoading && !evidenceError && !isClassifying && evidence.length === 0 && (
          <p className="placeholder-note">No matching evidence found for this ticket.</p>
        )}
        {!evidenceLoading && !evidenceError && evidence.length > 0 && (
          <ul className="evidence-list">
            {evidence.map((item) => (
              <li key={`${item.source_type}-${item.source_id}`} className="evidence-item">
                <div className="evidence-item-header">
                  <span className="status-badge">{SOURCE_LABEL[item.source_type]}</span>
                  {ticket.department_id && (
                    <span className="status-badge">
                      {departmentNames[ticket.department_id] ?? "—"}
                    </span>
                  )}
                </div>
                <strong>{item.title}</strong>
                <p className="evidence-snippet">{item.snippet}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
