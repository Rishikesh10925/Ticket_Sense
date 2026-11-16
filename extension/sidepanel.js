import { api, ApiError, DEFAULT_API, getSettings } from "./api.js";

const $ = (id) => document.getElementById(id);
const VIEWS = ["settings", "login", "ask", "ticket"];
const POLL_MS = 3000;
const POLL_LIMIT_MS = 5 * 60 * 1000;

let current = null; // { id, data }
let pollTimer = null;
let pollStarted = 0;
let lastView = "ask";

function show(view) {
  for (const v of VIEWS) $(`view-${v}`).hidden = v !== view;
  if (view !== "settings") lastView = view;
}

function showError(message) {
  const box = $("error");
  box.textContent = message || "";
  box.hidden = !message;
}

function clearPoll() {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = null;
}

async function handle(err) {
  if (err instanceof ApiError && err.status === 401) {
    await chrome.storage.session.remove("token");
    showError("Your session ended. Please sign in again.");
    show("login");
    return;
  }
  showError(err?.message || String(err));
}

// ---- settings ----------------------------------------------------------------------

$("settings-btn").addEventListener("click", async () => {
  const { apiBase } = await getSettings();
  $("api-base").value = apiBase;
  show("settings");
});

$("close-settings").addEventListener("click", () => show(lastView));

$("save-settings").addEventListener("click", async () => {
  let url;
  try {
    url = new URL($("api-base").value.trim() || DEFAULT_API);
    if (!/^https?:$/.test(url.protocol)) throw new Error();
  } catch {
    showError("Enter an address starting with http:// or https://");
    return;
  }
  const origin = `${url.origin}/*`;
  // Must run inside the click: Chrome only asks for permissions during a user gesture.
  const granted = await chrome.permissions.request({ origins: [origin] }).catch(() => false);
  if (!granted && !(await chrome.permissions.contains({ origins: [origin] }))) {
    showError(`TicketSense needs permission to reach ${url.origin}.`);
    return;
  }
  await chrome.storage.local.set({ apiBase: url.origin });
  await chrome.storage.session.remove("token");
  showError("");
  start();
});

// ---- sign in -------------------------------------------------------------------------

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  try {
    const { access_token: token } = await api("/auth/login", {
      method: "POST",
      form: { username: $("email").value.trim(), password: $("password").value },
    });
    await chrome.storage.session.set({ token });
    $("password").value = "";
    await start();
  } catch (err) {
    showError(err instanceof ApiError && err.status === 401 ? "Wrong email or password." : err.message);
  }
});

$("logout").addEventListener("click", async () => {
  clearPoll();
  await chrome.storage.session.remove("token");
  $("who").textContent = "";
  show("login");
});

// ---- ask ---------------------------------------------------------------------------

$("ask-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  const button = event.submitter;
  button.disabled = true;
  try {
    const body = new FormData();
    body.set("subject", $("subject").value.trim());
    body.set("description", $("description").value.trim());
    const ticket = await api("/tickets", { method: "POST", formData: body });
    $("subject").value = "";
    $("description").value = "";
    $("source-note").hidden = true;
    await openTicket(ticket.id, ticket.subject);
  } catch (err) {
    await handle(err);
  } finally {
    button.disabled = false;
  }
});

async function loadPending() {
  const { pendingText, pendingSource } = await chrome.storage.session.get(["pendingText", "pendingSource"]);
  if (!pendingText) return;
  await chrome.storage.session.remove(["pendingText", "pendingSource"]);
  $("description").value = pendingText;
  if (!$("subject").value) $("subject").value = pendingText.split(/\s+/).slice(0, 8).join(" ").slice(0, 120);
  if (pendingSource) {
    $("source-note").textContent = `From: ${pendingSource}`;
    $("source-note").hidden = false;
  }
  show("ask");
}

chrome.storage.session.onChanged.addListener((changes) => {
  if (changes.pendingText?.newValue) loadPending();
});

const STATUS_LABEL = {
  submitted: "processing",
  classified: "processing",
  routed: "processing",
  drafted: "answered",
  escalated: "complaint",
  reviewed: "engineer replied",
  closed: "closed",
};

async function loadTickets() {
  const list = $("ticket-list");
  try {
    const tickets = await api("/tickets");
    list.replaceChildren();
    if (!tickets.length) {
      const li = document.createElement("li");
      li.className = "hint";
      li.textContent = "No tickets yet.";
      list.append(li);
      return;
    }
    for (const t of tickets.slice(0, 15)) {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      const s = document.createElement("span");
      s.textContent = t.subject;
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = STATUS_LABEL[t.status] || t.status;
      b.append(s, badge);
      b.addEventListener("click", () => openTicket(t.id, t.subject));
      li.append(b);
      list.append(li);
    }
  } catch (err) {
    await handle(err);
  }
}

// ---- one ticket ----------------------------------------------------------------------

$("back").addEventListener("click", () => {
  clearPoll();
  current = null;
  show("ask");
  loadTickets();
});

async function openTicket(id, subject) {
  clearPoll();
  current = { id, data: null };
  $("t-subject").textContent = subject || "Your ticket";
  $("t-portal-status").textContent = "";
  show("ticket");
  pollStarted = Date.now();
  await refresh();
}

async function refresh() {
  if (!current) return;
  try {
    const data = await api(`/assist/tickets/${current.id}`);
    if (!current || current.id !== data.ticket_id) return;
    current.data = data;
    render(data);
    if (data.state === "processing" && Date.now() - pollStarted < POLL_LIMIT_MS) {
      pollTimer = setTimeout(refresh, POLL_MS);
    } else if (data.state === "processing") {
      $("t-message").textContent = "This is taking longer than usual. Check back in a few minutes.";
    }
  } catch (err) {
    await handle(err);
  }
}

function render(data) {
  showError("");
  $("t-message").textContent = data.message;
  $("t-processing").hidden = data.state !== "processing";

  const answer = data.state === "answer";
  $("t-answer").hidden = !answer;
  if (answer) {
    $("t-verify").hidden = !data.verify;
    $("t-answer-text").textContent = data.answer;
    const sources = $("t-sources");
    sources.replaceChildren(
      ...data.sources.map((s) => {
        const li = document.createElement("li");
        li.textContent = s.title;
        return li;
      }),
    );
    if (!data.sources.length) sources.replaceChildren(Object.assign(document.createElement("li"), {
      textContent: "No sources listed.",
    }));
  }

  $("t-final").hidden = !data.final_response;
  $("t-final-text").textContent = data.final_response || "";

  // The portal is shown straight away when the knowledge base cannot answer; after an
  // answer, only when the user says it did not help.
  const portalWanted = data.state === "portal" || (answer && current.portalRequested);
  $("t-portal").hidden = !(portalWanted && data.portal && !data.portal_reference);
  if (data.portal) {
    $("t-portal-name").textContent = data.portal.name;
    const dl = $("t-portal-values");
    dl.replaceChildren();
    for (const [key, label] of [["category", "Category"], ["priority", "Priority"], ["subject", "Subject"],
      ["name", "Name"], ["email", "Email"], ["ticket_ref", "Reference"]]) {
      if (!data.portal.field_map[key]) continue;
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = data.portal.values[key] ?? "";
      dd.title = dd.textContent;
      dl.append(dt, dd);
    }
  }

  const ref = $("t-reference");
  ref.hidden = !data.portal_reference;
  ref.replaceChildren();
  if (data.portal_reference) {
    const num = document.createElement("span");
    num.className = "nowrap";
    num.textContent = data.portal_reference;
    ref.append("Complaint filed. The portal's reference number is ", num, ".");
  }
}

$("solved").addEventListener("click", () => {
  $("t-message").textContent = "Glad it helped. An engineer may still follow up in TicketSense.";
});

$("not-solved").addEventListener("click", () => {
  if (!current?.data) return;
  current.portalRequested = true;
  render(current.data);
  if (!current.data.portal) showError("No complaint portal is registered for this ticket yet.");
});

$("open-portal").addEventListener("click", async () => {
  const portal = current?.data?.portal;
  if (!portal) return;
  const origin = `${new URL(portal.url).origin}/*`;
  // Ask for access to the portal's site inside the click (user gesture), only once.
  const granted = (await chrome.permissions.contains({ origins: [origin] })) ||
    (await chrome.permissions.request({ origins: [origin] }).catch(() => false));
  if (!granted) {
    showError(`TicketSense needs permission to fill forms on ${new URL(portal.url).origin}.`);
    return;
  }
  const tab = await chrome.tabs.create({ url: portal.url, active: true });
  await chrome.runtime.sendMessage({ type: "track-portal", tabId: tab.id, ticketId: current.id, portal });
  $("t-portal-status").textContent = "Opening the portal and filling the form…";
});

chrome.runtime.onMessage.addListener((message) => {
  if (!current || message?.ticketId !== current.id) return;
  if (message.type === "portal-filled") {
    $("t-portal-status").textContent =
      `Filled ${message.filled.length} field(s)` +
      (message.missing.length ? `; could not find: ${message.missing.join(", ")}` : "") +
      ". Check the form in the portal tab, then click its Submit button.";
  } else if (message.type === "portal-reference") {
    refresh();
  } else if (message.type === "portal-error") {
    showError(`Portal: ${message.message}`);
  }
});

// ---- start ---------------------------------------------------------------------------

async function start() {
  const { token } = await getSettings();
  if (!token) {
    show("login");
    return;
  }
  try {
    const me = await api("/auth/me");
    if (me.role !== "end_user" && me.role !== "admin") {
      await chrome.storage.session.remove("token");
      showError("The extension is for end-user accounts.");
      show("login");
      return;
    }
    $("who").textContent = me.email;
    show("ask");
    await loadTickets();
    await loadPending();
  } catch (err) {
    await handle(err);
  }
}

start();
