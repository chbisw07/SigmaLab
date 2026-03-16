import React from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import App from "../app/App";
import { mockFetchJson } from "../test/test_utils";

describe("Watchlists List", () => {
  it("renders an empty state when no watchlists exist", async () => {
    mockFetchJson({
      "GET /watchlists": []
    });

    render(
      <MemoryRouter initialEntries={["/watchlists"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Watchlists" })).toBeInTheDocument();
    expect(await screen.findByText("No watchlists yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sync instruments" })).toBeInTheDocument();
  });
});
