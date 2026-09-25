import { CheckIcon, AlertTriangleIcon } from "./icons";
import "./Timeline.css";

interface TimelineProps {
  status: string;
}

const STATUS_INDEX: Record<string, number> = {
  submitted: 0,
  classified: 1,
  routed: 2,
  drafted: 3,
  escalated: 3,
  reviewed: 4,
  closed: 4,
};

// A fixed 5-stage view of the pipeline (see docs/langgraph-pipeline.md) — the 4th
// stage's label and tone switch to "Escalated" when the confidence gate (or a
// reviewer's Doubt) sent the ticket to a human instead of drafting normally, and the
// last stage reads "Closed" rather than "Reviewed" when an admin rejected an
// escalation outright, with no engineer or response involved.
function buildSteps(status: string) {
  const isEscalatedTrack = status === "escalated" || status === "closed";
  const isClosed = status === "closed";
  return [
    { key: "submitted", label: "Submitted" },
    { key: "classified", label: "Classified" },
    { key: "routed", label: "Routed" },
    { key: "drafted", label: isEscalatedTrack ? "Escalated" : "Drafted", warn: isEscalatedTrack },
    { key: "reviewed", label: isClosed ? "Closed" : "Reviewed" },
  ];
}

export default function Timeline({ status }: TimelineProps) {
  const currentIndex = STATUS_INDEX[status] ?? 0;
  const steps = buildSteps(status);

  return (
    <ol className="ticket-timeline" aria-label="Ticket progress">
      {steps.map((step, i) => {
        const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "pending";
        const isWarnCurrent = state === "current" && step.warn;
        return (
          <li key={step.key} className={`ticket-timeline-step ticket-timeline-${state}`}>
            <span className={`ticket-timeline-dot${isWarnCurrent ? " ticket-timeline-dot-warn" : ""}`}>
              {state === "done" ? (
                <CheckIcon width={11} height={11} />
              ) : isWarnCurrent ? (
                <AlertTriangleIcon width={11} height={11} />
              ) : null}
            </span>
            <span className="ticket-timeline-label">{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
