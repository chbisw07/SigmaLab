import React, { useEffect, useMemo, useState } from "react";
import { api } from "../app/api/client";
import type { Instrument } from "../app/api/types";
import PageHeader from "../app/ui/PageHeader";
import EmptyState from "../app/ui/EmptyState";
import InlineError from "../app/ui/InlineError";

export default function InstrumentsPage() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<Instrument[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  async function load(initial = false) {
    setErr(null);
    try {
      const res = await api.listInstruments(initial ? undefined : q.trim(), "NSE", 50);
      setRows(res);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setRows(null);
    }
  }

  useEffect(() => {
    void load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const hasQuery = useMemo(() => !!q.trim(), [q]);

  async function sync() {
    setSyncing(true);
    setSyncMsg(null);
    setErr(null);
    try {
      const r = await api.syncInstruments();
      setSyncMsg(`Synced instruments. Upserted: ${r.upserted}`);
      await load(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSyncing(false);
    }
  }

  if (err && rows === null) {
    return <InlineError title="Instruments failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title="Instruments"
        subtitle="Sync and search the instrument master used for watchlists and historical data."
        actions={
          <>
            <button className="btn primary" disabled={syncing} onClick={() => void sync()}>
              {syncing ? "Syncing…" : "Sync from Kite"}
            </button>
            <button className="btn" onClick={() => void load(true)}>
              Refresh
            </button>
          </>
        }
      />

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Search</div>
            <div className="subtle">
              Search by symbol or name. UI currently filters to <span className="mono">NSE</span>.
            </div>
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
              if (e.key === "Enter") void load(false);
            }}
          />
          <button className="btn primary" disabled={!hasQuery} onClick={() => void load(false)}>
            Search
          </button>
          <button className="btn" onClick={() => { setQ(""); void load(true); }}>
            Clear
          </button>
        </div>

        {syncMsg ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(52,211,153,0.92)" }}>
            {syncMsg}
          </div>
        ) : null}
        {err ? (
          <div className="subtle" style={{ marginTop: 10, color: "rgba(251,113,133,0.92)" }}>
            {err}
          </div>
        ) : null}
      </div>

      <div className="panel">
        {rows === null ? (
          <div className="subtle">Loading…</div>
        ) : rows.length === 0 ? (
          <EmptyState
            title="No instruments found"
            body={
              <>
                If you haven’t synced yet, click <span className="mono">Sync from Kite</span>. Sync requires Kite API
                key and access token in your backend `.env`.
              </>
            }
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Exchange</th>
                <th>Token</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="mono" style={{ fontWeight: 650 }}>
                    {r.symbol}
                  </td>
                  <td className="subtle">{r.name ?? "—"}</td>
                  <td className="mono">{r.exchange}</td>
                  <td className="mono">{r.broker_instrument_token}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

