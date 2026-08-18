import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Shell from "./layouts/Shell";
import EndUserHome from "./pages/EndUserHome";
import EngineerQueue from "./pages/EngineerQueue";
import AdminHome from "./pages/AdminHome";
import "./pages/pages.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Shell />}>
          <Route index element={<Navigate to="/end-user" replace />} />
          <Route path="end-user" element={<EndUserHome />} />
          <Route path="engineer" element={<EngineerQueue />} />
          <Route path="admin" element={<AdminHome />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
