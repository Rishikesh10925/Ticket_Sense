import { Card } from "../components";

// Layout placeholder only, matching docs/wireframes.md "Department Engineer — review
// workspace". The queue/detail split and ticket review actions are not built yet —
// see README.md Project status.
const QUEUE = [
  { id: "#1042", priority: "High" },
  { id: "#1044", priority: "Med" },
  { id: "#1051", priority: "Low" },
  { id: "#1053", priority: "Med" },
];

export default function EngineerQueue() {
  return (
    <div className="engineer-layout">
      <Card title="Queue">
        <ul className="queue-list">
          {QUEUE.map((ticket) => (
            <li key={ticket.id}>
              <span>{ticket.id}</span>
              <span>{ticket.priority}</span>
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Ticket detail">
        <p className="placeholder-note">
          Select a ticket to review retrieved evidence, the AI draft, and its confidence
          score, and accept/edit/reject/escalate — not built yet.
        </p>
      </Card>
    </div>
  );
}
