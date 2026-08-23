import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components";
import { listTickets, ApiError, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const STATUSES = ["submitted", "classified", "routed", "drafted", "reviewed", "closed"];

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

  return (
    <Card
      title="Queue"
      actions={
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      }
    >
      {loading && <p className="placeholder-note">Loading...</p>}
      {error && <p className="form-error">{error}</p>}
      {!loading && !error && tickets.length === 0 && (
        <p className="placeholder-note">No tickets in this view.</p>
      )}
      {!loading && tickets.length > 0 && (
        <table className="ticket-table">
          <thead>
            <tr>
              <th>Subject</th>
              <th>Priority</th>
              <th>Sentiment</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr
                key={ticket.id}
                className="clickable-row"
                onClick={() => navigate(`/tickets/${ticket.id}`)}
              >
                <td>{ticket.subject}</td>
                <td>
                  {ticket.priority ? (
                    <span className={`priority-badge priority-${ticket.priority}`}>
                      {ticket.priority}
                    </span>
                  ) : (
                    <span className="placeholder-note">pending</span>
                  )}
                </td>
                <td>{ticket.sentiment ?? "—"}</td>
                <td>
                  <span className="status-badge">{ticket.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
