import { useQuery } from "@tanstack/react-query";
import { BarChart, Card, DonutChart, LaneBadge, type Lane } from "../../components";
import { ApiError, getLaneAnalytics } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

const LANES: Lane[] = ["fast", "assisted", "escalate"];
const LANE_LABEL: Record<Lane, string> = { fast: "Fast", assisted: "Assisted", escalate: "Escalated" };
const LANE_COLOR: Record<Lane, string> = {
  fast: "var(--lane-fast)",
  assisted: "var(--lane-assisted)",
  escalate: "var(--lane-escalate)",
};

const seconds = (ms: number | null) => (ms === null ? "—" : `${(ms / 1000).toFixed(1)} s`);
const pct = (x: number | null) => (x === null ? "—" : `${Math.round(x * 100)}%`);

// Dashboard v1 (Roadmap Week 9): how the confidence gate routes live tickets.
export default function LaneDashboard() {
  const { token } = useAuth();
  const q = useQuery({ queryKey: ["lane-analytics"], queryFn: () => getLaneAnalytics(token!), enabled: !!token });

  if (q.isPending) return <p className="placeholder-note">Loading lane analytics…</p>;
  if (q.error) {
    return <p className="form-error">{q.error instanceof ApiError ? q.error.message : "Could not load lane analytics"}</p>;
  }
  const a = q.data;

  return (
    <Card title="Confidence gate lanes">
      {a.total === 0 ? (
        <p className="placeholder-note">No live ticket has been through the gate yet.</p>
      ) : (
        <div className="lane-dashboard">
          <DonutChart
            ariaLabel="Tickets per lane"
            centerLabel={`${a.total} tickets`}
            data={LANES.map((l) => ({ label: LANE_LABEL[l], value: a.lane_mix[l], color: LANE_COLOR[l] }))}
          />
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Lane</th>
                <th className="col-right">Tickets</th>
                <th className="col-right">Accepted or edited</th>
                <th className="col-right">Pipeline time</th>
                <th className="col-right">Decision time</th>
              </tr>
            </thead>
            <tbody>
              {LANES.map((l) => (
                <tr key={l}>
                  <td>
                    <LaneBadge lane={l} />
                  </td>
                  <td className="col-right tabular-nums">{a.lane_mix[l]}</td>
                  <td className="col-right tabular-nums">{pct(a.acceptance_rate[l])}</td>
                  <td className="col-right tabular-nums">{seconds(a.median_pipeline_ms[l])}</td>
                  <td className="col-right tabular-nums">{seconds(a.median_decision_ms[l])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {a.total > 0 && (
        <>
          <h4 className="lane-dashboard-sub">Gate confidence, all lanes</h4>
          <BarChart
            ariaLabel="Tickets per confidence bin"
            height={120}
            data={a.confidence_bins.assisted.map((_, i) => ({
              label: `${i * 10}–${i * 10 + 10}%`,
              value: LANES.reduce((sum, l) => sum + a.confidence_bins[l][i], 0),
            }))}
          />
          <p className="placeholder-note">
            Median times. "Accepted or edited" is the share of engineer decisions on shown drafts in that lane. Escalated
            tickets have no AI draft; they are resolved through the approval queue and are not counted there.
          </p>
        </>
      )}
    </Card>
  );
}
