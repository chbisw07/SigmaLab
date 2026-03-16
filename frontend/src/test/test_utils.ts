import { vi } from "vitest";

type Json = any;

export function mockFetchJson(routes: Record<string, Json>) {
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = (init?.method ?? "GET").toUpperCase();
    const key = `${method} ${new URL(url, "http://localhost").pathname}${new URL(url, "http://localhost").search}`;

    // Match by exact key first.
    if (routes[key] !== undefined) {
      return mkResp(200, routes[key]);
    }

    // Fallback: match by path without query string.
    const pathOnly = `${method} ${new URL(url, "http://localhost").pathname}`;
    if (routes[pathOnly] !== undefined) {
      return mkResp(200, routes[pathOnly]);
    }

    return mkResp(404, { detail: `unmocked fetch: ${key}` });
  });

  vi.stubGlobal("fetch", fn as any);
  return fn;
}

function mkResp(status: number, json: any) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "content-type": "application/json" }),
    async json() {
      return json;
    },
    async text() {
      return typeof json === "string" ? json : JSON.stringify(json);
    }
  } as any;
}

