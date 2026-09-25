import { useState } from "react";
import "./charts.css";

export interface DonutDatum {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  data: DonutDatum[];
  ariaLabel: string;
  centerLabel?: string;
}

const R = 40;
const CX = 50;
const CY = 50;
const STROKE = 14;
const CIRCUMFERENCE = 2 * Math.PI * R;

// Identity chart (which status/department a slice is) — always legend + a hover
// tooltip with the exact count, never color-only. A 2px surface gap separates
// adjacent segments so no two colors touch directly.
export default function DonutChart({ data, ariaLabel, centerLabel }: DonutChartProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const total = data.reduce((sum, d) => sum + d.value, 0);

  let cursor = 0;
  const segments = data.map((d, i) => {
    const fraction = total > 0 ? d.value / total : 0;
    const gap = total > 0 && fraction > 0 ? 1.2 : 0; // degrees of surface gap between segments
    const startFraction = cursor;
    cursor += fraction;
    return { ...d, i, startFraction, fraction, gap };
  });

  return (
    <div className="viz-donut-root">
      <svg
        viewBox="0 0 100 100"
        width={148}
        height={148}
        role="img"
        aria-label={ariaLabel}
        className="viz-donut-svg"
      >
        <circle cx={CX} cy={CY} r={R} fill="none" stroke="var(--color-surface-alt)" strokeWidth={STROKE} />
        {segments.map((seg) => {
          if (seg.fraction <= 0) return null;
          const dash = Math.max(CIRCUMFERENCE * seg.fraction - seg.gap, 0);
          const gapDash = CIRCUMFERENCE - dash;
          const offset = CIRCUMFERENCE * (1 - seg.startFraction) + seg.gap / 2;
          return (
            <circle
              key={seg.label}
              cx={CX}
              cy={CY}
              r={R}
              fill="none"
              stroke={seg.color}
              strokeWidth={hovered === seg.i ? STROKE + 2 : STROKE}
              strokeDasharray={`${dash} ${gapDash}`}
              strokeDashoffset={offset}
              strokeLinecap="butt"
              transform={`rotate(-90 ${CX} ${CY})`}
              className="viz-donut-segment"
              onMouseEnter={() => setHovered(seg.i)}
              onMouseLeave={() => setHovered((h) => (h === seg.i ? null : h))}
            />
          );
        })}
        {centerLabel && (
          <text x={CX} y={CY + 4} textAnchor="middle" className="viz-donut-center">
            {centerLabel}
          </text>
        )}
      </svg>

      <ul className="viz-legend">
        {segments.map((seg) => (
          <li
            key={seg.label}
            className={`viz-legend-item${hovered === seg.i ? " viz-legend-item-active" : ""}`}
            onMouseEnter={() => setHovered(seg.i)}
            onMouseLeave={() => setHovered((h) => (h === seg.i ? null : h))}
          >
            <span className="viz-legend-swatch" style={{ background: seg.color }} />
            <span className="viz-legend-label">{seg.label}</span>
            <span className="viz-legend-value tabular-nums">{seg.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
