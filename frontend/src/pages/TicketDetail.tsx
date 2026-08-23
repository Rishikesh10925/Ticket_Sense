import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card } from "../components";
import { getTicket, listDepartments, ApiError, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function TicketDetail() {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [departmentNames, setDepartmentNames] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !id) return;
    setLoading(true);
    Promise.all([getTicket(token, id), listDepartments(token)])
      .then(([ticketData, departments]) => {
        setTicket(ticketData);
        setDepartmentNames(Object.fromEntries(departments.map((d) => [d.id, d.name])));
      })
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.status === 403
              ? "You don't have access to this ticket."
              : err.message
            : "Could not load ticket"
        )
      )
      .finally(() => setLoading(false));
  }, [token, id]);

  if (loading) return <p className="placeholder-note">Loading...</p>;
  if (error) return <p className="form-error">{error}</p>;
  if (!ticket) return null;

  return (
    <Card
      title={ticket.subject}
      actions={
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Back
        </Button>
      }
    >
      <div className="ticket-detail-badges">
        <span className="status-badge">{ticket.status}</span>
        {ticket.priority && (
          <span className={`priority-badge priority-${ticket.priority}`}>{ticket.priority}</span>
        )}
        {ticket.sentiment && <span className="status-badge">{ticket.sentiment}</span>}
      </div>

      <dl className="ticket-detail-fields">
        <dt>Description</dt>
        <dd>{ticket.description}</dd>

        <dt>Department</dt>
        <dd>
          {ticket.department_id ? departmentNames[ticket.department_id] ?? ticket.department_id : "Not yet routed"}
        </dd>

        <dt>Priority</dt>
        <dd>{ticket.priority ?? "Not yet classified"}</dd>

        <dt>Sentiment</dt>
        <dd>{ticket.sentiment ?? "Not yet classified"}</dd>

        {ticket.attachment_path && (
          <>
            <dt>Attachment</dt>
            <dd>
              {ticket.attachment_type} — {ticket.attachment_path.split("/").pop()}
            </dd>
          </>
        )}

        <dt>Submitted</dt>
        <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
      </dl>

      <p className="placeholder-note">
        Retrieved evidence, the AI draft, and confidence score, plus
        accept/edit/reject/escalate actions, are not built yet.
      </p>
    </Card>
  );
}
