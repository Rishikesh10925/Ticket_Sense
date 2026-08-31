import { useEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card } from "../components";
import {
  getTicket,
  getTicketEvidence,
  listDepartments,
  ApiError,
  type Ticket,
  type Evidence,
  type Citation,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { statusLabel, statusBadgeClass } from "../statusLabels";

const UNROUTED_STATUSES = ["submitted", "classified"];
// The pipeline (classify -> route -> retrieve -> draft, see docs/langgraph-pipeline.md)
// runs as a single background task, so this only ever needs a couple of polls in
// practice — but it polls through every pre-draft status, not just the pre-route ones,
// so the draft panel picks up the moment it's ready rather than stopping at "routed".
const PENDING_DRAFT_STATUSES = ["submitted", "classified", "routed"];
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 15; // ~30s — the pipeline normally finishes in a few seconds

const SOURCE_LABEL: Record<Evidence["source_type"], string> = {
  knowledge_base: "Knowledge Base",
  resolved_ticket: "Resolved Ticket",
};

// A resolved ticket's snippet is stored as "subject\n\ndescription" (see
// ai/embeddings/embed_resolved_tickets.py), and item.title already shows the subject
// — without this, the body repeats it verbatim on its own first line. A knowledge-base
// snippet is the article's raw markdown (see db/seed/knowledge_base/), which likewise
// opens with a "# Title" line duplicating item.title and a "**Department:** X" line
// duplicating the department badge already shown above it.
function evidenceBody(item: Evidence): string {
  let text = item.snippet;
  if (item.source_type === "resolved_ticket") {
    const [, ...rest] = text.split("\n\n");
    if (rest.length > 0) text = rest.join("\n\n");
  } else {
    text = text
      .replace(/^#\s+.*\n+/, "")
      .replace(/^\*\*Department:\*\*.*\n+/, "")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/\*\*(.+?)\*\*/g, "$1");
  }
  return text.trim();
}

const CITATION_RE = /(\[\d+\])/g;

// Renders the draft's inline [n] markers as small linked badges instead of plain
// text, and lets a reader hover one to see which source it points to without
// cross-referencing the sources list by number themselves.
function renderDraftWithCitations(draft: string, citations: Citation[]): ReactNode {
  return draft.split(CITATION_RE).map((part, i) => {
    const match = /^\[(\d+)\]$/.exec(part);
    if (!match) return <span key={i}>{part}</span>;
    const citation = citations[Number(match[1]) - 1];
    return (
      <sup key={i} className="citation-marker" title={citation?.title ?? "Unknown source"}>
        {part}
      </sup>
    );
  });
}

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const { token, user } = useAuth();
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
    if (!ticket || !PENDING_DRAFT_STATUSES.includes(ticket.status)) return;
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
  const isDrafting = PENDING_DRAFT_STATUSES.includes(ticket.status);
  // A department_engineer/admin sees the real draft once it exists; an end_user never
  // does (the API nulls both fields for that role — see build_ticket_out), so the
  // draft panel itself is engineer/admin-only rather than showing a permanently-empty
  // card to someone who structurally can't see the draft.
  const showDraftPanel = user?.role !== "end_user";

  return (
    <div className="ticket-detail-page">
      <Card
        title={ticket.subject}
        actions={
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Back
          </Button>
        }
      >
        <div className="ticket-detail-badges">
          <span className={statusBadgeClass(ticket.status)}>{statusLabel(ticket.status)}</span>
          {ticket.priority && (
            <span className={`priority-badge priority-${ticket.priority}`}>{ticket.priority}</span>
          )}
          {ticket.sentiment && <span className="status-badge">{ticket.sentiment}</span>}
          {isDrafting && <span className="status-badge status-pending">working…</span>}
        </div>

        <dl className="ticket-detail-fields">
          <div className="ticket-detail-field ticket-detail-field-wide">
            <dt>Description</dt>
            <dd>{ticket.description}</dd>
          </div>

          <div className="ticket-detail-field">
            <dt>Department</dt>
            <dd>
              {ticket.department_id
                ? departmentNames[ticket.department_id] ?? ticket.department_id
                : "Not yet routed"}
            </dd>
          </div>

          <div className="ticket-detail-field">
            <dt>Priority</dt>
            <dd>{ticket.priority ?? "Not yet classified"}</dd>
          </div>

          <div className="ticket-detail-field">
            <dt>Sentiment</dt>
            <dd>{ticket.sentiment ?? "Not yet classified"}</dd>
          </div>

          {ticket.attachment_path && (
            <div className="ticket-detail-field">
              <dt>Attachment</dt>
              <dd>
                {ticket.attachment_type} — {ticket.attachment_path.split("/").pop()}
              </dd>
            </div>
          )}

          <div className="ticket-detail-field">
            <dt>Submitted</dt>
            <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
          </div>
        </dl>

        {!showDraftPanel && (
          <p className="placeholder-note">
            {isDrafting
              ? "This ticket is being classified, routed, and drafted automatically."
              : "A department engineer has an AI-drafted reply for this ticket, based on retrieved evidence. They'll review it before anything is sent to you."}
          </p>
        )}
      </Card>

      <div className="ticket-detail-side-by-side">
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
                  <p className="evidence-snippet">{evidenceBody(item)}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {showDraftPanel && (
          <Card title="AI draft reply">
            {isClassifying && (
              <p className="placeholder-note">
                Not routed to a department yet — drafting starts once retrieval has
                somewhere to search.
              </p>
            )}
            {!isClassifying && isDrafting && (
              <p className="placeholder-note">Generating a grounded draft from the retrieved evidence…</p>
            )}
            {!isDrafting && !ticket.ai_draft_reply && (
              <p className="placeholder-note">No draft is available for this ticket.</p>
            )}
            {ticket.ai_draft_reply && (
              <>
                <p className="draft-text">
                  {renderDraftWithCitations(ticket.ai_draft_reply, ticket.ai_draft_citations ?? [])}
                </p>
                {ticket.ai_draft_citations && ticket.ai_draft_citations.length > 0 && (
                  <>
                    <h4 className="draft-sources-heading">Sources</h4>
                    <ol className="draft-sources-list">
                      {ticket.ai_draft_citations.map((citation, i) => (
                        <li key={`${citation.source_type}-${citation.source_id}`}>
                          <span className="status-badge">{SOURCE_LABEL[citation.source_type]}</span>{" "}
                          [{i + 1}] {citation.title}
                        </li>
                      ))}
                    </ol>
                  </>
                )}
              </>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
