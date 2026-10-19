import type { ConfidenceFeatures } from "../api/client";
import "./ConfidenceIndicator.css";

interface ConfidenceIndicatorProps {
  score: number;
  threshold: number;
  features: ConfidenceFeatures;
}

const FEATURE_LABELS: Record<keyof ConfidenceFeatures, string> = {
  retrieval_relevance: "Retrieval relevance",
  ticket_resolution_similarity: "Resolution similarity",
  document_freshness: "Document freshness",
  ocr_confidence: "OCR confidence",
  category_risk: "Category risk",
};

// Every feature bar reads "more filled = more confident" except this one — category
// risk is higher when the department classifier is less reliable (see
// docs/confidence-model.md), so a full bar here is bad news, not good news. Styled
// with a distinct color for that reason, not decoration.
const INVERTED_FEATURES = new Set<keyof ConfidenceFeatures>(["category_risk"]);

const FEATURE_ORDER: (keyof ConfidenceFeatures)[] = [
  "retrieval_relevance",
  "ticket_resolution_similarity",
  "document_freshness",
  "ocr_confidence",
  "category_risk",
];

// Radial gauge geometry — a fixed 100x100 viewBox so the arc math (circumference,
// dash-offset, threshold tick angle) is computed once here rather than smeared
// across CSS. 0% sits at the top and the arc sweeps clockwise, like a dial.
const R = 40;
const CX = 50;
const CY = 50;
const CIRCUMFERENCE = 2 * Math.PI * R;

function pointOnCircle(radius: number, fraction: number) {
  const angle = fraction * 2 * Math.PI - Math.PI / 2;
  return { x: CX + radius * Math.cos(angle), y: CY + radius * Math.sin(angle) };
}

function ConfidenceGauge({ score, threshold, passes }: { score: number; threshold: number; passes: boolean }) {
  const scoreFraction = Math.max(0, Math.min(1, score));
  const dashOffset = CIRCUMFERENCE * (1 - scoreFraction);
  const tickInner = pointOnCircle(R - 5, threshold);
  const tickOuter = pointOnCircle(R + 5, threshold);
  const scorePercent = Math.round(score * 100);

  return (
    <div className={`confidence-gauge ${passes ? "confidence-pass" : "confidence-fail"}`}>
      <svg viewBox="0 0 100 100" width={92} height={92} role="img" aria-label={`Confidence score ${scorePercent}%`}>
        <circle cx={CX} cy={CY} r={R} className="confidence-gauge-track" strokeWidth={8} fill="none" />
        <circle
          cx={CX}
          cy={CY}
          r={R}
          className="confidence-gauge-arc"
          strokeWidth={8}
          fill="none"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${CX} ${CY})`}
        />
        <line
          x1={tickInner.x}
          y1={tickInner.y}
          x2={tickOuter.x}
          y2={tickOuter.y}
          className="confidence-gauge-tick"
          strokeWidth={2.5}
          strokeLinecap="round"
        />
        <text x={CX} y={CY - 2} textAnchor="middle" className="confidence-gauge-value">
          {scorePercent}
        </text>
        <text x={CX} y={CY + 15} textAnchor="middle" className="confidence-gauge-unit">
          %
        </text>
      </svg>
    </div>
  );
}

export default function ConfidenceIndicator({ score, threshold, features }: ConfidenceIndicatorProps) {
  const passes = score >= threshold;
  const thresholdPercent = Math.round(threshold * 100);

  return (
    <div className="confidence-indicator">
      <div className="confidence-score-row">
        <ConfidenceGauge score={score} threshold={threshold} passes={passes} />
        <div className="confidence-score-meta">
          <span className={`confidence-score-label ${passes ? "confidence-pass-text" : "confidence-fail-text"}`}>
            {passes ? "Above threshold" : "Below threshold"}
          </span>
          <span className="confidence-score-threshold">
            Gate line at <strong className="tabular-nums">{thresholdPercent}%</strong> for this department
          </span>
          <span className="confidence-score-sub">
            {passes
              ? "This draft cleared the independent confidence check before reaching a reviewer."
              : "This draft did not clear the independent confidence check."}
          </span>
        </div>
      </div>

      <ul className="confidence-feature-list">
        {FEATURE_ORDER.map((key) => {
          const value = features[key];
          const percent = Math.round(value * 100);
          const inverted = INVERTED_FEATURES.has(key);
          return (
            <li key={key} className="confidence-feature-row">
              <span className="confidence-feature-label">{FEATURE_LABELS[key]}</span>
              <div className="confidence-feature-bar-track">
                <div
                  className={`confidence-feature-bar-fill${inverted ? " confidence-feature-bar-risk" : ""}`}
                  style={{ width: `${percent}%` }}
                />
              </div>
              <span className="confidence-feature-value tabular-nums">{percent}%</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
