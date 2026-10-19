import "./LaneBadge.css";

// The three V2 lanes (Blueprint §9.1, wireframes-v2 §2). Shape and colour together, so
// the badge reads correctly for colour-blind users and in greyscale prints.
export type Lane = "fast" | "assisted" | "escalate";

const LANES: Record<Lane, { glyph: string; label: string; title: string }> = {
  fast: { glyph: "●", label: "Fast", title: "Fast lane: pre-filled draft, one-click review" },
  assisted: { glyph: "◐", label: "Assisted", title: "Assisted lane: verify the draft and its weakest claims" },
  escalate: { glyph: "○", label: "Escalated", title: "Escalation lane: no AI draft, evidence only" },
};

export default function LaneBadge({ lane }: { lane: Lane }) {
  const l = LANES[lane];
  return (
    <span className={`lane-badge lane-${lane}`} title={l.title}>
      <span aria-hidden="true">{l.glyph}</span> {l.label}
    </span>
  );
}
