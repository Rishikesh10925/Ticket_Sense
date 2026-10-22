import { useCallback, useEffect, useRef, useState } from "react";
import { Button, Card, useToast } from "../components";
import { useAuth } from "../auth/AuthContext";
import {
  ApiError,
  getNextStudyTask,
  searchStudyKb,
  submitStudyTask,
  type StudyAction,
  type StudyArticle,
  type StudyItem,
} from "../api/client";
import "./Annotate.css";
import "./Study.css";

// User-study screen (docs/study/user-study/README.md). The API decides what a task shows:
// in the manual condition only the ticket and the knowledge-base search; in the workbench
// condition also the lane, its reasons and (unless escalated) the AI draft. Handling time
// is measured on the server, so no timer is shown here.
const CONDITION_NAME = { manual: "Without AI", workbench: "With the AI workbench" } as const;
const LANE_HINT: Record<string, string> = {
  fast: "Fast lane: the system is confident in this draft. Read it once and send, or edit if something is off.",
  assisted: "Assisted lane: check the weakest claims below against the evidence, then send, edit or escalate.",
  escalate: "Escalated: the system withheld its draft. Answer from the knowledge base yourself, or escalate.",
};

function draftText(item: StudyItem): string {
  return (item.draft?.steps ?? []).map((s, i) => `${i + 1}. ${s.text}`).join("\n");
}

export default function Study() {
  const { token } = useAuth();
  const { notify } = useToast();
  const [item, setItem] = useState<StudyItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [finished, setFinished] = useState(false);
  const [onBreak, setOnBreak] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [saving, setSaving] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StudyArticle[] | null>(null);
  const [searching, setSearching] = useState(false);
  const lastSection = useRef<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const next = await getNextStudyTask(token);
      setItem(next);
      setFinished(next === null);
      setReply(next ? draftText(next) : "");
      setQuery("");
      setResults(null);
      if (next && lastSection.current !== null && next.section !== lastSection.current) setOnBreak(true);
      if (next) lastSection.current = next.section;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load the next ticket");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function submit(escalate: boolean) {
    if (!token || !item || saving) return;
    const original = draftText(item);
    const action: StudyAction = escalate
      ? "escalate"
      : item.draft
        ? reply.trim() === original.trim()
          ? "accept"
          : "edit"
        : "write";
    setSaving(true);
    try {
      await submitStudyTask(token, item.task_id, { action, final_reply: escalate ? undefined : reply });
      await load();
    } catch (e) {
      notify(e instanceof ApiError ? e.message : "Could not save", "error");
    } finally {
      setSaving(false);
    }
  }

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !query.trim()) return;
    setSearching(true);
    try {
      setResults(await searchStudyKb(token, query));
    } catch {
      notify("Search failed", "error");
    } finally {
      setSearching(false);
    }
  }

  if (loading) return <p className="placeholder-note">Loading the next ticket…</p>;
  if (error) return <p className="form-error">{error}</p>;
  if (finished || !item) {
    return (
      <Card title="All done">
        <p>You have handled every ticket. Please tell the facilitator; there is a short questionnaire next.</p>
      </Card>
    );
  }
  if (onBreak) {
    return (
      <Card title="Part 1 done">
        <p>
          Take a short break. In part 2 you will work{" "}
          {item.condition === "manual" ? "without AI" : "with the AI workbench"}.
        </p>
        <Button onClick={() => setOnBreak(false)}>Start part 2</Button>
      </Card>
    );
  }

  const { done, total } = item.progress;
  const hasDraft = item.condition === "workbench" && item.draft !== null;

  return (
    <div className="annotate study">
      <div className="annotate-bar">
        <div>
          <strong>
            {done + 1} / {total}
          </strong>{" "}
          tickets · part {item.section} of 2 · <span className="study-condition">{CONDITION_NAME[item.condition]}</span>
        </div>
        <div className="annotate-progress" role="progressbar" aria-valuenow={done} aria-valuemax={total}>
          <span style={{ width: `${total ? (100 * done) / total : 0}%` }} />
        </div>
      </div>

      <div className="annotate-grid">
        <div className="annotate-main">
          <Card title="Ticket">
            <p className="annotate-subject">{item.ticket.subject}</p>
            <p className="annotate-body">{item.ticket.body}</p>
            {item.ticket.attachment_text && <pre className="annotate-log">{item.ticket.attachment_text}</pre>}
          </Card>

          {item.condition === "workbench" && item.lane && (
            <p className={`lane-hint lane-hint-${item.lane}`}>
              {LANE_HINT[item.lane]}
              {item.reasons.length > 0 && <span className="study-reasons"> Why: {item.reasons.join("; ")}.</span>}
            </p>
          )}

          {hasDraft && item.weakest_claims.length > 0 && (
            <Card title={item.lane === "assisted" ? "Weakest claims: verify these first" : "Check these claims"}>
              <ul className="study-claims">
                {item.weakest_claims.map((c, i) => (
                  <li key={i}>
                    Step {c.step}: {c.text} <small>(support {c.support})</small>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card title={hasDraft ? "Your reply (the AI draft, edit as needed)" : "Your reply"}>
            <label htmlFor="study-reply" className="sr-only">
              Reply to the user
            </label>
            <textarea
              id="study-reply"
              className="study-reply"
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              placeholder="Write the steps you would send to the user"
            />
            <div className="annotate-actions">
              <Button variant="secondary" disabled={saving} onClick={() => submit(true)}>
                Escalate
              </Button>
              <Button disabled={saving || !reply.trim()} onClick={() => submit(false)}>
                {saving ? "Saving…" : "Send reply →"}
              </Button>
            </div>
          </Card>
        </div>

        <div className="annotate-main">
          {hasDraft && (
            <Card title="Evidence the AI used" className="annotate-evidence">
              {item.evidence.map((e) => (
                <div key={e.n} className="annotate-passage">
                  <div className="annotate-passage-title">
                    [{e.n}] {e.title}
                  </div>
                  <p>{e.text}</p>
                </div>
              ))}
            </Card>
          )}

          <Card title="Knowledge base">
            <form className="study-search" onSubmit={search}>
              <label htmlFor="study-q" className="sr-only">
                Search the knowledge base
              </label>
              <input
                id="study-q"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search, e.g. vpn connecting"
              />
              <Button type="submit" variant="secondary" disabled={searching || !query.trim()}>
                {searching ? "…" : "Search"}
              </Button>
            </form>
            {results !== null && results.length === 0 && <p className="placeholder-note">No articles match.</p>}
            {results?.map((a) => (
              <details key={a.article_key ?? a.title} className="study-article">
                <summary>{a.title}</summary>
                <p>{a.content}</p>
              </details>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
