import { useState } from "react";
import type { CalibrationBucket } from "../../api/client";
import "./charts.css";

interface CalibrationChartProps {
  data: CalibrationBucket[];
}

// A reliability diagram: for each confidence decile, how often a human actually
// agreed with the AI. The dashed tick marks where a perfectly-calibrated model
// would land (the bucket's own midpoint) — a bar landing right at its tick means
// "70-80% confident" really does mean ~75% right; well below it means the model is
// overconfident in that range, well above means underconfident.
export default function CalibrationChart({ data }: CalibrationChartProps) {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <div className="calibration-chart">
      {data.map((bucket, i) => {
        const floor = Number(bucket.label.split("-")[0]);
        const idealPct = floor + 5;
        const hasData = bucket.count > 0 && bucket.actual_agreement_rate !== null;
        const actualPct = hasData ? Math.round((bucket.actual_agreement_rate as number) * 100) : 0;

        return (
          <div
            key={bucket.label}
            className="calibration-col"
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered((h) => (h === i ? null : h))}
          >
            {hovered === i && hasData && (
              <div className="viz-tooltip calibration-tooltip">
                <strong>{bucket.label} confidence</strong>
                <span>{actualPct}% actual agreement</span>
                <span>{bucket.count} labeled ticket{bucket.count === 1 ? "" : "s"}</span>
              </div>
            )}
            <div className="calibration-track">
              <div className="calibration-ideal-tick" style={{ bottom: `${idealPct}%` }} />
              {hasData && (
                <div
                  className={`calibration-bar${actualPct < idealPct - 7 ? " calibration-bar-under" : actualPct > idealPct + 7 ? " calibration-bar-over" : " calibration-bar-good"}`}
                  style={{ height: `${actualPct}%` }}
                />
              )}
            </div>
            <span className="calibration-count tabular-nums">{bucket.count || "—"}</span>
            <span className="calibration-label">{bucket.label.replace("%", "")}</span>
          </div>
        );
      })}
    </div>
  );
}
