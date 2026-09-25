import { useEffect, useState } from "react";
import { Card, StatCard } from "../../components";
import { listKnowledgeBase, listDepartments, ApiError, type KnowledgeBaseArticle, type Department } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

export default function AdminKnowledgeBase() {
  const { token } = useAuth();
  const [articles, setArticles] = useState<KnowledgeBaseArticle[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listKnowledgeBase(token), listDepartments(token)])
      .then(([a, d]) => {
        setArticles(a);
        setDepartments(d);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the knowledge base"))
      .finally(() => setLoading(false));
  }, [token]);

  const departmentName = (id: string) => departments.find((d) => d.id === id)?.name ?? "—";

  return (
    <>
      {!loading && !error && (
        <div className="stat-grid">
          <StatCard label="Articles" value={articles.length} accent />
          <StatCard label="Departments covered" value={departments.length} tone="info" />
        </div>
      )}
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
                  <td>
                    <span className="dept-chip">{departmentName(article.department_id)}</span>
                  </td>
                  <td>{new Date(article.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
