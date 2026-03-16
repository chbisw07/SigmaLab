export type ThemeId =
  | "dark_obsidian"
  | "dark_midnight"
  | "dark_graphite"
  | "light_paper"
  | "light_sand"
  | "light_mint";

export type ThemeMode = "dark" | "light";

export type ThemeDef = {
  id: ThemeId;
  label: string;
  mode: ThemeMode;
  // Used for sidebar swatches only.
  swatchBg: string;
  swatchAccent: string;
};

const STORAGE_KEY = "sigmalab_theme";
export const DEFAULT_THEME: ThemeId = "dark_obsidian";

export const THEMES: ThemeDef[] = [
  { id: "dark_obsidian", label: "Obsidian", mode: "dark", swatchBg: "#0b0f14", swatchAccent: "#2dd4bf" },
  { id: "dark_midnight", label: "Midnight", mode: "dark", swatchBg: "#071024", swatchAccent: "#38bdf8" },
  { id: "dark_graphite", label: "Graphite", mode: "dark", swatchBg: "#111216", swatchAccent: "#f59e0b" },
  { id: "light_paper", label: "Paper", mode: "light", swatchBg: "#f6f7fb", swatchAccent: "#0ea5e9" },
  { id: "light_sand", label: "Sand", mode: "light", swatchBg: "#fbf7ef", swatchAccent: "#f97316" },
  { id: "light_mint", label: "Mint", mode: "light", swatchBg: "#f2fbf8", swatchAccent: "#10b981" }
];

export function isThemeId(v: unknown): v is ThemeId {
  return typeof v === "string" && (THEMES as any[]).some((t) => t.id === v);
}

export function getStoredTheme(): ThemeId | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return isThemeId(v) ? v : null;
  } catch {
    return null;
  }
}

export function storeTheme(id: ThemeId) {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    // ignore (private mode, disabled storage)
  }
}

export function applyTheme(id: ThemeId) {
  // Use <html data-theme="..."> so CSS variables can be themed.
  document.documentElement.dataset.theme = id;
}

export function setTheme(id: ThemeId) {
  storeTheme(id);
  applyTheme(id);
}

export function applyInitialTheme() {
  const stored = getStoredTheme();
  applyTheme(stored ?? DEFAULT_THEME);
}

