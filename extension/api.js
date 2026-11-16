// Small client for the TicketSense API, shared by the side panel and the service worker.
// Extension pages with host permissions are not subject to CORS, so no server change is
// needed for the extension's origin.

export const DEFAULT_API = "http://localhost:8000";

export async function getSettings() {
  const { apiBase } = await chrome.storage.local.get("apiBase");
  // The token lives in session storage: it is cleared when the browser closes.
  const { token } = await chrome.storage.session.get("token");
  return { apiBase: (apiBase || DEFAULT_API).replace(/\/+$/, ""), token: token || null };
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function detail(resp) {
  try {
    const body = await resp.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d) => d.msg).join("; ");
  } catch {
    /* not JSON */
  }
  return resp.statusText || `HTTP ${resp.status}`;
}

export async function api(path, { method = "GET", json, form, formData } = {}) {
  const { apiBase, token } = await getSettings();
  const headers = {};
  let body;
  if (token) headers.Authorization = `Bearer ${token}`;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form) {
    body = new URLSearchParams(form);
  } else if (formData) {
    body = formData;
  }
  let resp;
  try {
    resp = await fetch(`${apiBase}${path}`, { method, headers, body });
  } catch {
    throw new ApiError(0, `Cannot reach the TicketSense API at ${apiBase}. Is it running?`);
  }
  if (!resp.ok) throw new ApiError(resp.status, await detail(resp));
  return resp.status === 204 ? null : resp.json();
}
