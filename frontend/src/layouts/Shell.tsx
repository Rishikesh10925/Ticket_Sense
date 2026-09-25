import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LogoMark, LogoutIcon, QueueIcon, ShieldIcon, TicketIcon } from "../components/icons";
import { ChatWidget, NotificationBell, ThemeToggle } from "../components";
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

const ROLE_TAG: Record<string, string> = {
  end_user: "USER",
  department_engineer: "ENG",
  admin: "ADMIN",
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || "?";
}

// A clean top navbar in place of the old dark sidebar — one global nav row every
// role shares, plus (for admin) its own second-level tab row inside AdminLayout. No
// per-role chrome duplicates the live stats now surfaced directly on each page
// (Engineer's "Today" panel, Admin's stat cards), so this bar stays lightweight.
export default function Shell() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  const nav = user ? ROLE_HOME[user.role] : null;
  const NavIcon = nav?.icon;
  const isAdmin = user?.role === "admin";

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="shell-v2">
      <header className="topnav">
        <div className="topnav-inner">
          <div className="topnav-brand">
            <LogoMark width={26} height={26} />
            <span>TicketSense</span>
          </div>

          {nav && NavIcon && (
            <nav className="topnav-links">
              <NavLink to={nav.to} className={({ isActive }) => (isActive ? "active" : "")}>
                <NavIcon width={16} height={16} />
                {nav.label}
              </NavLink>
            </nav>
          )}

          <div className="topnav-right">
            <ThemeToggle />
            <ChatWidget />
            {isAdmin && token && <NotificationBell token={token} />}
            {user && (
              <div className="topnav-user">
                <div className="topnav-user-avatar">{initials(user.full_name)}</div>
                <div className="topnav-user-meta">
                  <span className="topnav-user-name">{user.full_name}</span>
                  <span className="topnav-user-role">
                    <span className="topnav-role-tag">{ROLE_TAG[user.role]}</span>
                    {ROLE_DISPLAY[user.role]}
                  </span>
                </div>
                <button type="button" className="topnav-logout" onClick={handleLogout} aria-label="Log out">
                  <LogoutIcon width={16} height={16} />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="shell-content">
        <Outlet />
      </main>
    </div>
  );
}
