import { useEffect, useRef, useState } from "react";
import { ArrowLeftIcon, ChatIcon, SendIcon } from "./icons";
import { listChatContacts, getChatThread, sendChatMessage, type ChatContact, type ChatMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import "./ChatWidget.css";

const CONTACTS_POLL_MS = 15000;
const THREAD_POLL_MS = 4000;

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || "?";
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

// Direct messaging between admin and department_engineer accounts only (see
// backend/app/routers/messages.py) — end_user customers never render this. A single
// floating widget rather than a dedicated page, since the whole point is being
// reachable from wherever you're already working (a ticket, the queue, analytics).
export default function ChatWidget() {
  const { token, user } = useAuth();
  const [open, setOpen] = useState(false);
  const [contacts, setContacts] = useState<ChatContact[]>([]);
  const [active, setActive] = useState<ChatContact | null>(null);
  const [thread, setThread] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);

  const isEligible = user?.role === "admin" || user?.role === "department_engineer";
  const unreadTotal = contacts.reduce((sum, c) => sum + c.unread_count, 0);

  useEffect(() => {
    if (!token || !isEligible) return;
    let cancelled = false;
    async function refresh() {
      try {
        const data = await listChatContacts(token as string);
        if (!cancelled) setContacts(data);
      } catch {
        // Ambient badge — not worth a visible error state.
      }
    }
    refresh();
    const interval = setInterval(refresh, CONTACTS_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token, isEligible]);

  useEffect(() => {
    if (!token || !active || !open) return;
    let cancelled = false;
    async function refresh() {
      try {
        const data = await getChatThread(token as string, active!.user_id);
        if (!cancelled) setThread(data);
      } catch {
        // Silent — the composer below still works even if a poll tick fails.
      }
    }
    const interval = setInterval(refresh, THREAD_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token, active, open]);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [thread]);

  async function openThread(contact: ChatContact) {
    if (!token) return;
    setActive(contact);
    setThread([]);
    setLoadingThread(true);
    try {
      const data = await getChatThread(token, contact.user_id);
      setThread(data);
      setContacts((prev) => prev.map((c) => (c.user_id === contact.user_id ? { ...c, unread_count: 0 } : c)));
    } catch {
      // The thread pane's own empty state covers a failed load well enough.
    } finally {
      setLoadingThread(false);
    }
  }

  async function handleSend() {
    if (!token || !active || !draft.trim()) return;
    setSending(true);
    try {
      const sent = await sendChatMessage(token, active.user_id, draft.trim());
      setThread((prev) => [...prev, sent]);
      setDraft("");
    } catch {
      // Draft text stays in the box so nothing typed is lost on a failed send.
    } finally {
      setSending(false);
    }
  }

  if (!isEligible || !token || !user) return null;

  return (
    <div className="chat-widget-root" ref={rootRef}>
      <button
        type="button"
        className="chat-widget-trigger"
        aria-label={`Messages${unreadTotal > 0 ? `, ${unreadTotal} unread` : ""}`}
        onClick={() => setOpen((v) => !v)}
      >
        <ChatIcon width={18} height={18} />
        {unreadTotal > 0 && <span className="chat-widget-badge tabular-nums">{unreadTotal}</span>}
      </button>

      {open && (
        <div className="chat-widget-panel">
          {!active ? (
            <>
              <div className="chat-widget-header">
                <strong>Messages</strong>
              </div>
              {contacts.length === 0 ? (
                <p className="chat-widget-empty">
                  No {user.role === "admin" ? "engineers" : "admins"} to message yet.
                </p>
              ) : (
                <ul className="chat-widget-contacts">
                  {contacts.map((c) => (
                    <li key={c.user_id} className="chat-widget-contact" onClick={() => openThread(c)}>
                      <div className="chat-widget-avatar">{initials(c.full_name)}</div>
                      <div className="chat-widget-contact-meta">
                        <span className="chat-widget-contact-name">
                          {c.full_name}
                          {!c.is_active && <span className="chat-widget-inactive-tag">inactive</span>}
                        </span>
                        <span className="chat-widget-contact-preview">
                          {c.department_name && <span className="chat-widget-dept">{c.department_name} · </span>}
                          {c.last_message ?? "No messages yet"}
                        </span>
                      </div>
                      {c.unread_count > 0 && <span className="chat-widget-unread-dot tabular-nums">{c.unread_count}</span>}
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <>
              <div className="chat-widget-header chat-widget-thread-header">
                <button type="button" className="chat-widget-back" onClick={() => setActive(null)} aria-label="Back to contacts">
                  <ArrowLeftIcon />
                </button>
                <div className="chat-widget-thread-title">
                  <strong>{active.full_name}</strong>
                  {active.department_name && <span>{active.department_name}</span>}
                </div>
              </div>

              <div className="chat-widget-thread">
                {loadingThread && <p className="chat-widget-empty">Loading…</p>}
                {!loadingThread && thread.length === 0 && (
                  <p className="chat-widget-empty">Say hello — nothing here yet.</p>
                )}
                {thread.map((m) => (
                  <div key={m.id} className={`chat-bubble-row${m.sender_id === user.id ? " chat-bubble-row-mine" : ""}`}>
                    <div className="chat-bubble">
                      {m.body}
                      <span className="chat-bubble-time">{timeLabel(m.created_at)}</span>
                    </div>
                  </div>
                ))}
                <div ref={threadEndRef} />
              </div>

              <form
                className="chat-widget-composer"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
              >
                <input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Message…"
                  aria-label="Message"
                  autoFocus
                />
                <button type="submit" disabled={sending || !draft.trim()} aria-label="Send">
                  <SendIcon />
                </button>
              </form>
            </>
          )}
        </div>
      )}
    </div>
  );
}
