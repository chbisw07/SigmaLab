import React from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import App from "../app/App";
import { mockFetchJson } from "../test/test_utils";

describe("Optimizations List", () => {
  it("renders an actionable empty state when there are no jobs", async () => {
    mockFetchJson({
      "GET /optimizations": { status: "ok", jobs: [] }
    });

    render(
      <MemoryRouter initialEntries={["/optimizations"]}>
        <App />
      </MemoryRouter>
    );

    expect(await screen.findByText("No optimization jobs yet")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "New optimization" }).length).toBeGreaterThan(0);
  });
});
