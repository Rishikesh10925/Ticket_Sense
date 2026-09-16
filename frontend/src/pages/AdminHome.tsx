import { useEffect, useState, type CSSProperties } from "react";
import { Button, Card, StatCard } from "../components";
import { BookIcon, BuildingIcon, ChartIcon, GearIcon, UsersIcon } from "../components/icons";
import {
  listUsers,
  listDepartments,
  listKnowledgeBase,
  updateDepartmentThreshold,
  ApiError,
  type User,
  type Department,
  type KnowledgeBaseArticle,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Section = "users" | "departments" | "knowledge-base" | "analytics" | "settings";

const SECTIONS: { id: Section; label: string; hint: string; icon: typeof UsersIcon; available: boolean }[] = [
  { id: "users", label: "Users", hint: "Roles & departments", icon: UsersIcon, available: true },
  { id: "departments", label: "Departments", hint: "Confidence gates", icon: BuildingIcon, available: true },
  { id: "knowledge-base", label: "Knowledge base", hint: "Source articles", icon: BookIcon, available: true },
  { id: "analytics", label: "Analytics", hint: "Resolution metrics", icon: ChartIcon, available: false },
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [thresholdDrafts, setThresholdDrafts] = useState<Record<string, string>>({});
  const [savingThresholdId, setSavingThresholdId] = useState<string | null>(null);
  const [thresholdError, setThresholdError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listUsers(token), listDepartments(token), listKnowledgeBase(token)])
      .then(([u, d, a]) => {
        setUsers(u);
        setDepartments(d);
        setArticles(a);
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

        {(section === "analytics" || section === "settings") && (
          <Card title={section === "analytics" ? "Analytics" : "Settings"}>
            <p className="placeholder-note">
              Not built yet — {section === "analytics" ? "resolution/acceptance metrics land" : "workspace settings land"}{" "}
              in a later week.
            </p>
          </Card>
        )}
      </div>
    </>
  );
}
