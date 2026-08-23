import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, FormField } from "../components";
import { createTicket, listTickets, ApiError, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function EndUserHome() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

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
      await loadTickets();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : "Could not submit ticket");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Card title="New ticket">
        <form onSubmit={handleSubmit}>
          <FormField label="Subject" htmlFor="subject">
            <input
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Description" htmlFor="description">
            <textarea
              id="description"
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </FormField>

          <FormField label="Attachment" htmlFor="attachment" hint="Image, PDF, or log file — optional">
            <input
              id="attachment"
              type="file"
              accept="image/*,.pdf,.log,.txt"
              onChange={(e) => setAttachment(e.target.files?.[0] ?? null)}
            />
          </FormField>

          <p className="placeholder-note">
            Department, priority, and sentiment are classified automatically after
            submission — check "My tickets" below in a few seconds.
          </p>

          {submitError && <p className="form-error">{submitError}</p>}

          <Button type="submit" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit ticket"}
          </Button>
        </form>
      </Card>

      <div style={{ height: "var(--space-lg)" }} />

      <Card title="My tickets">
        {ticketsLoading && <p className="placeholder-note">Loading...</p>}
        {ticketsError && <p className="form-error">{ticketsError}</p>}
        {!ticketsLoading && !ticketsError && tickets.length === 0 && (
          <p className="placeholder-note">No tickets submitted yet.</p>
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
                  <td>{ticket.subject}</td>
                  <td>
                    <span className="status-badge">{ticket.status}</span>
                  </td>
                  <td>{new Date(ticket.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
