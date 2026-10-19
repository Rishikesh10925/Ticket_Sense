import { useCallback, useEffect, useRef, useState } from "react";
import { Button, Card, useToast } from "../components";
import { useAuth } from "../auth/AuthContext";
import {
  ApiError,
  REASON_CODES,
  getNextAnnotation,
  submitAnnotation,
  type AnnotationItem,
  type ReasonCode,
  type RubricLabel,
} from "../api/client";
import "./Annotate.css";

// Blinded labelling screen for outside reviewers (docs/annotation-tool.md, wireframes-v2
// §4). It never shows a confidence score, lane, model or ticket type: the API does not
// send them. Keys 1-4 pick a label; Ctrl+Enter saves.
const LABELS: { value: RubricLabel; name: string; hint: string }[] = [
  { value: "A", name: "Acceptable", hint: "Correct and complete enough to send as is" },
  { value: "M", name: "Minor edit", hint: "Correct; under two minutes of wording or order fixes" },
  { value: "R", name: "Major rework", hint: "Missing key steps or has wrong steps; rewriting is faster" },
  { value: "W", name: "Wrong or unsafe", hint: "Could mislead or cause harm, or uses a wrong source" },
];

const REASON_TEXT: Record<ReasonCode, string> = {
  wrong_source: "Wrong source",
  outdated_source: "Outdated source",
  missing_step: "Missing step",
  invented_step: "Invented step",
  did_not_address_question: "Did not address the question",
  tone: "Tone",
  formatting: "Formatting",
  other: "Other",
};

export default function Annotate() {
  const { token } = useAuth();
  const { notify } = useToast();
  const [item, setItem] = useState<AnnotationItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [finished, setFinished] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [label, setLabel] = useState<RubricLabel | null>(null);
  const [reasons, setReasons] = useState<ReasonCode[]>([]);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const startedAt = useRef<number>(Date.now());

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const next = await getNextAnnotation(token);
      setItem(next);
      setFinished(next === null);
      setLabel(null);
      setReasons([]);
      setNote("");
      startedAt.current = Date.now();
      setElapsed(0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the next draft");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const id = window.setInterval(() => setElapsed(Math.floor((Date.now() - startedAt.current) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [item]);

  const submit = useCallback(
    async (skippedReason?: string) => {
      if (!token || !item || saving) return;
      if (!skippedReason && !label) return;
      setSaving(true);
      try {
        await submitAnnotation(token, item.assignment_id, {
          label: skippedReason ? undefined : (label ?? undefined),
          reason_codes: skippedReason ? [] : reasons,
          note: note.trim() || undefined,
          skipped_reason: skippedReason,
          time_taken_ms: Date.now() - startedAt.current,
        });
        await load();
      } catch (err) {
        notify(err instanceof ApiError ? err.message : "Could not save the label", "error");
      } finally {
        setSaving(false);
      }
    },
    [token, item, saving, label, reasons, note, load, notify],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLTextAreaElement) {
        if (e.key === "Enter" && e.ctrlKey) submit();
        return;
      }
      const index = ["1", "2", "3", "4"].indexOf(e.key);
      if (index >= 0) setLabel(LABELS[index].value);
      if (e.key === "Enter" && e.ctrlKey) submit();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [submit]);

  function toggleReason(code: ReasonCode) {
    setReasons((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));
  }

  if (loading) return <p className="placeholder-note">Loading the next draft…</p>;
  if (error) return <p className="form-error">{error}</p>;
  if (finished || !item) {
    return (
      <Card title="All done">
        <p>You have labelled every draft assigned to you. Thank you!</p>
      </Card>
    );
  }

  const { done, total } = item.progress;
  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");

  return (
    <div className="annotate">
      <div className="annotate-bar">
        <div>
          <strong>
            {done + 1} / {total}
          </strong>{" "}
          drafts · rubric {item.rubric_version}
        </div>
        <div className="annotate-progress" role="progressbar" aria-valuenow={done} aria-valuemax={total}>
          <span style={{ width: `${total ? (100 * done) / total : 0}%` }} />
        </div>
        <div className="annotate-timer" aria-label="Time on this draft">
          {minutes}:{seconds}
        </div>
      </div>

      <div className="annotate-grid">
        <div className="annotate-main">
          <Card title="Ticket">
            <p className="annotate-subject">{item.ticket.subject}</p>
            <p className="annotate-body">{item.ticket.body}</p>
            {item.ticket.attachment_text && <pre className="annotate-log">{item.ticket.attachment_text}</pre>}
          </Card>

          <Card title="AI draft">
            {item.draft.can_answer === false && (
              <p className="annotate-flag">The draft says the evidence is not enough to answer.</p>
            )}
            <ol className="annotate-steps">
              {item.draft.steps.map((step, i) => (
                <li key={i}>
                  {step.text}{" "}
                  {step.citations.map((n) => (
                    <span key={n} className="annotate-cite">
                      [{n}]
                    </span>
                  ))}
                </li>
              ))}
            </ol>
            {item.draft.missing_information.length > 0 && (
              <p className="annotate-missing">Asks for: {item.draft.missing_information.join("; ")}</p>
            )}
          </Card>
        </div>

        <Card title="Cited evidence" className="annotate-evidence">
          {item.evidence.length === 0 && <p className="placeholder-note">No evidence was given to the model.</p>}
          {item.evidence.map((e) => (
            <div key={e.n} className="annotate-passage">
              <div className="annotate-passage-title">
                [{e.n}] {e.title}
              </div>
              <p>{e.text}</p>
            </div>
          ))}
        </Card>
      </div>

      <Card title="Your label">
        <div className="annotate-labels" role="radiogroup" aria-label="Rubric label">
          {LABELS.map((l, i) => (
            <label key={l.value} className={`annotate-label ${label === l.value ? "selected" : ""}`}>
              <input
                type="radio"
                name="label"
                value={l.value}
                checked={label === l.value}
                onChange={() => setLabel(l.value)}
              />
              <span className="annotate-label-key">{i + 1}</span>
              <span>
                <strong>
                  {l.value} · {l.name}
                </strong>
                <small>{l.hint}</small>
              </span>
            </label>
          ))}
        </div>

        {label && label !== "A" && (
          <fieldset className="annotate-reasons">
            <legend>Reasons (pick any)</legend>
            {REASON_CODES.map((code) => (
              <label key={code}>
                <input type="checkbox" checked={reasons.includes(code)} onChange={() => toggleReason(code)} />
                {REASON_TEXT[code]}
              </label>
            ))}
          </fieldset>
        )}

        <textarea
          className="annotate-note"
          placeholder="Optional note"
          value={note}
          maxLength={2000}
          onChange={(e) => setNote(e.target.value)}
        />

        <div className="annotate-actions">
          <Button variant="secondary" disabled={saving} onClick={() => submit("unreadable")}>
            Skip: unreadable
          </Button>
          <Button disabled={!label || saving} onClick={() => submit()}>
            {saving ? "Saving…" : "Save & next →"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
