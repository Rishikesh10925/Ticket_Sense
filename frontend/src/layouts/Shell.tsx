import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import "./Shell.css";

const ROLE_HOME: Record<string, { to: string; label: string }> = {
  end_user: { to: "/end-user", label: "My Tickets" },
  department_engineer: { to: "/engineer", label: "Queue" },
  admin: { to: "/admin", label: "Admin" },
};

const ROLE_DISPLAY: Record<string, string> = {
  end_user: "End User",
  department_engineer: "Department Engineer",
  admin: "Admin",
};

export default function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const home = user ? ROLE_HOME[user.role] : null;

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="shell">
      <header className="shell-header">
        <div className="shell-brand">TicketSense</div>
        {home && (
          <nav className="shell-role-nav">
            <NavLink to={home.to} className={({ isActive }) => (isActive ? "active" : "")}>
              {home.label}
            </NavLink>
          </nav>
        )}
        {user && (
          <div className="shell-user">
            <span>
              {user.full_name} · {ROLE_DISPLAY[user.role]}
            </span>
            <button type="button" className="link-button" onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </header>
      <main className="shell-content">
        <Outlet />
      </main>
    </div>
  );
}
