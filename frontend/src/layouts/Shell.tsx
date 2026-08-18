import { NavLink, Outlet } from "react-router-dom";
import "./Shell.css";

// No auth exists yet (see docs/architecture.md — planned for a later week), so the
// role switcher below is a stand-in for real role-based routing: it lets each of the
// three role screens be reached and demonstrates the shared shell, but it is not a
// permissions boundary.
const ROLES = [
  { to: "/end-user", label: "End User" },
  { to: "/engineer", label: "Department Engineer" },
  { to: "/admin", label: "Admin" },
];

export default function Shell() {
  return (
    <div className="shell">
      <header className="shell-header">
        <div className="shell-brand">TicketSense</div>
        <nav className="shell-role-nav">
          {ROLES.map((role) => (
            <NavLink
              key={role.to}
              to={role.to}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {role.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="shell-content">
        <Outlet />
      </main>
    </div>
  );
}
