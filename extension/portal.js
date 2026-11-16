// Functions injected into a complaint portal's tab with chrome.scripting.executeScript.
// They must be self-contained: no imports, no outer variables.

// Write the ticket's values into the portal's form. It never submits the form: the user
// reviews the fields and clicks the portal's own Submit button.
export function fillPortalForm(fieldMap, values) {
  const filled = [];
  const missing = [];
  for (const [field, selector] of Object.entries(fieldMap || {})) {
    const value = values?.[field];
    if (value === undefined || value === null || value === "") continue;
    let el = null;
    try {
      el = document.querySelector(selector);
    } catch {
      el = null;
    }
    if (!el) {
      missing.push(field);
      continue;
    }
    const text = String(value);
    if (el.tagName === "SELECT") {
      const want = text.toLowerCase();
      const option = [...el.options].find(
        (o) => o.value.toLowerCase() === want || o.text.trim().toLowerCase() === want,
      );
      if (!option) {
        missing.push(field);
        continue;
      }
      el.value = option.value;
    } else if (el.isContentEditable) {
      el.textContent = text;
    } else {
      // Use the native setter so frameworks that track input values (React, Vue) see it.
      const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
      if (setter) setter.call(el, text);
      else el.value = text;
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    el.style.outline = "2px solid #0f766e";
    el.style.outlineOffset = "1px";
    filled.push(field);
  }

  document.getElementById("ticketsense-banner")?.remove();
  const banner = document.createElement("div");
  banner.id = "ticketsense-banner";
  banner.setAttribute("role", "status");
  banner.style.cssText =
    "position:fixed;top:12px;right:12px;z-index:2147483647;max-width:340px;padding:12px 14px;" +
    "background:#0f766e;color:#fff;border-radius:8px;font:14px/1.4 system-ui,sans-serif;" +
    "box-shadow:0 6px 20px rgba(0,0,0,.25)";
  const title = document.createElement("strong");
  title.textContent = "TicketSense filled this form";
  const body = document.createElement("div");
  body.textContent =
    `${filled.length} field${filled.length === 1 ? "" : "s"} filled` +
    (missing.length ? `; not found: ${missing.join(", ")}` : "") +
    ". Check every field, then click Submit yourself.";
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Dismiss";
  close.style.cssText =
    "margin-top:8px;background:#fff;color:#0f766e;border:0;border-radius:4px;padding:4px 10px;cursor:pointer;font:inherit";
  close.addEventListener("click", () => banner.remove());
  banner.append(title, body, close);
  document.body.appendChild(banner);
  return { filled, missing };
}

// After the user submits, find the reference number the portal shows.
export function readPortalReference(selector) {
  if (!selector) return null;
  let el = null;
  try {
    el = document.querySelector(selector);
  } catch {
    return null;
  }
  const text = el?.textContent?.trim();
  if (!text) return null;
  const match = text.match(/[A-Za-z0-9][A-Za-z0-9._/-]{0,63}/);
  return match ? match[0] : null;
}
