import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, FormField, useToast } from "../../components";
import { CheckIcon, XIcon } from "../../components/icons";
import {
  listPendingEscalations,
  listUsers,
  approveEscalation,
  rejectEscalation,
  ApiError,
  type PendingEscalation,
  type User,
} from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

export default function AdminApprovals() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const { notify } = useToast();

  const [pending, setPending] = useState<PendingEscalation[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [approvePickerId, setApprovePickerId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectNote, setRejectNote] = useState("");
  const [actingOnId, setActingOnId] = useState<string | null>(null);

  async function loadAll() {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [p, u] = await Promise.all([listPendingEscalations(token), listUsers(token)]);
      setPending(p);
      setUsers(u);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load approvals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleApprove(escalation: PendingEscalation, engineerId: string) {
    if (!token || !engineerId) return;
    const engineer = users.find((u) => u.id === engineerId);
    setActingOnId(escalation.id);
    try {
      await approveEscalation(token, escalation.id, engineerId);
      setPending((prev) => prev.filter((p) => p.id !== escalation.id));
      setApprovePickerId(null);
      notify(`Assigned "${escalation.ticket_subject}" to ${engineer?.full_name ?? "the engineer"}.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not approve this escalation", "error");
    } finally {
      setActingOnId(null);
    }
  }

  async function handleReject(escalation: PendingEscalation) {
    if (!token || !rejectNote.trim()) return;
    setActingOnId(escalation.id);
    try {
      await rejectEscalation(token, escalation.id, rejectNote);
      setPending((prev) => prev.filter((p) => p.id !== escalation.id));
      setRejectingId(null);
      setRejectNote("");
      notify(`Closed "${escalation.ticket_subject}" without routing to an engineer.`, "info");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not reject this escalation", "error");
    } finally {
      setActingOnId(null);
    }
  }

  return (
    <Card title="Approvals" actions={<span className="placeholder-note">Escalated tickets waiting on a decision</span>}>
      {loading && <p className="placeholder-note">Loading...</p>}
      {error && <p className="form-error">{error}</p>}
      {!loading && !error && pending.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <p className="empty-state-title">Nothing waiting</p>
          <p className="empty-state-desc">Every escalation has been approved or rejected.</p>
        </div>
      )}
      {!loading && !error && pending.length > 0 && (
        <ul className="approval-list">
          {pending.map((esc) => {
            const deptEngineers = users.filter(
              (u) => u.role === "department_engineer" && u.is_active && u.department_id === esc.department_id
            );
            return (
              <li key={esc.id} className="approval-item">
                <div className="approval-item-header">
                  <strong className="link-button" onClick={() => navigate(`/tickets/${esc.ticket_id}`)}>
                    {esc.ticket_subject}
                  </strong>
                  <span className="status-badge">{esc.department_name ?? "Unrouted"}</span>
                  {esc.priority && <span className={`priority-badge priority-${esc.priority}`}>{esc.priority}</span>}
                </div>
                <p className="placeholder-note">{esc.reason}</p>
                {esc.confidence_score !== null && (
                  <p className="placeholder-note">Confidence at the time: {Math.round(esc.confidence_score * 100)}%</p>
                )}

                {approvePickerId === esc.id ? (
                  <div className="review-actions-buttons">
                    <select
                      aria-label="Assign to engineer"
                      defaultValue=""
                      onChange={(e) => e.target.value && handleApprove(esc, e.target.value)}
                    >
                      <option value="" disabled>
                        Choose an engineer…
                      </option>
                      {deptEngineers.map((eng) => (
                        <option key={eng.id} value={eng.id}>
                          {eng.full_name}
                        </option>
                      ))}
                    </select>
                    <Button variant="secondary" onClick={() => setApprovePickerId(null)}>
                      Cancel
                    </Button>
                    {deptEngineers.length === 0 && (
                      <span className="form-error">No active engineers in this department yet.</span>
                    )}
                  </div>
                ) : rejectingId === esc.id ? (
                  <div className="review-actions">
                    <FormField label="Why reject this?" htmlFor={`reject-note-${esc.id}`}>
                      <textarea
                        id={`reject-note-${esc.id}`}
                        rows={2}
                        value={rejectNote}
                        onChange={(e) => setRejectNote(e.target.value)}
                      />
                    </FormField>
                    <div className="review-actions-buttons">
                      <Button
                        variant="danger"
                        disabled={actingOnId === esc.id || !rejectNote.trim()}
                        onClick={() => handleReject(esc)}
                      >
                        <XIcon />
                        Confirm reject
                      </Button>
                      <Button variant="secondary" onClick={() => setRejectingId(null)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="review-actions-buttons">
                    <Button disabled={actingOnId === esc.id} onClick={() => setApprovePickerId(esc.id)}>
                      <CheckIcon />
                      Approve
                    </Button>
                    <Button
                      variant="danger"
                      disabled={actingOnId === esc.id}
                      onClick={() => {
                        setRejectingId(esc.id);
                        setRejectNote("");
                      }}
                    >
                      <XIcon />
                      Reject
                    </Button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
