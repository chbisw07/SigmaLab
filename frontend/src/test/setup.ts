import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";

beforeEach(() => {
  try {
    localStorage.clear();
  } catch {
    // ignore
  }
  // Keep tests deterministic if a prior run modified theme state.
  document.documentElement.dataset.theme = "dark_obsidian";
});
