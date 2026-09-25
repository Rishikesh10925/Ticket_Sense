import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components";
import { listTickets, getAnalyticsSummary, ApiError, type Ticket, type ReviewerBreakdown } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { statusLabel, statusBadgeClass } from "../statusLabels";

const QUICK_FILTERS: { key: string; label: string }[] = [
  { key: "", label: "All" },
  { key: "drafted", label: "Draft in review" },
  { key: "escalated", label: "Escalated" },
  { key: "reviewed", label: "Reviewed" },
];

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
  const [myStats, setMyStats] = useState<ReviewerBreakdown | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    listTickets(token, { status: status || undefined, sort: "priority" })
      .then(setTickets)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load queue"))
      .finally(() => setLoading(false));
  }, [token, status]);

  // Scoped server-side to just this engineer's own row (see GET /analytics/summary) —
  // a personal record of what they've actually done, distinct from the queue below,
  // which is just what's currently waiting.
  useEffect(() => {
    if (!token) return;
    getAnalyticsSummary(token)
      .then((summary) => setMyStats(summary.by_reviewer[0] ?? null))
      .catch(() => setMyStats(null));
  }, [token]);

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

      <div className="engineer-layout">
        <div className="engineer-side">
          <Card title="Today">
            <div className="workspace-stat-list">
              <div className="workspace-stat-row">
                <span>In queue</span>
                <strong className="tabular-nums">{tickets.length}</strong>
              </div>
              <div className="workspace-stat-row">
                <span>High priority</span>
                <strong className={`tabular-nums${highPriorityCount > 0 ? " workspace-stat-warning" : ""}`}>
                  {highPriorityCount}
                </strong>
              </div>
              <div className="workspace-stat-row">
                <span>Draft in review</span>
                <strong className="tabular-nums">{draftCount}</strong>
              </div>
              <div className="workspace-stat-row">
                <span>Escalated</span>
                <strong className={`tabular-nums${escalatedCount > 0 ? " workspace-stat-danger" : ""}`}>
                  {escalatedCount}
                </strong>
              </div>
            </div>
          </Card>

          {myStats && (
            <Card title="My review record">
              <div className="workspace-stat-list">
                <div className="workspace-stat-row">
                  <span>Resolved</span>
                  <strong className="tabular-nums workspace-stat-success">{myStats.resolved}</strong>
                </div>
                <div className="workspace-stat-row">
                  <span>Rejected</span>
                  <strong className="tabular-nums">{myStats.rejected}</strong>
                </div>
                <div className="workspace-stat-row">
                  <span>Escalated / doubted</span>
                  <strong className="tabular-nums">{myStats.escalated}</strong>
                </div>
              </div>
            </Card>
          )}

          <Card title="Filter">
            <div className="quick-filter-list">
              {QUICK_FILTERS.map((f) => (
                <button
                  key={f.key}
                  type="button"
                  className={`quick-filter-btn${status === f.key ? " quick-filter-btn-active" : ""}`}
                  onClick={() => setStatus(f.key)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </Card>
        </div>

        <Card title="Tickets">
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
            <table className="ticket-table ticket-table-dense">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Priority</th>
                  <th>Sentiment</th>
                  <th className="col-right">Confidence</th>
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
                        <span className={`glance glance-${ticket.priority}`}>
                          <span className="glance-dot" />
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
                    <td className="col-right">
                      {ticket.confidence_score !== null && ticket.confidence_threshold !== null ? (
                        <span
                          className={`confidence-mini-badge tabular-nums ${
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
      </div>
    </>
  );
}
