import React from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import App from "../app/App";
import { mockFetchJson } from "../test/test_utils";

describe("Backtests List", () => {
  it("renders an actionable empty state when there are no runs", async () => {
    mockFetchJson({
      "GET /backtests": { status: "ok", runs: [] }
    });

    render(
      <MemoryRouter initialEntries={["/backtests"]}>
        <App />
      </MemoryRouter>
    );

    expect(await screen.findByText("No backtest runs found yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sync instruments" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create watchlist" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Run backtest" })).toBeInTheDocument();
  });
});

