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

export default function ConfidenceIndicator({ score, threshold, features }: ConfidenceIndicatorProps) {
  const passes = score >= threshold;
  const scorePercent = Math.round(score * 100);
  const thresholdPercent = Math.round(threshold * 100);

  return (
    <div className="confidence-indicator">
      <div className="confidence-score-row">
        <div className={`confidence-score-badge ${passes ? "confidence-pass" : "confidence-fail"}`}>
          {scorePercent}%
        </div>
        <div className="confidence-score-meta">
          <span className="confidence-score-label">
            {passes ? "Above threshold" : "Below threshold"}
          </span>
          <span className="confidence-score-threshold">Department threshold: {thresholdPercent}%</span>
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
              <span className="confidence-feature-value">{percent}%</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
