import { useState, type FormEvent } from "react";
import { Button, Card, FormField } from "../components";

// Static UI only — no backend wiring yet (see docs/wireframes.md "End User — submit a
// ticket"). Submitting logs the form values and resets the form; nothing is sent
// anywhere until the tickets API exists.
const MY_TICKETS = [
  { id: "#1042", subject: "ME023 error on PO creation", status: "In review" },
  { id: "#1039", subject: "VPN not connecting from home", status: "Resolved" },
];

export default function EndUserHome() {
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    console.log("new ticket (static, not submitted anywhere yet)", {
      subject,
      description,
      attachment: attachment?.name ?? null,
    });
    setSubject("");
    setDescription("");
    setAttachment(null);
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

          <FormField
            label="Department"
            hint="Suggested automatically once classification is built — not implemented yet"
          >
            <select disabled>
              <option>Suggested after submit</option>
            </select>
          </FormField>

          <Button type="submit">Submit ticket</Button>
        </form>
      </Card>

      <div style={{ height: "var(--space-lg)" }} />

      <Card title="My tickets">
        <table className="ticket-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Subject</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {MY_TICKETS.map((ticket) => (
              <tr key={ticket.id}>
                <td>{ticket.id}</td>
                <td>{ticket.subject}</td>
                <td>{ticket.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}
