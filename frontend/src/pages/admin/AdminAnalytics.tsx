import { useEffect, useState } from "react";
import { BarChart, Card, DonutChart, StatCard } from "../../components";
import { getAnalyticsSummary, ApiError, type AnalyticsSummary } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { statusLabel } from "../../statusLabels";

// Fixed order, validated for CVD-safe adjacent contrast (dataviz skill's default
// categorical palette) — departments are always rendered in this same slot order
// so a bar's color means the same department every time the page reloads.
const CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"];

const STATUS_COLORS: Record<string, string> = {
  submitted: "var(--color-text-faint)",
  classified: "var(--color-text-faint)",
  routed: "var(--color-border-strong)",
  drafted: "var(--color-info-strong)",
  escalated: "var(--color-danger-strong)",
  reviewed: "var(--color-success-strong)",
  closed: "var(--color-text-muted)",
};

const ACTION_COLORS: Record<string, string> = {
  accept: "var(--color-success-strong)",
  edit: "var(--color-info-strong)",
  resolve: "var(--color-success)",
  reject: "var(--color-danger-strong)",
  escalate: "var(--color-warning-strong)",
  doubt: "var(--color-warning)",
};

const ACTION_LABELS: Record<string, string> = {
  accept: "Accept",
  edit: "Edit",
  reject: "Reject",
  escalate: "Escalate",
  doubt: "Doubt",
  resolve: "Resolve",
};

export default function AdminAnalytics() {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    getAnalyticsSummary(token)
      .then(setAnalytics)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load analytics"))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <p className="placeholder-note">Loading...</p>;
  if (error) return <p className="form-error">{error}</p>;
  if (!analytics) return null;

  const statusData = Object.entries(analytics.by_status)
    .filter(([, count]) => count > 0)
    .map(([status, count]) => ({ label: statusLabel(status), value: count, color: STATUS_COLORS[status] ?? "var(--color-text-faint)" }));

  const departmentBarData = analytics.by_department.map((d, i) => ({
    label: d.department_name,
    value: d.total_tickets,
    color: CATEGORICAL[i % CATEGORICAL.length],
  }));

  const confidenceBarData = analytics.confidence_distribution.map((b) => ({
    label: b.label.replace("%", ""),
    value: b.count,
  }));

  const actionData = Object.entries(analytics.real_feedback.review_actions).map(([action, count]) => ({
    label: ACTION_LABELS[action] ?? action,
    value: count,
    color: ACTION_COLORS[action],
  }));

  return (
    <>
      <div className="stat-grid">
        <StatCard label="Total tickets" value={analytics.total_tickets} accent />
        <StatCard
          label="Escalation rate"
          value={analytics.escalation_rate !== null ? `${Math.round(analytics.escalation_rate * 100)}%` : "—"}
        />
        <StatCard label="Draft in review" value={analytics.by_status.drafted ?? 0} tone="info" />
        <StatCard
          label="Escalated (open)"
          value={analytics.by_status.escalated ?? 0}
          tone={(analytics.by_status.escalated ?? 0) > 0 ? "danger" : undefined}
        />
      </div>

      <div className="analytics-grid">
        <Card title="Tickets by status">
          <DonutChart data={statusData} ariaLabel="Ticket count by status" centerLabel={String(analytics.total_tickets)} />
        </Card>

        <Card title="Tickets by department">
          <BarChart data={departmentBarData} ariaLabel="Ticket count by department" />
        </Card>
      </div>

      <Card title="Confidence score distribution">
        <BarChart data={confidenceBarData} ariaLabel="Confidence score distribution" height={140} />
      </Card>

      {analytics.real_feedback.total > 0 && (
        <Card title="Reviewer actions">
          <BarChart data={actionData} ariaLabel="Review actions taken by engineers" height={140} />
        </Card>
      )}

      <Card title="By department">
        <table className="ticket-table">
          <thead>
            <tr>
              <th>Department</th>
              <th>Tickets</th>
              <th>Avg confidence</th>
              <th>Escalation rate</th>
            </tr>
          </thead>
          <tbody>
            {analytics.by_department.map((dept) => (
              <tr key={dept.department_id}>
                <td className="ticket-table-subject">{dept.department_name}</td>
                <td>{dept.total_tickets}</td>
                <td>{dept.avg_confidence !== null ? `${Math.round(dept.avg_confidence * 100)}%` : "—"}</td>
                <td>{dept.escalation_rate !== null ? `${Math.round(dept.escalation_rate * 100)}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="By engineer">
        {analytics.by_reviewer.length === 0 ? (
          <p className="placeholder-note">No department engineers on record yet.</p>
        ) : (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Engineer</th>
                <th>Department</th>
                <th>Resolved</th>
                <th>In review</th>
                <th>Rejected</th>
                <th>Escalated</th>
              </tr>
            </thead>
            <tbody>
              {analytics.by_reviewer.map((reviewer) => (
                <tr key={reviewer.reviewer_id}>
                  <td className="ticket-table-subject">{reviewer.reviewer_name}</td>
                  <td>{reviewer.department_name}</td>
                  <td>{reviewer.resolved}</td>
                  <td>{reviewer.in_review}</td>
                  <td>{reviewer.rejected}</td>
                  <td>{reviewer.escalated}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="placeholder-note draft-status-legend">
          "Resolved" counts Accept, Edit, and manually-resolved escalations combined (all three
          send a final response); "Escalated" counts Escalate and Doubt combined (both send a
          ticket back without deciding it). "In review" is how many drafted tickets are
          currently waiting in that engineer's department queue, not assigned to them
          personally — a ticket has no specific reviewer until someone acts on it.
          {analytics.real_feedback.total === 0 &&
            " No real reviewer actions have been recorded yet, so these are all zero — they'll fill in as engineers actually review drafted tickets."}
          {" "}({analytics.synthetic_feedback.total} synthetic bootstrap feedback rows exist for
          confidence-model training and are intentionally excluded from this per-engineer view.)
        </p>
      </Card>
    </>
  );
}
