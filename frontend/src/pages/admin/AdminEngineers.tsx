import { useEffect, useState } from "react";
import { Button, Card, ConfirmDialog, FormField, StatCard, useToast } from "../../components";
import { CheckIcon, PlusIcon } from "../../components/icons";
import {
  listUsers,
  createUser,
  updateUser,
  listDepartments,
  ApiError,
  type User,
  type Department,
} from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

// "Delete" is implemented as the existing soft-delete (is_active toggle) rather than
// a hard DELETE — an engineer who has already reviewed tickets can't be removed
// without breaking that history's foreign keys, and deactivating has the same
// practical effect (they can no longer be assigned new work).
export default function AdminEngineers() {
  const { token } = useAuth();
  const { notify } = useToast();

  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showNewEngineer, setShowNewEngineer] = useState(false);
  const [newEngineer, setNewEngineer] = useState({ fullName: "", email: "", password: "", departmentId: "" });
  const [newEngineerError, setNewEngineerError] = useState<string | null>(null);
  const [creatingEngineer, setCreatingEngineer] = useState(false);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<User | null>(null);

  async function loadAll() {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [u, d] = await Promise.all([listUsers(token), listDepartments(token)]);
      setUsers(u);
      setDepartments(d);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load engineers");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const departmentName = (id: string | null) => departments.find((d) => d.id === id)?.name ?? "—";
  const engineers = users.filter((u) => u.role === "department_engineer");

  async function handleCreateEngineer() {
    if (!token) return;
    if (!newEngineer.fullName.trim() || !newEngineer.email.trim() || !newEngineer.password || !newEngineer.departmentId) {
      setNewEngineerError("Name, email, password, and department are all required.");
      return;
    }
    setCreatingEngineer(true);
    setNewEngineerError(null);
    try {
      const created = await createUser(token, {
        email: newEngineer.email,
        fullName: newEngineer.fullName,
        password: newEngineer.password,
        role: "department_engineer",
        departmentId: newEngineer.departmentId,
      });
      setUsers((prev) => [...prev, created]);
      setNewEngineer({ fullName: "", email: "", password: "", departmentId: "" });
      setShowNewEngineer(false);
      notify(`${created.full_name} added to ${departmentName(created.department_id)}.`, "success");
    } catch (err) {
      setNewEngineerError(err instanceof ApiError ? err.message : "Could not create the engineer account");
    } finally {
      setCreatingEngineer(false);
    }
  }

  async function confirmDeactivate() {
    if (!token || !deactivateTarget) return;
    setSavingUserId(deactivateTarget.id);
    try {
      const updated = await updateUser(token, deactivateTarget.id, { isActive: false });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      notify(`${updated.full_name} deactivated.`, "info");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not deactivate this engineer", "error");
    } finally {
      setSavingUserId(null);
      setDeactivateTarget(null);
    }
  }

  async function handleReactivate(user: User) {
    if (!token) return;
    setSavingUserId(user.id);
    try {
      const updated = await updateUser(token, user.id, { isActive: true });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      notify(`${updated.full_name} reactivated.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not reactivate this engineer", "error");
    } finally {
      setSavingUserId(null);
    }
  }

  async function handleReassignDepartment(user: User, departmentId: string) {
    if (!token || !departmentId || departmentId === user.department_id) return;
    setSavingUserId(user.id);
    try {
      const updated = await updateUser(token, user.id, { departmentId });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      notify(`${updated.full_name} moved to ${departmentName(updated.department_id)}.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not reassign department", "error");
    } finally {
      setSavingUserId(null);
    }
  }

  const activeCount = engineers.filter((e) => e.is_active).length;

  return (
    <>
      {!loading && !error && (
        <div className="stat-grid">
          <StatCard label="Engineers" value={engineers.length} accent />
          <StatCard label="Active" value={activeCount} tone="success" />
          <StatCard label="Deactivated" value={engineers.length - activeCount} />
          <StatCard label="Departments" value={departments.length} tone="info" />
        </div>
      )}

      <Card
        title="Engineers"
        actions={
          <Button variant="secondary" onClick={() => setShowNewEngineer((v) => !v)}>
            <PlusIcon />
            New engineer
          </Button>
        }
      >
        {loading && <p className="placeholder-note">Loading...</p>}
        {error && <p className="form-error">{error}</p>}

        {showNewEngineer && (
          <div className="review-actions" style={{ marginBottom: "var(--space-lg)" }}>
            <FormField label="Full name" htmlFor="new-eng-name">
              <input
                id="new-eng-name"
                value={newEngineer.fullName}
                onChange={(e) => setNewEngineer((prev) => ({ ...prev, fullName: e.target.value }))}
              />
            </FormField>
            <FormField label="Email" htmlFor="new-eng-email">
              <input
                id="new-eng-email"
                type="email"
                value={newEngineer.email}
                onChange={(e) => setNewEngineer((prev) => ({ ...prev, email: e.target.value }))}
              />
            </FormField>
            <FormField label="Temporary password" htmlFor="new-eng-password">
              <input
                id="new-eng-password"
                type="password"
                value={newEngineer.password}
                onChange={(e) => setNewEngineer((prev) => ({ ...prev, password: e.target.value }))}
              />
            </FormField>
            <FormField label="Department" htmlFor="new-eng-dept">
              <select
                id="new-eng-dept"
                value={newEngineer.departmentId}
                onChange={(e) => setNewEngineer((prev) => ({ ...prev, departmentId: e.target.value }))}
              >
                <option value="">Select a department…</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </FormField>
            {newEngineerError && <p className="form-error">{newEngineerError}</p>}
            <div className="review-actions-buttons">
              <Button disabled={creatingEngineer} onClick={handleCreateEngineer}>
                <CheckIcon />
                {creatingEngineer ? "Creating…" : "Create account"}
              </Button>
              <Button variant="secondary" disabled={creatingEngineer} onClick={() => setShowNewEngineer(false)}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {!loading && !error && engineers.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">👤</div>
            <p className="empty-state-title">No engineers yet</p>
            <p className="empty-state-desc">Create the first engineer account to start routing tickets to a team.</p>
          </div>
        )}

        {!loading && !error && engineers.length > 0 && (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Department</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {engineers.map((user) => (
                <tr key={user.id} className={!user.is_active ? "row-inactive" : undefined}>
                  <td className="ticket-table-subject">{user.full_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <select
                      className="select-filter"
                      value={user.department_id ?? ""}
                      disabled={savingUserId === user.id}
                      onChange={(e) => handleReassignDepartment(user, e.target.value)}
                      aria-label={`Department for ${user.full_name}`}
                    >
                      {departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <span className={`status-badge ${user.is_active ? "status-drafted" : ""}`}>
                      {user.is_active ? "Active" : "Deactivated"}
                    </span>
                  </td>
                  <td>
                    <Button
                      variant="secondary"
                      className="btn-sm"
                      disabled={savingUserId === user.id}
                      onClick={() => (user.is_active ? setDeactivateTarget(user) : handleReactivate(user))}
                    >
                      {user.is_active ? "Deactivate" : "Reactivate"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <ConfirmDialog
        open={deactivateTarget !== null}
        title="Deactivate this engineer?"
        message={
          deactivateTarget
            ? `${deactivateTarget.full_name} will no longer be assignable to new tickets or appear as an option when approving escalations. Their past review history is kept.`
            : ""
        }
        confirmLabel="Deactivate"
        danger
        busy={savingUserId === deactivateTarget?.id}
        onConfirm={confirmDeactivate}
        onCancel={() => setDeactivateTarget(null)}
      />
    </>
  );
}
