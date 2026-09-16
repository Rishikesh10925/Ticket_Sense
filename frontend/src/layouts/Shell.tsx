import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LogoMark, LogoutIcon, QueueIcon, ShieldIcon, TicketIcon } from "../components/icons";
import { listDepartments, listTickets, type Department } from "../api/client";
import "./Shell.css";

const ROLE_HOME: Record<string, { to: string; label: string; icon: typeof TicketIcon }> = {
  end_user: { to: "/end-user", label: "My Tickets", icon: TicketIcon },
  department_engineer: { to: "/engineer", label: "Queue", icon: QueueIcon },
  admin: { to: "/admin", label: "Admin", icon: ShieldIcon },
};

const ROLE_DISPLAY: Record<string, string> = {
  end_user: "End User",
  department_engineer: "Department Engineer",
  admin: "Admin",
};

// Short badge letters for the role chip — distinct from the user's own
// initials, which already live in the avatar circle right next to it.
const ROLE_TAG: Record<string, string> = {
  end_user: "USER",
  department_engineer: "ENG",
  admin: "ADMIN",
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || "?";
}

// A compact live read of the engineer's own queue, refreshed periodically —
// gives the sidebar an actual reason to exist for the highest-frequency role
// instead of sitting mostly empty beneath the single nav item. Reuses the
// same listTickets() the Queue page itself calls; no new endpoint.
function useQueuePulse(token: string | null, active: boolean) {
  const [counts, setCounts] = useState<{ escalated: number; drafted: number } | null>(null);

  useEffect(() => {
    if (!token || !active) return;
    let cancelled = false;

    async function refresh() {
      if (!token) return;
      try {
        const tickets = await listTickets(token);
        if (cancelled) return;
        setCounts({
          escalated: tickets.filter((t) => t.status === "escalated").length,
          drafted: tickets.filter((t) => t.status === "drafted").length,
        });
      } catch {
        // Sidebar chrome is not the place to surface a fetch error — the
        // Queue page's own table already reports load failures.
      }
    }

    refresh();
    const interval = setInterval(refresh, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token, active]);

  return counts;
}

export default function Shell() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const nav = user ? ROLE_HOME[user.role] : null;
  const NavIcon = nav?.icon;

  const isEngineer = user?.role === "department_engineer";
  const pulse = useQueuePulse(token, isEngineer);

  const [departments, setDepartments] = useState<Department[]>([]);
  useEffect(() => {
    if (!token || !user?.department_id) return;
    let cancelled = false;
    listDepartments(token)
      .then((d) => !cancelled && setDepartments(d))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [token, user?.department_id]);

  const departmentName = user?.department_id
    ? departments.find((d) => d.id === user.department_id)?.name
    : null;

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <div className="shell-brand">
          <LogoMark />
          <span>TicketSense</span>
        </div>

        {nav && NavIcon && (
          <div className="shell-nav-group">
            <span className="shell-nav-label eyebrow">Workspace</span>
            <nav className="shell-nav">
              <NavLink to={nav.to} className={({ isActive }) => (isActive ? "active" : "")}>
                <NavIcon />
                {nav.label}
              </NavLink>
            </nav>
          </div>
        )}

        {isEngineer && (
          <div className="shell-pulse">
            <span className="shell-nav-label eyebrow">Your queue, live</span>
            <div className="shell-pulse-row">
              <span className="shell-pulse-label">Escalated</span>
              <span className={`shell-pulse-value${pulse && pulse.escalated > 0 ? " shell-pulse-danger" : ""}`}>
                {pulse ? pulse.escalated : "—"}
              </span>
            </div>
            <div className="shell-pulse-row">
              <span className="shell-pulse-label">Draft in review</span>
              <span className="shell-pulse-value shell-pulse-info">{pulse ? pulse.drafted : "—"}</span>
            </div>
          </div>
        )}

        <div className="shell-spacer" />

        {user && (
          <div className="shell-footer">
            <div className="shell-user">
              <div className="shell-user-avatar">{initials(user.full_name)}</div>
              <div className="shell-user-meta">
                <span className="shell-user-name">{user.full_name}</span>
                <span className="shell-user-role">
                  <span className="shell-role-tag">{ROLE_TAG[user.role]}</span>
                  {departmentName ?? ROLE_DISPLAY[user.role]}
                </span>
              </div>
              <button type="button" className="shell-logout" onClick={handleLogout} aria-label="Log out">
                <LogoutIcon width={16} height={16} />
              </button>
            </div>
          </div>
        )}
      </aside>
      <main className="shell-content">
        <Outlet />
      </main>
    </div>
  );
}
