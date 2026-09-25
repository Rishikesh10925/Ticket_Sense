import { useEffect, useState } from "react";
import { BarChart, CalibrationChart, Card, StatCard } from "../../components";
import { getConfidenceModelReport, ApiError, type ConfidenceModelReport } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

export default function AdminModelHealth() {
  const { token } = useAuth();
  const [report, setReport] = useState<ConfidenceModelReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setError(null);
    getConfidenceModelReport(token)
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load the model report"))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <p className="placeholder-note">Loading...</p>;
  if (error) return <p className="form-error">{error}</p>;
  if (!report) return null;

  const trendData = report.daily_trend.map((p) => ({
    label: new Date(p.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    value: Math.round(p.agreement_rate * 100),
  }));
  const volumeData = report.daily_trend.map((p) => ({
    label: new Date(p.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    value: p.count,
  }));

  return (
    <>
      <div className="stat-grid">
        <StatCard label="Labeled tickets" value={report.total_labeled} accent />
        <StatCard
          label="Overall agreement rate"
          value={report.overall_agreement_rate !== null ? `${Math.round(report.overall_agreement_rate * 100)}%` : "—"}
          tone="success"
        />
        <StatCard label="From real reviews" value={report.real_labeled} tone="info" />
        <StatCard label="From synthetic bootstrap" value={report.synthetic_labeled} />
      </div>

      <Card title="Calibration">
        {report.total_labeled === 0 ? (
          <p className="placeholder-note">
            No labeled feedback yet — this fills in once engineers review drafted tickets (or the synthetic
            bootstrap set is seeded).
          </p>
        ) : (
          <>
            <CalibrationChart data={report.calibration} />
            <p className="placeholder-note draft-status-legend">
              For each confidence decile, the bar is how often a human actually agreed with the AI's draft
              (accepted or lightly edited it); the dashed line marks where a perfectly-calibrated model would
              land — the bucket's own midpoint. A bar well below its line means the model is{" "}
              <strong>overconfident</strong> in that range; well above means <strong>underconfident</strong>.
              Empty deciles (—) have no labeled tickets yet.
            </p>
          </>
        )}
      </Card>

      <Card title="Agreement rate over time">
        {report.daily_trend.length <= 1 ? (
          <p className="placeholder-note">
            Only {report.daily_trend.length === 1 ? "one day" : "no days"} of labeled data exists so far, so
            there's no trend to show yet — this chart fills in day by day as more tickets get reviewed.
          </p>
        ) : (
          <BarChart data={trendData} ariaLabel="Agreement rate by day" valueFormatter={(v) => `${v}%`} />
        )}
      </Card>

      <Card title="Tickets scored per day">
        <BarChart data={volumeData} ariaLabel="Tickets scored per day" height={120} />
      </Card>
    </>
  );
}
