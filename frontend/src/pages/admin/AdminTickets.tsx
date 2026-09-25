import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, StatCard } from "../../components";
import { SearchIcon } from "../../components/icons";
import { listTickets, listDepartments, ApiError, type Ticket, type Department } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { statusLabel, statusBadgeClass } from "../../statusLabels";

const STATUSES = ["submitted", "classified", "routed", "drafted", "escalated", "reviewed", "closed"];
const PRIORITIES = ["high", "medium", "low"];

// The one screen the admin control center was missing entirely before this redesign:
// every ticket in the system, regardless of department or status (the backend's
// visibility filter already grants admin unrestricted read access — see
// app/routers/tickets.py's _visibility_filter — this page is just the first UI for it).
export default function AdminTickets() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [priority, setPriority] = useState("");

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([
      listTickets(token, {
        status: status || undefined,
        departmentId: departmentId || undefined,
        priority: priority || undefined,
        sort: "priority",
      }),
      listDepartments(token),
    ])
      .then(([t, d]) => {
        setTickets(t);
        setDepartments(d);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load tickets"))
      .finally(() => setLoading(false));
  }, [token, status, departmentId, priority]);

  const departmentName = (id: string | null) => (id ? departments.find((d) => d.id === id)?.name ?? "—" : "Unrouted");

  const filtered = useMemo(() => {
    if (!search.trim()) return tickets;
    const q = search.trim().toLowerCase();
    return tickets.filter((t) => t.subject.toLowerCase().includes(q) || t.description.toLowerCase().includes(q));
  }, [tickets, search]);

  const escalatedCount = tickets.filter((t) => t.status === "escalated").length;
  const draftedCount = tickets.filter((t) => t.status === "drafted").length;
  const reviewedCount = tickets.filter((t) => t.status === "reviewed" || t.status === "closed").length;

  return (
    <>
      {!loading && !error && (
        <div className="stat-grid">
          <StatCard label="Total tickets" value={tickets.length} accent />
          <StatCard label="Draft in review" value={draftedCount} tone="info" />
          <StatCard label="Escalated" value={escalatedCount} tone={escalatedCount > 0 ? "danger" : undefined} />
          <StatCard label="Resolved" value={reviewedCount} tone="success" />
        </div>
      )}

      <Card title="All tickets">
        <div className="filter-bar">
          <div className="filter-bar-search">
            <SearchIcon width={15} height={15} />
            <input
              placeholder="Search subject or description…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search tickets"
            />
          </div>
          <select className="select-filter" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {statusLabel(s)}
              </option>
            ))}
          </select>
          <select
            className="select-filter"
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value)}
            aria-label="Filter by department"
          >
            <option value="">All departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select className="select-filter" value={priority} onChange={(e) => setPriority(e.target.value)} aria-label="Filter by priority">
            <option value="">All priorities</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p[0].toUpperCase() + p.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {loading && <p className="placeholder-note">Loading...</p>}
        {error && <p className="form-error">{error}</p>}
        {!loading && !error && filtered.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <p className="empty-state-title">No tickets match</p>
            <p className="empty-state-desc">Try clearing a filter or the search box.</p>
          </div>
        )}
        {!loading && filtered.length > 0 && (
          <table className="ticket-table ticket-table-dense">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Department</th>
                <th>Priority</th>
                <th className="col-right">Confidence</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((ticket) => (
                <tr key={ticket.id} className="clickable-row" onClick={() => navigate(`/tickets/${ticket.id}`)}>
                  <td className="ticket-table-subject">{ticket.subject}</td>
                  <td>
                    <span className="dept-chip">{departmentName(ticket.department_id)}</span>
                  </td>
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
                  <td className="ticket-table-date">{new Date(ticket.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
