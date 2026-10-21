import { useEffect, useRef, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  ApiError,
  getTicketDecision,
  getTicketDraft,
  type DraftClaim,
  type DraftPassage,
  type TicketDecision,
  type TicketDraft,
} from "../api/client";
import LaneBadge from "./LaneBadge";
import "./DraftPanel.css";

// Claims below this entailment support are highlighted as unsupported — the same cut
// the claim checker uses for groundedness (ai/grounding/claims.py SUPPORTED).
const SUPPORTED = 0.5;

function pct(x: number | null): string {
  return x === null ? "—" : `${Math.round(x * 100)}%`;
}

// Marks each claim of a step inside the step's own text, so an unsupported claim is
// highlighted in place rather than listed separately. Claims are whitespace-normalised
// substrings of the step (split_claims); a claim that can't be located is left plain.
function renderStep(text: string, claims: DraftClaim[]): ReactNode[] {
  const out: ReactNode[] = [];
  let cursor = 0;
  claims.forEach((claim, i) => {
    const at = text.indexOf(claim.text, cursor);
    if (at < 0) return;
    if (at > cursor) out.push(text.slice(cursor, at));
    const weak = claim.support !== null && claim.support < SUPPORTED;
    out.push(
      <span
        key={i}
        className={weak ? "claim claim-unsupported" : "claim"}
        title={`Support ${pct(claim.support)}${weak ? " — not backed by the cited passage" : ""}`}
      >
        {claim.text}
      </span>
    );
    cursor = at + claim.text.length;
  });
  if (cursor < text.length) out.push(text.slice(cursor));
  return out;
}

function Passages({ passages, active }: { passages: DraftPassage[]; active: number | null }) {
  const refs = useRef<Record<number, HTMLLIElement | null>>({});
  useEffect(() => {
    if (active !== null) refs.current[active]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [active]);

  if (passages.length === 0) {
    return <p className="placeholder-note">Retrieval found no passages in this department.</p>;
  }
  return (
    <ol className="draft-passages">
      {passages.map((p) => (
        <li
          key={p.n}
          ref={(el) => {
            refs.current[p.n] = el;
          }}
          className={p.n === active ? "draft-passage draft-passage-active" : "draft-passage"}
        >
          <div className="draft-passage-header">
            <span className="draft-passage-n">[{p.n}]</span>
            <strong>{p.title}</strong>
            {p.article_key && <span className="status-badge">{p.article_key}</span>}
          </div>
          <p className="draft-passage-text">{p.text}</p>
        </li>
      ))}
    </ol>
  );
}

// The confidence gate's verdict (Week 8). Logged for every draft; ticket routing still
// follows the V1 rule until the Week 9 switch, so this is shown as information.
function GateLine({ decision }: { decision: TicketDecision }) {
  return (
    <div className="gate-line">
      <span className="gate-line-label">Confidence gate</span>
      <LaneBadge lane={decision.lane} />
      {decision.score !== null && <span className="status-badge">score {Math.round(decision.score * 100)}%</span>}
      {decision.label_source === "judge" && (
        <span className="status-badge" title="Thresholds certified on AI-judge labels, not human labels">
          provisional
        </span>
      )}
      {decision.reasons.length > 0 && (
        <span className="gate-line-reasons">Held back by: {decision.reasons.join(" · ")}</span>
      )}
    </div>
  );
}

function DraftBody({ draft, decision, lane }: { draft: TicketDraft; decision?: TicketDecision; lane?: string | null }) {
  const [active, setActive] = useState<number | null>(null);

  const claimsByStep = new Map<number, DraftClaim[]>();
  for (const claim of draft.claims) {
    claimsByStep.set(claim.step_index, [...(claimsByStep.get(claim.step_index) ?? []), claim]);
  }
  const supported = draft.claims.filter((c) => c.support !== null && c.support >= SUPPORTED).length;
  // Assisted lane (Blueprint V2 §9.1): always show the three weakest claims to verify.
  // Elsewhere only claims below the support line are listed.
  const assisted = lane === "assisted";
  const weak = assisted ? draft.weakest : draft.weakest.filter((c) => c.support !== null && c.support < SUPPORTED);

  return (
    <div className="draft-panel">
      {decision && <GateLine decision={decision} />}
      <div className="draft-panel-meta">
        {draft.lane === "escalate" ? (
          <LaneBadge lane="escalate" />
        ) : draft.lane === "fast" || draft.lane === "assisted" ? (
          <LaneBadge lane={draft.lane} />
        ) : (
          <span className="status-badge" title="Fast and assisted lanes arrive with the Week 9 gate">
            Lane: not yet assigned
          </span>
        )}
        {draft.shown && (
          <span className="status-badge" title="Claims entailed by their cited passage">
            {supported} of {draft.claims.length} claims supported
          </span>
        )}
      </div>

      <div className="draft-panel-grid">
        <section aria-label="Draft">
          {draft.shown ? (
            <ol className="draft-steps">
              {draft.steps.map((step, i) => (
                <li key={i}>
                  {renderStep(step.text, claimsByStep.get(i) ?? [])}{" "}
                  {step.citations.map((n) => (
                    <button
                      key={n}
                      type="button"
                      className={n === active ? "citation-chip citation-chip-active" : "citation-chip"}
                      onMouseEnter={() => setActive(n)}
                      onFocus={() => setActive(n)}
                      onClick={() => setActive(n)}
                      aria-label={`Show passage ${n}`}
                    >
                      {n}
                    </button>
                  ))}
                </li>
              ))}
            </ol>
          ) : (
            <p className="placeholder-note">
              No AI draft in the escalation lane. Work from the evidence alongside.
            </p>
          )}

          {draft.shown && weak.length > 0 && (
            <div className="draft-weakest">
              <h4>{assisted ? "Weakest claims: verify these first" : "Check these claims"}</h4>
              <ul>
                {weak.map((c) => (
                  <li key={`${c.step_index}-${c.claim_index}`}>
                    Step {c.step_index + 1}: “{c.text}” <span className="draft-support">{pct(c.support)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {draft.missing_information.length > 0 && (
            <div className="draft-missing">
              <h4>Not covered by the evidence</h4>
              <ul>
                {draft.missing_information.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section aria-label="Evidence">
          <h4 className="draft-evidence-heading">Evidence</h4>
          <Passages passages={draft.evidence} active={active} />
        </section>
      </div>

      <p className="draft-provenance">
        {draft.model} · {draft.prompt_version}
      </p>
    </div>
  );
}

// The structured draft with inline citations and a side-by-side evidence view
// (Roadmap Week 5). `version` changes whenever the ticket moves on, so a draft that
// lands while the page is open is fetched without a reload.
export default function DraftPanel({
  token,
  ticketId,
  version,
  lane,
}: {
  token: string;
  ticketId: string;
  version: string;
  lane?: string | null;
}) {
  const query = useQuery({
    queryKey: ["draft", ticketId, version],
    queryFn: () => getTicketDraft(token, ticketId),
    retry: (count, err) => !(err instanceof ApiError && err.status === 404) && count < 1,
  });

  const decision = useQuery({
    queryKey: ["decision", ticketId, version],
    queryFn: () => getTicketDecision(token, ticketId),
    retry: false,
  });

  if (query.isPending) return <p className="placeholder-note">Loading the draft…</p>;
  if (query.error) {
    if (query.error instanceof ApiError && query.error.status === 404) {
      return <p className="placeholder-note">No draft has been generated for this ticket yet.</p>;
    }
    return (
      <div className="form-error">
        Could not load the draft.{" "}
        <button type="button" className="link-button" onClick={() => query.refetch()}>
          Try again
        </button>
      </div>
    );
  }
  return <DraftBody draft={query.data} decision={decision.data} lane={lane} />;
}
