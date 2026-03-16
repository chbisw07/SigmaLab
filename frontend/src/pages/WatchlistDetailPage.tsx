import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../app/api/client";
import type { Instrument, UUID, Watchlist } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import EmptyState from "../app/ui/EmptyState";
import InlineError from "../app/ui/InlineError";

export default function WatchlistDetailPage() {
  const { watchlistId } = useParams();
  const wid = watchlistId as UUID | undefined;

  const [wl, setWl] = useState<Watchlist | null>(null);
  const [items, setItems] = useState<Instrument[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [editName, setEditName] = useState("");
  const [renaming, setRenaming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<Instrument[]>([]);
  const [actionErr, setActionErr] = useState<string | null>(null);

  async function load() {
    if (!wid) return;
    setErr(null);
    setWl(null);
    setItems(null);
    try {
      const [w, it] = await Promise.all([api.getWatchlist(wid), api.listWatchlistItems(wid)]);
      setWl(w);
      setEditName(w.name);
      setItems(it);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wid]);

  const itemIds = useMemo(() => new Set((items ?? []).map((i) => i.id)), [items]);

  async function search() {
    const qq = q.trim();
    if (!qq) return;
    setSearching(true);
    setActionErr(null);
    try {
      const res = await api.listInstruments(qq, "NSE", 50);
      setResults(res);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSearching(false);
    }
  }

  async function add(instId: UUID) {
    if (!wid) return;
    setActionErr(null);
    try {
      await api.addWatchlistItem(wid, instId);
      const it = await api.listWatchlistItems(wid);
      setItems(it);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function remove(instId: UUID) {
    if (!wid) return;
    setActionErr(null);
    try {
      await api.removeWatchlistItem(wid, instId);
      const it = await api.listWatchlistItems(wid);
      setItems(it);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function rename() {
    if (!wid) return;
    const n = editName.trim();
    if (!n) return;
    if (wl && n === wl.name) return;
    setRenaming(true);
    setActionErr(null);
    try {
      const updated = await api.renameWatchlist(wid, { name: n });
      setWl(updated);
      setEditName(updated.name);
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setRenaming(false);
    }
  }

  async function del() {
    if (!wid) return;
    const name = wl?.name ?? wid;
    const ok = window.confirm(`Delete watchlist "${name}"? This cannot be undone.`);
    if (!ok) return;
    setDeleting(true);
    setActionErr(null);
    try {
      await api.deleteWatchlist(wid);
      window.location.href = "/watchlists";
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setDeleting(false);
    }
  }

  if (!wid) {
    return <InlineError title="Missing watchlist id" error="No watchlist id found in route." />;
  }
  if (err) {
    return <InlineError title="Watchlist failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title={wl?.name ?? "Watchlist"}
        subtitle={
          <>
            <Link to="/watchlists">Watchlists</Link> / <span className="mono">{wid}</span>
          </>
        }
        actions={
          <button className="btn" onClick={() => void load()}>
            Refresh
          </button>
        }
      />

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Instruments</div>
            <div className="subtle">These symbols will be used when you run a backtest on this watchlist.</div>
          </div>
          <Link to={`/backtests/new?watchlist=${encodeURIComponent(wid)}`} className="btn primary">
            Run backtest
          </Link>
        </div>

        {items === null ? (
          <div className="subtle">Loading…</div>
        ) : items.length === 0 ? (
          <EmptyState
            title="No instruments in this watchlist"
            body={<>Search instruments below and add them. Make sure you have synced instruments first.</>}
            actions={[{ label: "Sync instruments", to: "/instruments" }]}
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Exchange</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((i) => (
                <tr key={i.id}>
                  <td className="mono" style={{ fontWeight: 650 }}>
                    {i.symbol}
                  </td>
                  <td className="subtle">{i.name ?? "—"}</td>
                  <td className="mono">{i.exchange}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn" onClick={() => void remove(i.id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Manage watchlist</div>
            <div className="subtle">Rename or delete this watchlist.</div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10, alignItems: "end" }}>
          <div>
            <div className="subtle">Name</div>
            <input className="input" value={editName} onChange={(e) => setEditName(e.target.value)} />
          </div>
          <button className="btn primary" disabled={renaming || !editName.trim() || editName.trim() === (wl?.name ?? "")} onClick={() => void rename()}>
            {renaming ? "Saving…" : "Save"}
          </button>
        </div>

        <div style={{ height: 12 }} />

        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 650, color: "rgba(251,113,133,0.95)" }}>Danger zone</div>
            <div className="subtle">Deleting a watchlist removes the list and its items (not instruments).</div>
          </div>
          <button className="btn" disabled={deleting} onClick={() => void del()} style={{ borderColor: "rgba(251,113,133,0.35)", color: "rgba(251,113,133,0.92)" }}>
            {deleting ? "Deleting…" : "Delete watchlist"}
          </button>
        </div>

        {actionErr ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {actionErr}
          </div>
        ) : null}
      </div>

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Add instruments</div>
            <div className="subtle">Search by symbol or name. (Currently filters to NSE in the UI.)</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <input
            className="input"
            style={{ width: 360 }}
            placeholder="Search (e.g. RELIANCE, HDFCBANK)…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void search();
            }}
          />
          <button className="btn primary" disabled={searching || !q.trim()} onClick={() => void search()}>
            {searching ? "Searching…" : "Search"}
          </button>
          <Link to="/instruments" className="btn">
            Instruments
          </Link>
        </div>
        {actionErr ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {actionErr}
          </div>
        ) : null}

        {results.length ? (
          <div style={{ marginTop: 12 }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Exchange</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {results.map((r) => {
                  const inList = itemIds.has(r.id);
                  return (
                    <tr key={r.id}>
                      <td className="mono" style={{ fontWeight: 650 }}>
                        {r.symbol}
                      </td>
                      <td className="subtle">{r.name ?? "—"}</td>
                      <td className="mono">{r.exchange}</td>
                      <td style={{ textAlign: "right" }}>
                        <button className={`btn ${inList ? "" : "primary"}`} disabled={inList} onClick={() => void add(r.id)}>
                          {inList ? "Added" : "Add"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="subtle" style={{ marginTop: 10 }}>
            Search results will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
