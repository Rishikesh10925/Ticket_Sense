export type Theme = "light" | "dark";

const STORAGE_KEY = "ticketsense_theme";

// An explicit choice always wins; with none stored, the OS preference decides (see
// the @media block in src/styles/tokens.css) — this just needs to report which one
// is actually in effect so the toggle button shows the right icon.
export function getStoredTheme(): Theme | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

export function getEffectiveTheme(): Theme {
  const stored = getStoredTheme();
  if (stored) return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Private-window/blocked storage — the attribute above still applies for
    // this session, it just won't persist across reloads.
  }
}
