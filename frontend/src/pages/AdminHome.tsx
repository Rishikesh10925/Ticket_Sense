import { useEffect, useState } from "react";
import { Card, StatCard } from "../components";
import {
  listUsers,
  listDepartments,
  listKnowledgeBase,
  ApiError,
  type User,
  type Department,
  type KnowledgeBaseArticle,
} from "../api/client";
import { useAuth } from "../auth/AuthContext";

type Section = "users" | "departments" | "knowledge-base" | "analytics" | "settings";

const SECTIONS: { id: Section; label: string; available: boolean }[] = [
  { id: "users", label: "Users", available: true },
  { id: "departments", label: "Departments", available: true },
  { id: "knowledge-base", label: "Knowledge base", available: true },
  { id: "analytics", label: "Analytics", available: false },
  { id: "settings", label: "Settings", available: false },
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

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listUsers(token), listDepartments(token), listKnowledgeBase(token)])
      .then(([u, d, a]) => {
        setUsers(u);
        setDepartments(d);
        setArticles(a);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load admin data"))
      .finally(() => setLoading(false));
  }, [token]);

  const departmentName = (id: string) => departments.find((d) => d.id === id)?.name ?? "—";

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
          <StatCard label="Knowledge base articles" value={articles.length} />
        </div>
      )}

      <div className="admin-layout">
        <Card title="Sections">
          <ul className="section-list">
            {SECTIONS.map((s) => (
              <li
                key={s.id}
                className={s.id === section ? "section-active" : ""}
                onClick={() => setSection(s.id)}
              >
                {s.label}
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
            {!loading && !error && (
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Engineers</th>
                    <th>KB articles</th>
                  </tr>
                </thead>
                <tbody>
                  {departments.map((dept) => (
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
                    </tr>
                  ))}
                </tbody>
              </table>
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
