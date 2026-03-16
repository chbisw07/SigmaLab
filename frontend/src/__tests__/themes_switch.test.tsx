import React from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import App from "../app/App";
import { mockFetchJson } from "../test/test_utils";

describe("Themes", () => {
  it("applies a selected theme and persists it", async () => {
    mockFetchJson({
      "GET /health": { status: "ok" },
      "GET /backtests": { status: "ok", runs: [] },
      "GET /watchlists": [],
      "GET /strategies": { status: "ok", strategies: [] }
    });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>
    );

    const btn = await screen.findByRole("button", { name: "Paper" });
    fireEvent.click(btn);

    expect(document.documentElement.dataset.theme).toBe("light_paper");
    expect(localStorage.getItem("sigmalab_theme")).toBe("light_paper");
  });
});

