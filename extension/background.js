// Service worker: opens the side panel, offers a context-menu entry for selected text,
// and follows complaint-portal tabs: fill the form once it loads, then read the
// reference number after the user submits and record it on the ticket.

import { api } from "./api.js";
import { fillPortalForm, readPortalReference } from "./portal.js";

const MENU_ID = "ticketsense-ask";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "Ask TicketSense about \"%s\"",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID) return;
  // Open first: sidePanel.open must run inside the user gesture.
  if (tab?.windowId !== undefined) chrome.sidePanel.open({ windowId: tab.windowId }).catch(() => {});
  await chrome.storage.session.set({
    pendingText: (info.selectionText || "").slice(0, 4000),
    pendingSource: tab?.url || "",
  });
});

async function tracked() {
  const { portalTabs } = await chrome.storage.session.get("portalTabs");
  return portalTabs || {};
}

async function saveTracked(map) {
  await chrome.storage.session.set({ portalTabs: map });
}

function notify(message) {
  chrome.runtime.sendMessage(message).catch(() => {}); // the panel may be closed
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "track-portal") return false;
  (async () => {
    const map = await tracked();
    map[message.tabId] = {
      ticketId: message.ticketId,
      portalId: message.portal.id,
      fieldMap: message.portal.field_map,
      values: message.portal.values,
      referenceSelector: message.portal.reference_selector,
      origin: new URL(message.portal.url).origin,
      phase: "fill",
    };
    await saveTracked(map);
    sendResponse({ ok: true });
    // A fast page can finish loading before it was registered: handle it now.
    const tab = await chrome.tabs.get(message.tabId).catch(() => null);
    if (tab?.status === "complete") await handleLoaded(message.tabId, tab);
  })();
  return true;
});

chrome.tabs.onUpdated.addListener((tabId, change, tab) => {
  if (change.status === "complete") handleLoaded(tabId, tab);
});

const busy = new Set();

async function handleLoaded(tabId, tab) {
  if (busy.has(tabId)) return; // the same load reported twice
  busy.add(tabId);
  try {
    await step(tabId, tab);
  } finally {
    busy.delete(tabId);
  }
}

async function step(tabId, tab) {
  const map = await tracked();
  const entry = map[tabId];
  if (!entry) return;
  // Only act on the portal's own site; stop following the tab if it navigates away.
  if (!tab.url || new URL(tab.url).origin !== entry.origin) {
    delete map[tabId];
    await saveTracked(map);
    return;
  }
  try {
    if (entry.phase === "fill") {
      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId },
        func: fillPortalForm,
        args: [entry.fieldMap, entry.values],
      });
      entry.phase = "await-reference";
      await saveTracked(map);
      notify({ type: "portal-filled", ticketId: entry.ticketId, ...result });
      return;
    }
    const [{ result: reference }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: readPortalReference,
      args: [entry.referenceSelector],
    });
    if (!reference) return; // e.g. a validation error page; keep waiting
    await api(`/assist/tickets/${entry.ticketId}/portal-reference`, {
      method: "POST",
      json: { reference, portal_id: entry.portalId },
    });
    delete map[tabId];
    await saveTracked(map);
    notify({ type: "portal-reference", ticketId: entry.ticketId, reference });
  } catch (err) {
    notify({ type: "portal-error", ticketId: entry.ticketId, message: String(err?.message || err) });
  }
}

chrome.tabs.onRemoved.addListener(async (tabId) => {
  const map = await tracked();
  if (map[tabId]) {
    delete map[tabId];
    await saveTracked(map);
  }
});
