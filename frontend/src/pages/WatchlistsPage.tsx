import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../app/api/client";
import type { Watchlist } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import EmptyState from "../app/ui/EmptyState";
import InlineError from "../app/ui/InlineError";
import { fmtDateTimeIso } from "../app/ui/format";

export default function WatchlistsPage() {
  const [items, setItems] = useState<Watchlist[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setErr(null);
    try {
      const w = await api.listWatchlists();
      setItems(w);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setItems(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function create() {
    const n = name.trim();
    if (!n) return;
    setCreating(true);
    setErr(null);
    try {
      await api.createWatchlist({ name: n, description: desc.trim() ? desc.trim() : null });
      setName("");
      setDesc("");
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  if (err && items === null) {
    return <InlineError title="Watchlists failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title="Watchlists"
        subtitle="Create symbol universes for watchlist-wide research and backtests."
        actions={
          <button className="btn" onClick={() => void load()}>
            Refresh
          </button>
        }
      />

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div style={{ fontWeight: 650 }}>New watchlist</div>
          <div className="subtle">Names must be unique.</div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 10 }}>
          <input className="input" placeholder="Name (e.g. Swing Candidates)" value={name} onChange={(e) => setName(e.target.value)} />
          <input className="input" placeholder="Description (optional)" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <button className="btn primary" disabled={creating || !name.trim()} onClick={() => void create()}>
            {creating ? "Creating…" : "Create"}
          </button>
        </div>
        {err ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {err}
          </div>
        ) : null}
      </div>

      <div className="panel">
        {items === null ? (
          <div className="subtle">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState
            title="No watchlists yet"
            body={
              <>
                Create a watchlist, then add instruments from the Instruments screen or inside the watchlist detail view.
              </>
            }
            actions={[
              { label: "Sync instruments", to: "/instruments" }
            ]}
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Updated</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((w) => (
                <tr key={w.id}>
                  <td style={{ fontWeight: 650 }}>
                    <Link to={`/watchlists/${w.id}`}>{w.name}</Link>
                  </td>
                  <td className="subtle">{w.description ?? "—"}</td>
                  <td>{fmtDateTimeIso(w.updated_at)}</td>
                  <td style={{ textAlign: "right" }}>
                    <Link to={`/watchlists/${w.id}`} className="btn">
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

