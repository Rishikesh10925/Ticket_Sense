import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, StatCard } from "../components";
import { listTickets, ApiError, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { statusLabel, statusBadgeClass } from "../statusLabels";

const STATUSES = ["submitted", "classified", "routed", "drafted", "escalated", "reviewed", "closed"];

const SENTIMENT_CLASS: Record<string, string> = {
  positive: "sentiment-positive",
  neutral: "sentiment-neutral",
  negative: "sentiment-negative",
};

export default function EngineerQueue() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    listTickets(token, { status: status || undefined, sort: "priority" })
      .then(setTickets)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load queue"))
      .finally(() => setLoading(false));
  }, [token, status]);

  const highPriorityCount = tickets.filter((t) => t.priority === "high").length;
  const draftCount = tickets.filter((t) => t.status === "drafted").length;
  const escalatedCount = tickets.filter((t) => t.status === "escalated").length;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Queue</h1>
          <p>Tickets routed to your department, sorted by priority.</p>
        </div>
      </div>

      {!loading && !error && tickets.length > 0 && (
        <div className="stat-grid">
          <StatCard label="In queue" value={tickets.length} accent />
          <StatCard label="High priority" value={highPriorityCount} />
          <StatCard label="Draft in review" value={draftCount} />
          <StatCard label="Escalated" value={escalatedCount} tone={escalatedCount > 0 ? "danger" : undefined} />
        </div>
      )}

      <Card
        title="Tickets"
        actions={
          <select
            className="select-filter"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
        }
      >
        {loading && <p className="placeholder-note">Loading...</p>}
        {error && <p className="form-error">{error}</p>}
        {!loading && !error && tickets.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">✅</div>
            <p className="empty-state-title">Queue is clear</p>
            <p className="empty-state-desc">
              {status ? `No tickets with status "${statusLabel(status)}"` : "No tickets in your queue right now."}
            </p>
          </div>
        )}
        {!loading && tickets.length > 0 && (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Priority</th>
                <th>Sentiment</th>
                <th>Confidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  className={`clickable-row${ticket.status === "escalated" ? " row-escalated" : ""}`}
                  onClick={() => navigate(`/tickets/${ticket.id}`)}
                >
                  <td className="ticket-table-subject">{ticket.subject}</td>
                  <td>
                    {ticket.priority ? (
                      <span className={`priority-badge priority-${ticket.priority}`}>
                        {ticket.priority}
                      </span>
                    ) : (
                      <span className="placeholder-note">—</span>
                    )}
                  </td>
                  <td>
                    {ticket.sentiment ? (
                      <span className={`sentiment-badge ${SENTIMENT_CLASS[ticket.sentiment] ?? ""}`}>
                        {ticket.sentiment}
                      </span>
                    ) : (
                      <span className="placeholder-note">—</span>
                    )}
                  </td>
                  <td>
                    {ticket.confidence_score !== null && ticket.confidence_threshold !== null ? (
                      <span
                        className={`confidence-mini-badge ${
                          ticket.confidence_score >= ticket.confidence_threshold
                            ? "confidence-mini-pass"
                            : "confidence-mini-fail"
                        }`}
                      >
                        {Math.round(ticket.confidence_score * 100)}%
                      </span>
                    ) : (
                      <span className="placeholder-note">—</span>
                    )}
                  </td>
                  <td>
                    <span className={statusBadgeClass(ticket.status)}>{statusLabel(ticket.status)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
