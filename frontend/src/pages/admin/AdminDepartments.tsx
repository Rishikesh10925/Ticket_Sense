import { useEffect, useState, type CSSProperties } from "react";
import { Button, Card } from "../../components";
import {
  listDepartments,
  listUsers,
  listKnowledgeBase,
  updateDepartmentThreshold,
  ApiError,
  type Department,
  type User,
  type KnowledgeBaseArticle,
} from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { useToast } from "../../components";

// Mirrors backend/app/schemas/tickets.py's CUSTOMER_READY_CONFIDENCE_THRESHOLD — the
// one boundary every department shares and can't change from here, unlike the
// per-department slider below it.
const AUTO_RESOLVE_PERCENT = 85;

// A live picture of what a given threshold actually does to a ticket, since a bare
// "55%" slider doesn't tell an admin what happens on either side of that line. Three
// zones, always in the same order and colors as confidence rises: admin has to
// decide -> an engineer reviews -> nothing, it just goes out.
function ZoneBar({ thresholdPercent }: { thresholdPercent: number }) {
  const clamped = Math.min(Math.max(thresholdPercent, 0), 100);
  const adminWidth = Math.min(clamped, AUTO_RESOLVE_PERCENT);
  const engineerWidth = Math.max(0, AUTO_RESOLVE_PERCENT - clamped);
  const autoWidth = 100 - AUTO_RESOLVE_PERCENT;

  return (
    <div
      className="zone-bar"
      role="img"
      aria-label={`Below ${clamped}% goes to admin approval, ${clamped}% to ${AUTO_RESOLVE_PERCENT}% goes to an engineer, ${AUTO_RESOLVE_PERCENT}% and up auto-resolves`}
    >
      <div className="zone-bar-segment zone-bar-admin" style={{ width: `${adminWidth}%` }} />
      <div className="zone-bar-segment zone-bar-engineer" style={{ width: `${engineerWidth}%` }} />
      <div className="zone-bar-segment zone-bar-auto" style={{ width: `${autoWidth}%` }} />
    </div>
  );
}

function ZoneLegend({ thresholdPercent }: { thresholdPercent: number }) {
  const clamped = Math.min(Math.max(thresholdPercent, 0), 100);
  return (
    <ul className="zone-legend">
      <li className="zone-legend-admin">
        <span className="zone-legend-dot" />
        <strong>0–{clamped}%</strong> goes to your Approvals queue
      </li>
      <li className="zone-legend-engineer">
        <span className="zone-legend-dot" />
        <strong>
          {clamped}–{AUTO_RESOLVE_PERCENT}%
        </strong>{" "}
        goes to an engineer to review
      </li>
      <li className="zone-legend-auto">
        <span className="zone-legend-dot" />
        <strong>{AUTO_RESOLVE_PERCENT}–100%</strong> auto-resolves straight to the customer
      </li>
    </ul>
  );
}

export default function AdminDepartments() {
  const { token } = useAuth();
  const { notify } = useToast();

  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [articles, setArticles] = useState<KnowledgeBaseArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [thresholdDrafts, setThresholdDrafts] = useState<Record<string, string>>({});
  const [savingThresholdId, setSavingThresholdId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    Promise.all([listDepartments(token), listUsers(token), listKnowledgeBase(token)])
      .then(([d, u, a]) => {
        setDepartments(d);
        setUsers(u);
        setArticles(a);
        setThresholdDrafts(Object.fromEntries(d.map((dept) => [dept.id, String(dept.confidence_threshold)])));
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load departments"))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleSaveThreshold(deptId: string, deptName: string) {
    if (!token) return;
    const value = Number(thresholdDrafts[deptId]);
    if (Number.isNaN(value) || value < 0 || value > 1) {
      notify("Threshold must be a number between 0 and 1.", "error");
      return;
    }
    setSavingThresholdId(deptId);
    try {
      const updated = await updateDepartmentThreshold(token, deptId, value);
      setDepartments((prev) => prev.map((d) => (d.id === deptId ? updated : d)));
      notify(`${deptName}'s confidence threshold set to ${Math.round(value * 100)}%.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not update threshold", "error");
    } finally {
      setSavingThresholdId(null);
    }
  }

  return (
    <Card title="Departments">
      {loading && <p className="placeholder-note">Loading...</p>}
      {error && <p className="form-error">{error}</p>}
      {!loading && !error && (
        <div className="dept-panel-list">
          {departments.map((dept) => {
            const draft = thresholdDrafts[dept.id] ?? String(dept.confidence_threshold);
            const draftPercent = Math.round(Number(draft) * 100);
            const changed = Number(draft) !== dept.confidence_threshold;
            const engineerCount = users.filter((u) => u.department_id === dept.id && u.role === "department_engineer").length;
            const articleCount = articles.filter((a) => a.department_id === dept.id).length;

            return (
              <div className="dept-panel" key={dept.id}>
                <div className="dept-panel-header">
                  <div>
                    <strong>{dept.name}</strong>
                    <span className="dept-panel-meta">
                      {engineerCount} engineer{engineerCount === 1 ? "" : "s"} · {articleCount} KB article{articleCount === 1 ? "" : "s"}
                    </span>
                  </div>
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
                      onChange={(e) => setThresholdDrafts((prev) => ({ ...prev, [dept.id]: e.target.value }))}
                    />
                    <span className={`threshold-readout tabular-nums${changed ? " threshold-readout-changed" : ""}`}>
                      {draftPercent}%
                    </span>
                    <Button
                      variant="secondary"
                      className="btn-sm"
                      disabled={!changed || savingThresholdId === dept.id}
                      onClick={() => handleSaveThreshold(dept.id, dept.name)}
                    >
                      {savingThresholdId === dept.id ? "Saving…" : "Save"}
                    </Button>
                  </div>
                </div>

                <ZoneBar thresholdPercent={draftPercent} />
                <ZoneLegend thresholdPercent={draftPercent} />
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
