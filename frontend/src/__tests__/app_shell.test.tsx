import React from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import App from "../app/App";
import { mockFetchJson } from "../test/test_utils";

describe("App Shell", () => {
  it("renders sidebar navigation and dashboard empty guidance", async () => {
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

    expect(screen.getByText("SigmaLab")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Watchlists" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Strategies" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();

    // Dashboard content becomes available after async fetches resolve.
    expect(await screen.findByText("Recent backtests")).toBeInTheDocument();
    expect(await screen.findByText("No watchlists yet")).toBeInTheDocument();
    expect(await screen.findByText("No backtest runs yet")).toBeInTheDocument();
  });
});
