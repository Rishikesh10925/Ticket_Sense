import { useEffect, useMemo, useState } from "react";
import { Card, StatCard } from "../../components";
import { SearchIcon } from "../../components/icons";
import { listUsers, listTickets, ApiError, type User, type Ticket } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

const OPEN_STATUSES = new Set(["submitted", "classified", "routed", "drafted"]);
const RESOLVED_STATUSES = new Set(["reviewed", "closed"]);

// The placeholder account data/seed_synthetic_tickets.py attributes the 120 synthetic
// historical tickets to (see PLACEHOLDER_EMAIL there) — it isn't a real customer, and
// including it would both clutter this list and badly skew "avg tickets/customer".
const SYNTHETIC_PLACEHOLDER_EMAIL = "synthetic-tickets@ticketsense.local";

interface CustomerStats {
  user: User;
  total: number;
  resolved: number;
  open: number;
  escalated: number;
  lastActivity: string | null;
}

// A per-customer rollup built client-side from the same two admin-visible endpoints
// every other tab already calls (GET /users, GET /tickets) — no new backend endpoint
// needed, since Ticket.submitted_by is already on every ticket the admin can see.
export default function AdminCustomers() {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listUsers(token), listTickets(token)])
      .then(([u, t]) => {
        setUsers(u);
        setTickets(t);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load customers"))
      .finally(() => setLoading(false));
  }, [token]);

  const customerStats = useMemo<CustomerStats[]>(() => {
    const customers = users.filter((u) => u.role === "end_user" && u.email !== SYNTHETIC_PLACEHOLDER_EMAIL);
    const ticketsByCustomer = new Map<string, Ticket[]>();
    for (const t of tickets) {
      const list = ticketsByCustomer.get(t.submitted_by) ?? [];
      list.push(t);
      ticketsByCustomer.set(t.submitted_by, list);
    }

    return customers
      .map((user) => {
        const owned = ticketsByCustomer.get(user.id) ?? [];
        const resolved = owned.filter((t) => RESOLVED_STATUSES.has(t.status)).length;
        const open = owned.filter((t) => OPEN_STATUSES.has(t.status)).length;
        const escalated = owned.filter((t) => t.status === "escalated").length;
        const lastActivity = owned.length
          ? owned.reduce((latest, t) => (t.created_at > latest ? t.created_at : latest), owned[0].created_at)
          : null;
        return { user, total: owned.length, resolved, open, escalated, lastActivity };
      })
      .sort((a, b) => b.total - a.total);
  }, [users, tickets]);

  const filtered = useMemo(() => {
    if (!search.trim()) return customerStats;
    const q = search.trim().toLowerCase();
    return customerStats.filter(
      (c) => c.user.full_name.toLowerCase().includes(q) || c.user.email.toLowerCase().includes(q)
    );
  }, [customerStats, search]);

  const totalCustomers = customerStats.length;
  const activeSubmitters = customerStats.filter((c) => c.total > 0).length;
  const totalTicketsFromCustomers = customerStats.reduce((sum, c) => sum + c.total, 0);
  const avgPerCustomer = totalCustomers > 0 ? (totalTicketsFromCustomers / totalCustomers).toFixed(1) : "0";

  return (
    <>
      {!loading && !error && (
        <div className="stat-grid">
          <StatCard label="Customers" value={totalCustomers} accent />
          <StatCard label="Have submitted a ticket" value={activeSubmitters} tone="info" />
          <StatCard label="Tickets submitted" value={totalTicketsFromCustomers} />
          <StatCard label="Avg. tickets / customer" value={avgPerCustomer} tone="success" />
        </div>
      )}

      <Card title="Customers">
        <div className="filter-bar">
          <div className="filter-bar-search">
            <SearchIcon width={15} height={15} />
            <input
              placeholder="Search name or email…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search customers"
            />
          </div>
        </div>

        {loading && <p className="placeholder-note">Loading...</p>}
        {error && <p className="form-error">{error}</p>}
        {!loading && !error && filtered.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">👥</div>
            <p className="empty-state-title">No customers match</p>
            <p className="empty-state-desc">Try a different search.</p>
          </div>
        )}
        {!loading && !error && filtered.length > 0 && (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th className="col-right">Total tickets</th>
                <th className="col-right">Resolved</th>
                <th className="col-right">Open</th>
                <th className="col-right">Escalated</th>
                <th>Last activity</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.user.id} className={!c.user.is_active ? "row-inactive" : undefined}>
                  <td className="ticket-table-subject">{c.user.full_name}</td>
                  <td>{c.user.email}</td>
                  <td className="col-right tabular-nums">{c.total}</td>
                  <td className="col-right tabular-nums">
                    {c.resolved > 0 ? <span className="status-badge status-reviewed">{c.resolved}</span> : "0"}
                  </td>
                  <td className="col-right tabular-nums">
                    {c.open > 0 ? <span className="status-badge status-drafted">{c.open}</span> : "0"}
                  </td>
                  <td className="col-right tabular-nums">
                    {c.escalated > 0 ? <span className="status-badge status-escalated">{c.escalated}</span> : "0"}
                  </td>
                  <td className="ticket-table-date">
                    {c.lastActivity ? new Date(c.lastActivity).toLocaleDateString() : "—"}
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
