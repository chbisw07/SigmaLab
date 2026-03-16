import React, { useEffect, useState } from "react";
import { api } from "../app/api/client";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";
import type { KiteBrokerState } from "../app/api/types";

export default function SettingsPage() {
  const [health, setHealth] = useState<"ok" | "loading" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  const [kite, setKite] = useState<KiteBrokerState | null>(null);
  const [kiteLoading, setKiteLoading] = useState<boolean>(true);
  const [kiteErr, setKiteErr] = useState<string | null>(null);
  const [saveBusy, setSaveBusy] = useState(false);
  const [testBusy, setTestBusy] = useState(false);
  const [clearBusy, setClearBusy] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [accessToken, setAccessToken] = useState("");

  useEffect(() => {
    setErr(null);
    setHealth("loading");
    api
      .health()
      .then(() => setHealth("ok"))
      .catch((e) => {
        setHealth("error");
        setErr(e instanceof Error ? e.message : String(e));
      });
  }, []);

  useEffect(() => {
    setKiteErr(null);
    setKiteLoading(true);
    api
      .getKiteBrokerState()
      .then((s) => setKite(s))
      .catch((e) => setKiteErr(e instanceof Error ? e.message : String(e)))
      .finally(() => setKiteLoading(false));
  }, []);

  if (health === "error" && err) {
    return <InlineError title="Settings failed to load" error={err} />;
  }

  const kiteConfigured = kite?.configured ?? false;
  const kiteStatus = kite?.status ?? "disconnected";

  async function onSave() {
    setKiteErr(null);
    setSaveBusy(true);
    try {
      const next = await api.saveKiteBrokerCredentials({
        api_key: apiKey.trim() ? apiKey.trim() : null,
        api_secret: apiSecret.trim() ? apiSecret.trim() : null,
        access_token: accessToken.trim() ? accessToken.trim() : null
      });
      setKite(next);
      // Avoid keeping secrets in memory longer than needed.
      setApiKey("");
      setApiSecret("");
      setAccessToken("");
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSaveBusy(false);
    }
  }

  async function onTest() {
    setKiteErr(null);
    setTestBusy(true);
    try {
      await api.testKiteBrokerConnection();
      const next = await api.getKiteBrokerState();
      setKite(next);
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setTestBusy(false);
    }
  }

  async function onClearSession() {
    setKiteErr(null);
    setClearBusy(true);
    try {
      const next = await api.clearKiteBrokerSession();
      setKite(next);
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setClearBusy(false);
    }
  }

  return (
    <div className="page">
      <PageHeader
        title="Settings"
        subtitle="Configuration and system status."
      />

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>System</div>
            <div className="subtle">Backend connectivity and runtime hints.</div>
          </div>
          <span className={`pill ${health === "ok" ? "ok" : ""}`}>Health: {health}</span>
        </div>
        <div className="subtle">
          API base URL is configured in the frontend via <span className="mono">VITE_API_BASE_URL</span>.
        </div>
      </div>

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>Zerodha / Kite (v1)</div>
            <div className="subtle">
              Store Kite credentials encrypted-at-rest in PostgreSQL (requires <span className="mono">SIGMALAB_ENCRYPTION_KEY</span> on the backend).
            </div>
          </div>
          <span
            className={`pill ${kiteStatus === "connected" ? "ok" : kiteStatus === "error" ? "bad" : ""}`}
            title="Broker connection status (last known)"
          >
            Kite: {kiteStatus}
          </span>
        </div>

        {kiteErr ? <InlineError title="Kite settings error" error={kiteErr} /> : null}

        <div className="subtle" style={{ marginBottom: 10 }}>
          {kiteLoading ? (
            "Loading broker state..."
          ) : kite ? (
            <>
              <div>
                Configured: <span className="mono">{String(kiteConfigured)}</span>
              </div>
              <div>
                Masked:{" "}
                <span className="mono">
                  api_key={kite.masked?.api_key ?? "null"} api_secret={kite.masked?.api_secret ?? "null"} access_token=
                  {kite.masked?.access_token ?? "null"}
                </span>
              </div>
              <div>
                Last verified: <span className="mono">{kite.last_verified_at ?? "null"}</span>
              </div>
              {kite.metadata?.profile ? (
                <div style={{ marginTop: 8 }}>
                  Profile: <span className="mono">{JSON.stringify(kite.metadata.profile)}</span>
                </div>
              ) : null}
            </>
          ) : (
            "Broker state unavailable."
          )}
        </div>

        <div className="row" style={{ gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 220px" }}>
            <div className="subtle" style={{ marginBottom: 6 }}>
              API Key (client id)
            </div>
            <input
              className="input"
              placeholder="Paste API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <div style={{ flex: "1 1 220px" }}>
            <div className="subtle" style={{ marginBottom: 6 }}>
              API Secret
            </div>
            <input
              className="input"
              type="password"
              placeholder="Paste API secret"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <div style={{ flex: "1 1 280px" }}>
            <div className="subtle" style={{ marginBottom: 6 }}>
              Access Token (session)
            </div>
            <input
              className="input"
              type="password"
              placeholder="Paste access_token"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <div className="row" style={{ gap: 10 }}>
            <button className="btn" onClick={onSave} disabled={saveBusy}>
              {saveBusy ? "Saving..." : "Save"}
            </button>
            <button className="btn" onClick={onTest} disabled={testBusy}>
              {testBusy ? "Testing..." : "Test connection"}
            </button>
            <button className="btn danger" onClick={onClearSession} disabled={clearBusy}>
              {clearBusy ? "Clearing..." : "Clear session"}
            </button>
          </div>
        </div>

        <div className="subtle" style={{ marginTop: 12 }}>
          Notes:
          <div className="mono" style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
            - Secrets are never returned by the API; only masked values are shown above.
            {"\n"}- Instrument sync and historical backfill require a valid access token.
            {"\n"}- If you prefer env-only config, you can still set SIGMALAB_KITE_API_KEY / SIGMALAB_KITE_ACCESS_TOKEN in backend .env.
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="row" style={{ marginBottom: 10 }}>
          <div>
            <div style={{ fontWeight: 650 }}>CORS (local dev)</div>
            <div className="subtle">
              If the frontend runs on a different origin, configure <span className="mono">SIGMALAB_CORS_ORIGINS</span> in backend `.env`.
            </div>
          </div>
        </div>
        <div className="mono">
          SIGMALAB_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
        </div>
      </div>
    </div>
  );
}
