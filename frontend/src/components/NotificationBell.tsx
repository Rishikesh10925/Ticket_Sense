import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BellIcon } from "./icons";
import { listPendingEscalations, type PendingEscalation } from "../api/client";
import "./NotificationBell.css";

const POLL_MS = 20000;

// Admin-only live read of the approvals queue — the one thing on this dashboard that
// genuinely needs push-like awareness, since a ticket sitting unapproved is a customer
// waiting. Reuses the same GET /escalations/pending the Approvals page itself calls.
export default function NotificationBell({ token }: { token: string }) {
  const navigate = useNavigate();
  const [pending, setPending] = useState<PendingEscalation[]>([]);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function refresh() {
      try {
        const data = await listPendingEscalations(token);
        if (!cancelled) setPending(data);
      } catch {
        // Silent — this is an ambient indicator, not a page the user is waiting on.
      }
    }
    refresh();
    const interval = setInterval(refresh, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token]);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  return (
    <div className="notif-bell-root" ref={rootRef}>
      <button
        type="button"
        className="notif-bell-trigger"
        aria-label={`Notifications${pending.length > 0 ? `, ${pending.length} pending` : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        <BellIcon width={18} height={18} />
        {pending.length > 0 && <span className="notif-bell-badge tabular-nums">{pending.length}</span>}
      </button>

      {open && (
        <div className="notif-bell-panel">
          <div className="notif-bell-panel-header">
            <strong>Pending approvals</strong>
          </div>
          {pending.length === 0 ? (
            <p className="notif-bell-empty">Nothing waiting on you right now.</p>
          ) : (
            <ul className="notif-bell-list">
              {pending.slice(0, 6).map((esc) => (
                <li
                  key={esc.id}
                  className="notif-bell-item"
                  onClick={() => {
                    setOpen(false);
                    navigate(`/tickets/${esc.ticket_id}`);
                  }}
                >
                  <span className="notif-bell-item-subject">{esc.ticket_subject}</span>
                  <span className="notif-bell-item-meta">
                    {esc.department_name ?? "Unrouted"}
                    {esc.confidence_score !== null && ` · ${Math.round(esc.confidence_score * 100)}% confidence`}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            className="notif-bell-view-all"
            onClick={() => {
              setOpen(false);
              navigate("/admin/approvals");
            }}
          >
            View all approvals
          </button>
        </div>
      )}
    </div>
  );
}
