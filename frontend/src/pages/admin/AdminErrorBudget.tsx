import { useQuery } from "@tanstack/react-query";
import { BarChart, Card, StatCard } from "../../components";
import { ApiError, getGateThresholds, type GateThresholdSet } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

const pct = (x: number | null | undefined) => (x === null || x === undefined ? "—" : `${Math.round(x * 100)}%`);

function thresholdLabel(t: number | null) {
  return t === null ? "not certified (lane closed)" : t.toFixed(2);
}

// Stat cards have room for a number, not a sentence.
function thresholdValue(t: number | null) {
  return t === null ? "closed" : t.toFixed(2);
}

// Blueprint V2 §13.4: "The administrator screen shows the expected coverage for any
// chosen alpha so the trade-off is visible." Read-only: a new budget means certifying a
// new threshold set on the calibration split, never typing a number in here.
export default function AdminErrorBudget() {
  const { token } = useAuth();
  const q = useQuery({ queryKey: ["gate-thresholds"], queryFn: () => getGateThresholds(token!), enabled: !!token });

  if (q.isPending) return <p className="placeholder-note">Loading the error budget…</p>;
  if (q.error) {
    return <p className="form-error">{q.error instanceof ApiError ? q.error.message : "Could not load thresholds"}</p>;
  }
  const { active, alpha_curve: curve, calibration_n: n, history } = q.data;

  if (!active) {
    return (
      <Card title="Error budget">
        <p className="placeholder-note">
          No certified threshold set is active, so every draft escalates. Train the confidence model and load
          its thresholds with <code>python -m app.scripts.load_thresholds</code>.
        </p>
      </Card>
    );
  }

  return (
    <>
      {active.label_source === "judge" && (
        <div className="budget-warning" role="note">
          <strong>Provisional.</strong> These thresholds were certified on the AI judge's labels, not on human
          labels. They prove the pipeline works; they are not the guarantee the project reports.
        </div>
      )}

      <div className="stat-grid">
        <StatCard label="Fast lane: error budget" value={pct(active.alpha_fast)} accent />
        <StatCard
          label={active.fast_threshold === null ? "Fast lane: no threshold certified" : "Fast lane: threshold"}
          value={thresholdValue(active.fast_threshold)}
        />
        <StatCard label="Assisted lane: error budget" value={pct(active.alpha_assisted)} tone="info" />
        <StatCard
          label={active.assisted_threshold === null ? "Assisted lane: no threshold certified" : "Assisted lane: threshold"}
          value={thresholdValue(active.assisted_threshold)}
        />
      </div>

      <Card title="What each error budget allows">
        <p className="placeholder-note">
          For each budget (the most unacceptable drafts a lane may show), the share of calibration drafts the
          gate can show while the budget holds with {pct(1 - active.delta)} confidence
          {n ? ` (${n} calibration drafts)` : ""}. A stricter budget shows fewer drafts; 0% means no threshold
          could be certified at that budget.
        </p>
        {curve.length > 0 ? (
          <BarChart
            ariaLabel="Certified coverage by error budget"
            data={curve.map((c) => ({ label: pct(c.alpha), value: Math.round(c.coverage * 100) }))}
            valueFormatter={(v) => `${v}%`}
          />
        ) : (
          <p className="placeholder-note">This threshold set was loaded without a coverage curve.</p>
        )}
      </Card>

      <Card title="Threshold sets">
        <table className="ticket-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Model</th>
              <th>Labels</th>
              <th>Fast</th>
              <th>Assisted</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {history.map((h: GateThresholdSet) => (
              <tr key={h.version}>
                <td>{h.version}</td>
                <td>{h.model_version}</td>
                <td>{h.label_source === "judge" ? "AI judge (provisional)" : "human"}</td>
                <td>{thresholdLabel(h.fast_threshold)}</td>
                <td>{thresholdLabel(h.assisted_threshold)}</td>
                <td>{new Date(h.created_at).toLocaleString()}</td>
                <td>{h.active && <span className="status-badge">active</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
