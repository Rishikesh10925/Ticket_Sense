import { useState } from "react";
import "./charts.css";

export interface BarDatum {
  label: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: BarDatum[];
  valueFormatter?: (value: number) => string;
  height?: number;
  ariaLabel: string;
}

const DEFAULT_COLOR = "var(--color-primary)";

// A single-series vertical bar chart — thin bars, rounded data-ends anchored to the
// baseline, a value label over every bar (never color-only — several of the
// categorical slots this chart is fed sit below 3:1 contrast against a white
// surface, per dataviz skill's relief rule) and a hover tooltip per bar.
export default function BarChart({ data, valueFormatter, height = 160, ariaLabel }: BarChartProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const max = Math.max(...data.map((d) => d.value), 1);
  const format = valueFormatter ?? ((v: number) => String(v));

  return (
    <div className="viz-bar-chart" style={{ height }} role="img" aria-label={ariaLabel}>
      {data.map((d, i) => {
        const pct = (d.value / max) * 100;
        return (
          <div
            key={d.label}
            className="viz-bar-col"
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered((h) => (h === i ? null : h))}
          >
            {hovered === i && (
              <div className="viz-tooltip">
                <strong>{d.label}</strong>
                <span>{format(d.value)}</span>
              </div>
            )}
            <span className="viz-bar-value tabular-nums">{format(d.value)}</span>
            <div className="viz-bar-track">
              <div
                className="viz-bar-fill"
                style={{ height: `${Math.max(pct, d.value > 0 ? 2 : 0)}%`, background: d.color ?? DEFAULT_COLOR }}
              />
            </div>
            <span className="viz-bar-label">{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}
