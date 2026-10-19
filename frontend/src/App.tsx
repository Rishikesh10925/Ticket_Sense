import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import RequireRole from "./auth/RequireRole";
import Shell from "./layouts/Shell";
import { ToastProvider } from "./components";
import Login from "./pages/Login";
import EndUserHome from "./pages/EndUserHome";
import EngineerQueue from "./pages/EngineerQueue";
import AdminLayout from "./pages/admin/AdminLayout";
import AdminTickets from "./pages/admin/AdminTickets";
import AdminApprovals from "./pages/admin/AdminApprovals";
import AdminCustomers from "./pages/admin/AdminCustomers";
import AdminEngineers from "./pages/admin/AdminEngineers";
import AdminDepartments from "./pages/admin/AdminDepartments";
import AdminKnowledgeBase from "./pages/admin/AdminKnowledgeBase";
import AdminAnalytics from "./pages/admin/AdminAnalytics";
import AdminModelHealth from "./pages/admin/AdminModelHealth";
import TicketDetail from "./pages/TicketDetail";
import "./pages/pages.css";

const ROLE_HOME: Record<string, string> = {
  end_user: "/end-user",
  department_engineer: "/engineer",
  admin: "/admin",
};

function RoleHomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user ? ROLE_HOME[user.role] : "/login"} replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="login" element={<Login />} />

            <Route element={<RequireAuth />}>
              <Route element={<Shell />}>
                <Route index element={<RoleHomeRedirect />} />
                <Route element={<RequireRole role="end_user" />}>
                  <Route path="end-user" element={<EndUserHome />} />
                </Route>
                <Route element={<RequireRole role="department_engineer" />}>
                  <Route path="engineer" element={<EngineerQueue />} />
                </Route>
                <Route element={<RequireRole role="admin" />}>
                  <Route path="admin" element={<AdminLayout />}>
                    <Route index element={<Navigate to="tickets" replace />} />
                    <Route path="tickets" element={<AdminTickets />} />
                    <Route path="approvals" element={<AdminApprovals />} />
                    <Route path="customers" element={<AdminCustomers />} />
                    <Route path="engineers" element={<AdminEngineers />} />
                    <Route path="departments" element={<AdminDepartments />} />
                    <Route path="knowledge-base" element={<AdminKnowledgeBase />} />
                    <Route path="analytics" element={<AdminAnalytics />} />
                    <Route path="model-health" element={<AdminModelHealth />} />
                  </Route>
                </Route>
                {/* Backend enforces per-ticket access (see app/routers/tickets.py), so
                    this route isn't role-restricted — any authenticated role that owns
                    or is scoped to the ticket can reach it. */}
                <Route path="tickets/:id" element={<TicketDetail />} />
              </Route>
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
