import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { listPendingEscalations } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import "./admin.css";

const TABS = [
  { to: "/admin/tickets", label: "All Tickets" },
  { to: "/admin/approvals", label: "Approvals" },
  { to: "/admin/customers", label: "Customers" },
  { to: "/admin/engineers", label: "Engineers" },
  { to: "/admin/departments", label: "Departments" },
  { to: "/admin/knowledge-base", label: "Knowledge Base" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/model-health", label: "Model Health" },
];

// The admin control-center shell: a second-level tab row beneath the global top
// navbar (see Shell.tsx), so admin reads as a multi-section product surface rather
// than one more page that happens to have a table on it. Every section below
// fetches its own data independently — this layout only owns navigation chrome plus
// the one piece of ambient state (pending-approval count) worth surfacing on the tab
// itself; the bell in the global navbar covers the same count everywhere else.
export default function AdminLayout() {
  const { token } = useAuth();
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    listPendingEscalations(token)
      .then((d) => !cancelled && setPendingCount(d.length))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="admin-shell">
      <div className="admin-topbar">
        <div>
          <h1>Control center</h1>
          <p>Every ticket, every engineer, every number — in one place.</p>
        </div>
      </div>

      <nav className="admin-tabs">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) => `admin-tab${isActive ? " admin-tab-active" : ""}`}
          >
            {tab.label}
            {tab.to === "/admin/approvals" && pendingCount > 0 && (
              <span className="admin-tab-badge tabular-nums">{pendingCount}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <Outlet />
    </div>
  );
}
