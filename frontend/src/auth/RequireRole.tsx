import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

const ROLE_HOME: Record<string, string> = {
  end_user: "/end-user",
  department_engineer: "/engineer",
  admin: "/admin",
};

export default function RequireRole({ role }: { role: string }) {
  const { user } = useAuth();

  // RequireAuth (parent route) already guarantees user is set here.
  if (user && user.role !== role) {
    return <Navigate to={ROLE_HOME[user.role] ?? "/login"} replace />;
  }

  return <Outlet />;
}
