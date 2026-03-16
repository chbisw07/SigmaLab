import React from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import App from "../app/App";
import { mockFetchJson } from "../test/test_utils";

describe("Settings (PH7 Kite broker section)", () => {
  it("renders Kite connection state from the API", async () => {
    mockFetchJson({
      "GET /health": { status: "ok" },
      "GET /settings/broker/kite": {
        broker_name: "zerodha_kite",
        configured: false,
        status: "disconnected",
        masked: {},
        metadata: {},
        last_verified_at: null
      }
    });

    render(
      <MemoryRouter initialEntries={["/settings"]}>
        <App />
      </MemoryRouter>
    );

    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(await screen.findByText("Zerodha / Kite (v1)")).toBeInTheDocument();
    expect(await screen.findByText(/Kite: disconnected/i)).toBeInTheDocument();
  });
});

