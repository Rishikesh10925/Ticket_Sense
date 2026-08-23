import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import RequireAuth from "./auth/RequireAuth";
import RequireRole from "./auth/RequireRole";
import Shell from "./layouts/Shell";
import Login from "./pages/Login";
import EndUserHome from "./pages/EndUserHome";
import EngineerQueue from "./pages/EngineerQueue";
import AdminHome from "./pages/AdminHome";
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
                <Route path="admin" element={<AdminHome />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
