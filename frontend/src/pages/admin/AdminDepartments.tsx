import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../../components";
import {
  listDepartments,
  listUsers,
  listKnowledgeBase,
  ApiError,
  type Department,
  type User,
  type KnowledgeBaseArticle,
} from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

// Departments at a glance: engineers and knowledge-base articles per department.
// Until Week 9 this screen also set a per-department confidence threshold. That number no
// longer decides anything: every ticket's lane comes from the certified gate thresholds,
// which are global and versioned (Error budget page), so the control was removed in the
// Week 11 bug bash rather than left in place doing nothing.
export default function AdminDepartments() {
  const { token } = useAuth();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [articles, setArticles] = useState<KnowledgeBaseArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listDepartments(token), listUsers(token), listKnowledgeBase(token)])
      .then(([d, u, a]) => {
        setDepartments(d);
        setUsers(u);
        setArticles(a);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load departments"))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <Card title="Departments">
      <p className="placeholder-note">
        Which lane a ticket goes to (fast, assisted or escalate) is decided by the certified gate thresholds, the same
        for every department. See <Link to="/admin/error-budget">Error budget</Link>.
      </p>
      {loading && <p className="placeholder-note">Loading...</p>}
      {error && <p className="form-error">{error}</p>}
      {!loading && !error && (
        <div className="dept-panel-list">
          {departments.map((dept) => {
            const engineerCount = users.filter((u) => u.department_id === dept.id && u.role === "department_engineer").length;
            const articleCount = articles.filter((a) => a.department_id === dept.id).length;
            return (
              <div className="dept-panel" key={dept.id}>
                <div className="dept-panel-header">
                  <div>
                    <strong>{dept.name}</strong>
                    <span className="dept-panel-meta">
                      {engineerCount} engineer{engineerCount === 1 ? "" : "s"} · {articleCount} KB article
                      {articleCount === 1 ? "" : "s"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
