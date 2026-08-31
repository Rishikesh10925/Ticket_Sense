import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LogoMark, LogoutIcon, QueueIcon, ShieldIcon, TicketIcon } from "../components/icons";
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

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || "?";
}

export default function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const nav = user ? ROLE_HOME[user.role] : null;
  const NavIcon = nav?.icon;

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
          <nav className="shell-nav">
            <NavLink to={nav.to} className={({ isActive }) => (isActive ? "active" : "")}>
              <NavIcon />
              {nav.label}
            </NavLink>
          </nav>
        )}

        {user && (
          <div className="shell-user">
            <div className="shell-user-avatar">{initials(user.full_name)}</div>
            <div className="shell-user-meta">
              <span className="shell-user-name">{user.full_name}</span>
              <span className="shell-user-role">{ROLE_DISPLAY[user.role]}</span>
            </div>
            <button type="button" className="shell-logout" onClick={handleLogout} aria-label="Log out">
              <LogoutIcon width={16} height={16} />
            </button>
          </div>
        )}
      </aside>
      <main className="shell-content">
        <Outlet />
      </main>
    </div>
  );
}
