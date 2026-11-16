import { useEffect, useState } from "react";
import { Button, Card, FormField, useToast } from "../../components";
import {
  deletePortal,
  listDepartments,
  listPortals,
  savePortal,
  ApiError,
  PORTAL_FIELDS,
  type ComplaintPortal,
  type Department,
} from "../../api/client";
import { useAuth } from "../../auth/AuthContext";

// Complaint portals for the TicketSense browser extension. When the knowledge base
// cannot answer a ticket, the extension opens the portal registered for the ticket's
// department (or the default portal), fills the form using the field map, and the user
// reviews it and clicks Submit. `python -m app.scripts.seed_portals` registers local demo
// portals; point a department at a real site here.

interface Row {
  key: string;
  departmentId: string | null;
  label: string;
}

interface Draft {
  name: string;
  url: string;
  fieldMap: string;
  referenceSelector: string;
  active: boolean;
}

function toDraft(portal: ComplaintPortal | undefined, label: string): Draft {
  return {
    name: portal?.name ?? `${label} complaints`,
    url: portal?.url ?? "",
    fieldMap: JSON.stringify(portal?.field_map ?? {}, null, 2),
    referenceSelector: portal?.reference_selector ?? "",
    active: portal?.active ?? true,
  };
}

export default function AdminPortals() {
  const { token } = useAuth();
  const { notify } = useToast();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [portals, setPortals] = useState<ComplaintPortal[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);

  const rows: Row[] = [
    ...departments.map((d) => ({ key: d.id, departmentId: d.id, label: d.name })),
    { key: "default", departmentId: null, label: "Default (unrouted tickets)" },
  ];
  const portalFor = (departmentId: string | null) => portals.find((p) => p.department_id === departmentId);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    Promise.all([listDepartments(token), listPortals(token)])
      .then(([d, p]) => {
        setDepartments(d);
        setPortals(p);
        const next: Record<string, Draft> = {};
        for (const dept of d) next[dept.id] = toDraft(p.find((x) => x.department_id === dept.id), dept.name);
        next.default = toDraft(p.find((x) => x.department_id === null), "General");
        setDrafts(next);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load complaint portals"))
      .finally(() => setLoading(false));
  }, [token]);

  const update = (key: string, patch: Partial<Draft>) =>
    setDrafts((prev) => ({ ...prev, [key]: { ...prev[key], ...patch } }));

  async function save(row: Row) {
    if (!token) return;
    const draft = drafts[row.key];
    let fieldMap: Record<string, string>;
    try {
      fieldMap = JSON.parse(draft.fieldMap || "{}");
      if (typeof fieldMap !== "object" || Array.isArray(fieldMap) || fieldMap === null) throw new Error();
    } catch {
      notify(`${row.label}: the field map must be a JSON object, for example {"subject": "#subject"}.`, "error");
      return;
    }
    setSaving(row.key);
    try {
      const saved = await savePortal(token, {
        department_id: row.departmentId,
        name: draft.name.trim(),
        url: draft.url.trim(),
        field_map: fieldMap,
        reference_selector: draft.referenceSelector.trim() || null,
        active: draft.active,
      });
      setPortals((prev) => [...prev.filter((p) => p.id !== saved.id), saved]);
      notify(`${row.label}: portal saved.`, "success");
    } catch (err) {
      notify(err instanceof ApiError ? `${row.label}: ${err.message}` : "Could not save the portal", "error");
    } finally {
      setSaving(null);
    }
  }

  async function remove(row: Row) {
    const portal = portalFor(row.departmentId);
    if (!token || !portal) return;
    setSaving(row.key);
    try {
      await deletePortal(token, portal.id);
      setPortals((prev) => prev.filter((p) => p.id !== portal.id));
      update(row.key, toDraft(undefined, row.label));
      notify(`${row.label}: portal removed.`, "info");
    } catch (err) {
      notify(err instanceof ApiError ? err.message : "Could not remove the portal", "error");
    } finally {
      setSaving(null);
    }
  }

  return (
    <Card title="Complaint portals">
      <p className="placeholder-note">
        Used by the TicketSense browser extension. When the knowledge base cannot answer a ticket, the extension opens
        the department's portal and fills the form; the user reviews it and clicks Submit. The field map links ticket
        fields ({PORTAL_FIELDS.join(", ")}) to CSS selectors on the portal's form. The reference selector finds the
        complaint number shown after submitting.
      </p>
      {loading && <p className="placeholder-note">Loading...</p>}
      {error && <p className="form-error">{error}</p>}
      {!loading && !error && (
        <div className="dept-panel-list">
          {rows.map((row) => {
            const draft = drafts[row.key];
            const existing = portalFor(row.departmentId);
            if (!draft) return null;
            return (
              <div className="dept-panel" key={row.key}>
                <div className="dept-panel-header">
                  <div>
                    <strong>{row.label}</strong>
                    <span className="dept-panel-meta">
                      {existing ? (existing.active ? "active" : "inactive") : "no portal registered"}
                    </span>
                  </div>
                </div>
                <FormField label="Portal name" htmlFor={`name-${row.key}`}>
                  <input id={`name-${row.key}`} value={draft.name}
                    onChange={(e) => update(row.key, { name: e.target.value })} />
                </FormField>
                <FormField label="Form URL" htmlFor={`url-${row.key}`} hint="The page with the complaint form.">
                  <input id={`url-${row.key}`} type="url" placeholder="https://..." value={draft.url}
                    onChange={(e) => update(row.key, { url: e.target.value })} />
                </FormField>
                <details>
                  <summary>Form mapping</summary>
                  <FormField label="Field map (JSON)" htmlFor={`map-${row.key}`}>
                    <textarea id={`map-${row.key}`} rows={6} value={draft.fieldMap} spellCheck={false}
                      onChange={(e) => update(row.key, { fieldMap: e.target.value })} />
                  </FormField>
                  <FormField label="Reference selector" htmlFor={`ref-${row.key}`}
                    hint="CSS selector of the complaint number on the confirmation page (optional).">
                    <input id={`ref-${row.key}`} value={draft.referenceSelector}
                      onChange={(e) => update(row.key, { referenceSelector: e.target.value })} />
                  </FormField>
                </details>
                <label className="portal-active">
                  <input type="checkbox" checked={draft.active}
                    onChange={(e) => update(row.key, { active: e.target.checked })} /> Active
                </label>
                <div className="portal-actions">
                  <Button onClick={() => save(row)} disabled={saving === row.key || !draft.url.trim()}>
                    {saving === row.key ? "Saving..." : "Save"}
                  </Button>
                  {existing && (
                    <Button variant="secondary" onClick={() => remove(row)} disabled={saving === row.key}>
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
