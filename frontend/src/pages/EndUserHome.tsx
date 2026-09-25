import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { AttachmentInput, Button, Card, FormField, StatCard, useToast } from "../components";
import { CloseIcon, PlusIcon } from "../components/icons";
import { createTicket, listTickets, ApiError, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { statusLabel, statusBadgeClass } from "../statusLabels";

const OPEN_STATUSES = ["submitted", "classified", "routed", "drafted"];

export default function EndUserHome() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [drawerOpen, setDrawerOpen] = useState(false);
  const subjectRef = useRef<HTMLInputElement>(null);

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { notify } = useToast();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ticketsLoading, setTicketsLoading] = useState(true);
  const [ticketsError, setTicketsError] = useState<string | null>(null);

  async function loadTickets() {
    if (!token) return;
    setTicketsLoading(true);
    setTicketsError(null);
    try {
      const data = await listTickets(token);
      setTickets(data);
    } catch (err) {
      setTicketsError(err instanceof ApiError ? err.message : "Could not load tickets");
    } finally {
      setTicketsLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function openDrawer() {
    setDrawerOpen(true);
    // Focus the first field once the panel has actually mounted/animated in.
    setTimeout(() => subjectRef.current?.focus(), 50);
  }

  function closeDrawer() {
    setDrawerOpen(false);
    setSubmitError(null);
  }

  useEffect(() => {
    if (!drawerOpen) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") closeDrawer();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [drawerOpen]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await createTicket(token, subject, description, attachment);
      setSubject("");
      setDescription("");
      setAttachment(null);
      setAttachmentError(null);
      setDrawerOpen(false);
      notify("Ticket submitted — it'll appear in the list below in a moment.", "success");
      await loadTickets();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Could not submit ticket");
    } finally {
      setSubmitting(false);
    }
  }

  const openCount = tickets.filter((t) => OPEN_STATUSES.includes(t.status)).length;
  const draftCount = tickets.filter((t) => t.status === "drafted").length;
  const closedCount = tickets.filter((t) => t.status === "closed" || t.status === "reviewed").length;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>My tickets</h1>
          <p>Track every issue you've submitted through to resolution.</p>
        </div>
        <Button onClick={openDrawer}>
          <PlusIcon width={16} height={16} />
          New ticket
        </Button>
      </div>

      {!ticketsLoading && !ticketsError && tickets.length > 0 && (
        <div className="stat-grid">
          <StatCard label="Open" value={openCount} accent />
          <StatCard label="Draft in review" value={draftCount} tone="info" />
          <StatCard label="Resolved" value={closedCount} tone="success" />
          <StatCard label="Total" value={tickets.length} />
        </div>
      )}

      <Card title="Tickets">
        {ticketsLoading && <p className="placeholder-note">Loading...</p>}
        {ticketsError && <p className="form-error">{ticketsError}</p>}
        {!ticketsLoading && !ticketsError && tickets.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">🎫</div>
            <p className="empty-state-title">No tickets yet</p>
            <p className="empty-state-desc">Submit your first ticket and it'll show up here.</p>
            <Button variant="secondary" onClick={openDrawer}>
              <PlusIcon width={16} height={16} />
              Submit your first ticket
            </Button>
          </div>
        )}
        {!ticketsLoading && tickets.length > 0 && (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  className="clickable-row"
                  onClick={() => navigate(`/tickets/${ticket.id}`)}
                >
                  <td className="ticket-table-subject">{ticket.subject}</td>
                  <td>
                    <span className={statusBadgeClass(ticket.status)}>{statusLabel(ticket.status)}</span>
                  </td>
                  <td className="ticket-table-date">{new Date(ticket.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!ticketsLoading && !ticketsError && tickets.length > 0 && (
          <p className="placeholder-note draft-status-legend">
            "Draft in review" — a department engineer has an AI-drafted reply ready and is reviewing it. A human always makes the final call.
          </p>
        )}
      </Card>

      {drawerOpen && (
        <div className="drawer-overlay" onClick={closeDrawer}>
          <div
            className="drawer-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-ticket-heading"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="drawer-header">
              <h2 id="new-ticket-heading">New ticket</h2>
              <button type="button" className="drawer-close" onClick={closeDrawer} aria-label="Close">
                <CloseIcon width={18} height={18} />
              </button>
            </div>
            <div className="drawer-body">
              <form onSubmit={handleSubmit}>
                <FormField label="Subject" htmlFor="subject">
                  <input
                    id="subject"
                    ref={subjectRef}
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    required
                  />
                </FormField>

                <FormField label="Description" htmlFor="description">
                  <textarea
                    id="description"
                    rows={6}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                  />
                </FormField>

                <AttachmentInput
                  file={attachment}
                  onChange={(file, error) => {
                    setAttachment(file);
                    setAttachmentError(error);
                  }}
                />
                {attachmentError && <p className="form-error">{attachmentError}</p>}

                <p className="placeholder-note">
                  Your ticket is classified, routed to the right team, and drafted into a
                  reply automatically — check "My tickets" in a few seconds.
                </p>

                {submitError && <p className="form-error">{submitError}</p>}

                <div className="drawer-actions">
                  <Button type="submit" disabled={submitting || !!attachmentError}>
                    {submitting ? "Submitting…" : "Submit ticket"}
                  </Button>
                  <Button type="button" variant="secondary" onClick={closeDrawer}>
                    Cancel
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
