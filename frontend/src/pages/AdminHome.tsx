import { useEffect, useState, type CSSProperties } from "react";
import { Button, Card, StatCard } from "../components";
import { BookIcon, BuildingIcon, ChartIcon, GearIcon, UsersIcon } from "../components/icons";
import {
  listUsers,
  listDepartments,
  listKnowledgeBase,
  updateDepartmentThreshold,
  getAnalyticsSummary,
  ApiError,
  type User,
  type Department,
  type KnowledgeBaseArticle,
  type AnalyticsSummary,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Section = "users" | "departments" | "knowledge-base" | "analytics" | "settings";

const SECTIONS: { id: Section; label: string; hint: string; icon: typeof UsersIcon; available: boolean }[] = [
  { id: "users", label: "Users", hint: "Roles & departments", icon: UsersIcon, available: true },
  { id: "departments", label: "Departments", hint: "Confidence gates", icon: BuildingIcon, available: true },
  { id: "knowledge-base", label: "Knowledge base", hint: "Source articles", icon: BookIcon, available: true },
  { id: "analytics", label: "Analytics", hint: "Resolution metrics", icon: ChartIcon, available: true },
  { id: "settings", label: "Settings", hint: "Workspace config", icon: GearIcon, available: false },
];

const ROLE_LABEL: Record<string, string> = {
  end_user: "End User",
  department_engineer: "Department Engineer",
  admin: "Admin",
};

export default function AdminHome() {
  const { token } = useAuth();

  const [section, setSection] = useState<Section>("users");
  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [articles, setArticles] = useState<KnowledgeBaseArticle[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [thresholdDrafts, setThresholdDrafts] = useState<Record<string, string>>({});
  const [savingThresholdId, setSavingThresholdId] = useState<string | null>(null);
  const [thresholdError, setThresholdError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listUsers(token), listDepartments(token), listKnowledgeBase(token), getAnalyticsSummary(token)])
      .then(([u, d, a, summary]) => {
        setUsers(u);
        setDepartments(d);
        setArticles(a);
        setAnalytics(summary);
        setThresholdDrafts(Object.fromEntries(d.map((dept) => [dept.id, String(dept.confidence_threshold)])));
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load admin data"))
      .finally(() => setLoading(false));
  }, [token]);

  const departmentName = (id: string) => departments.find((d) => d.id === id)?.name ?? "—";

  async function handleSaveThreshold(deptId: string) {
    if (!token) return;
    const value = Number(thresholdDrafts[deptId]);
    if (Number.isNaN(value) || value < 0 || value > 1) {
      setThresholdError("Threshold must be a number between 0 and 1.");
      return;
    }
    setSavingThresholdId(deptId);
    setThresholdError(null);
    try {
      const updated = await updateDepartmentThreshold(token, deptId, value);
      setDepartments((prev) => prev.map((d) => (d.id === deptId ? updated : d)));
    } catch (err) {
      setThresholdError(err instanceof ApiError ? err.message : "Could not update threshold");
    } finally {
      setSavingThresholdId(null);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Admin</h1>
          <p>Manage users, departments, and the knowledge base.</p>
        </div>
      </div>

      {!loading && !error && (
        <div className="stat-grid">
          <StatCard label="Users" value={users.length} accent />
          <StatCard label="Departments" value={departments.length} />
          <StatCard label="Knowledge base articles" value={articles.length} tone="info" />
        </div>
      )}

      <div className="admin-layout">
        <Card title="Sections">
          <ul className="section-list">
            {SECTIONS.map((s) => (
              <li
                key={s.id}
                className={s.id === section ? "section-active" : ""}
                onClick={() => s.available && setSection(s.id)}
                aria-disabled={!s.available}
                style={!s.available ? { cursor: "default", opacity: 0.6 } : {}}
              >
                <span className="section-list-icon">
                  <s.icon width={16} height={16} />
                </span>
                <span className="section-list-text">
                  <span className="section-list-label">{s.label}</span>
                  <span className="section-list-hint">{s.hint}</span>
                </span>
                {!s.available && <span className="section-soon">Soon</span>}
              </li>
            ))}
          </ul>
        </Card>

        {section === "users" && (
          <Card title="Users">
            {loading && <p className="placeholder-note">Loading...</p>}
            {error && <p className="form-error">{error}</p>}
            {!loading && !error && (
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Department</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="ticket-table-subject">{user.full_name}</td>
                      <td>{user.email}</td>
                      <td>{ROLE_LABEL[user.role] ?? user.role}</td>
                      <td>{user.department_id ? departmentName(user.department_id) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        )}

        {section === "departments" && (
          <Card title="Departments">
            {loading && <p className="placeholder-note">Loading...</p>}
            {error && <p className="form-error">{error}</p>}
            {thresholdError && <p className="form-error">{thresholdError}</p>}
            {!loading && !error && (
              <>
                <table className="ticket-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Engineers</th>
                      <th>KB articles</th>
                      <th>Confidence threshold</th>
                    </tr>
                  </thead>
                  <tbody>
                    {departments.map((dept) => {
                      const draft = thresholdDrafts[dept.id] ?? String(dept.confidence_threshold);
                      const changed = Number(draft) !== dept.confidence_threshold;
                      return (
                        <tr key={dept.id}>
                          <td className="ticket-table-subject">{dept.name}</td>
                          <td>
                            {
                              users.filter(
                                (u) => u.department_id === dept.id && u.role === "department_engineer"
                              ).length
                            }
                          </td>
                          <td>{articles.filter((a) => a.department_id === dept.id).length}</td>
                          <td>
                            <div className="threshold-editor">
                              <div className="threshold-editor-control">
                                <input
                                  type="range"
                                  min={0}
                                  max={1}
                                  step={0.05}
                                  value={draft}
                                  aria-label={`Confidence threshold for ${dept.name}`}
                                  className="threshold-slider"
                                  style={{ "--fill": `${Number(draft) * 100}%` } as CSSProperties}
                                  onChange={(e) =>
                                    setThresholdDrafts((prev) => ({ ...prev, [dept.id]: e.target.value }))
                                  }
                                />
                                <span className={`threshold-readout tabular-nums${changed ? " threshold-readout-changed" : ""}`}>
                                  {Math.round(Number(draft) * 100)}%
                                </span>
                              </div>
                              <Button
                                variant="secondary"
                                disabled={!changed || savingThresholdId === dept.id}
                                onClick={() => handleSaveThreshold(dept.id)}
                              >
                                {savingThresholdId === dept.id ? "Saving…" : "Save"}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <p className="placeholder-note draft-status-legend">
                  Tickets routed to a department below this score are escalated instead
                  of shown to an engineer, once the Week 9 confidence gate is wired in.
                  Existing tickets keep whatever threshold was in force when they were
                  scored — changing this only affects new tickets.
                </p>
              </>
            )}
          </Card>
        )}

        {section === "knowledge-base" && (
          <Card title="Knowledge base">
            {loading && <p className="placeholder-note">Loading...</p>}
            {error && <p className="form-error">{error}</p>}
            {!loading && !error && (
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Department</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {articles.map((article) => (
                    <tr key={article.id}>
                      <td className="ticket-table-subject">{article.title}</td>
                      <td>{departmentName(article.department_id)}</td>
                      <td>{new Date(article.updated_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        )}

        {section === "analytics" && (
          <Card title="Analytics">
            {loading && <p className="placeholder-note">Loading...</p>}
            {error && <p className="form-error">{error}</p>}
            {!loading && !error && analytics && (
              <>
                <div className="stat-grid">
                  <StatCard label="Total tickets" value={analytics.total_tickets} accent />
                  <StatCard
                    label="Escalation rate"
                    value={
                      analytics.escalation_rate !== null ? `${Math.round(analytics.escalation_rate * 100)}%` : "—"
                    }
                  />
                  <StatCard label="Draft in review" value={analytics.by_status.drafted ?? 0} tone="info" />
                  <StatCard
                    label="Escalated (open)"
                    value={analytics.by_status.escalated ?? 0}
                    tone={(analytics.by_status.escalated ?? 0) > 0 ? "danger" : undefined}
                  />
                </div>

                <h4 className="draft-sources-heading">Confidence score distribution</h4>
                <div className="confidence-histogram">
                  {analytics.confidence_distribution.map((bucket) => {
                    const max = Math.max(...analytics.confidence_distribution.map((b) => b.count), 1);
                    return (
                      <div key={bucket.label} className="confidence-histogram-col">
                        <span className="confidence-histogram-count tabular-nums">{bucket.count}</span>
                        <div className="confidence-histogram-track">
                          <div
                            className="confidence-histogram-bar"
                            style={{ height: `${(bucket.count / max) * 100}%` }}
                          />
                        </div>
                        <span className="confidence-histogram-label">{bucket.label.replace("%", "")}</span>
                      </div>
                    );
                  })}
                </div>

                <h4 className="draft-sources-heading">By department</h4>
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
                        <td>
                          {dept.avg_confidence !== null ? `${Math.round(dept.avg_confidence * 100)}%` : "—"}
                        </td>
                        <td>
                          {dept.escalation_rate !== null ? `${Math.round(dept.escalation_rate * 100)}%` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <h4 className="draft-sources-heading">By engineer</h4>
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
                  "Resolved" counts a reviewer's Accept and Edit actions combined (both send the final
                  response); "In review" is how many drafted tickets are currently waiting in that
                  engineer's department queue, not assigned to them personally — a ticket has no
                  specific reviewer until someone acts on it.
                  {analytics.real_feedback.total === 0 &&
                    " No real reviewer actions have been recorded yet, so these are all zero — they'll fill in as engineers actually review drafted tickets."}
                  {" "}({analytics.synthetic_feedback.total} synthetic bootstrap feedback rows exist for
                  confidence-model training and are intentionally excluded from this per-engineer view.)
                </p>
              </>
            )}
          </Card>
        )}

        {section === "settings" && (
          <Card title="Settings">
            <p className="placeholder-note">Not built yet — workspace settings land in a later week.</p>
          </Card>
        )}
      </div>
    </>
  );
}
