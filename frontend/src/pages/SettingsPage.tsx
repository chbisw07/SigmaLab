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
  const [resetBusy, setResetBusy] = useState(false);
  const [loginBusy, setLoginBusy] = useState(false);
  const [connectBusy, setConnectBusy] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [requestToken, setRequestToken] = useState("");
  const [accessToken, setAccessToken] = useState(""); // optional manual mode

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

  async function saveCredsOrThrow() {
    const next = await api.saveKiteBrokerCredentials({
      api_key: apiKey.trim() ? apiKey.trim() : null,
      api_secret: apiSecret.trim() ? apiSecret.trim() : null,
      access_token: accessToken.trim() ? accessToken.trim() : null
    });
    setKite(next);
    // Avoid keeping secrets in memory longer than needed.
    setApiKey("");
    setApiSecret("");
    setRequestToken("");
    setAccessToken("");
  }

  async function onSave() {
    setKiteErr(null);
    setSaveBusy(true);
    try {
      await saveCredsOrThrow();
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSaveBusy(false);
    }
  }

  async function onReset() {
    setKiteErr(null);
    setResetBusy(true);
    try {
      const next = await api.resetKiteBrokerState();
      setKite(next);
      setApiKey("");
      setApiSecret("");
      setRequestToken("");
      setAccessToken("");
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setResetBusy(false);
    }
  }

  async function onOpenLogin() {
    setKiteErr(null);
    setLoginBusy(true);
    try {
      // Ensure api_key/api_secret are saved first if user typed them.
      if (apiKey.trim() || apiSecret.trim()) {
        await saveCredsOrThrow();
      }
      const r = await api.getKiteLoginUrl();
      window.open(r.login_url, "_blank", "noopener,noreferrer");
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoginBusy(false);
    }
  }

  async function onConnectFromRequestToken() {
    setKiteErr(null);
    setConnectBusy(true);
    try {
      // Save api_key/api_secret if user typed them.
      if (apiKey.trim() || apiSecret.trim()) {
        await saveCredsOrThrow();
      }
      const rt = requestToken.trim();
      if (!rt) throw new Error("request_token is required");
      await api.exchangeKiteRequestToken({ request_token: rt });
      const next = await api.getKiteBrokerState();
      setKite(next);
      setRequestToken("");
    } catch (e) {
      setKiteErr(e instanceof Error ? e.message : String(e));
    } finally {
      setConnectBusy(false);
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
              request_token (after login)
            </div>
            <input
              className="input"
              type="password"
              placeholder="Paste request_token"
              value={requestToken}
              onChange={(e) => setRequestToken(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <div className="row" style={{ gap: 10 }}>
            <button className="btn" onClick={onOpenLogin} disabled={loginBusy}>
              {loginBusy ? "Opening..." : "Open Zerodha Login"}
            </button>
            <button className="btn primary" onClick={onConnectFromRequestToken} disabled={connectBusy}>
              {connectBusy ? "Connecting..." : "Connect Zerodha"}
            </button>
            <button
              className="btn"
              onClick={() => setShowAdvanced((v) => !v)}
              aria-expanded={showAdvanced}
              aria-controls="kite-advanced"
              title="Show advanced broker actions"
            >
              {showAdvanced ? "Hide advanced" : "Advanced"}
            </button>
          </div>
        </div>

        {showAdvanced ? (
          <div id="kite-advanced" className="panel" style={{ marginTop: 12, background: "rgba(255,255,255,0.03)" }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 650 }}>Advanced</div>
                <div className="subtle">Optional actions for debugging, token rotation, and recovery.</div>
              </div>
            </div>
            <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
              <button className="btn" onClick={onSave} disabled={saveBusy}>
                {saveBusy ? "Saving..." : "Save api_key/api_secret"}
              </button>
              <button className="btn" onClick={onTest} disabled={testBusy}>
                {testBusy ? "Testing..." : "Test connection"}
              </button>
              <button className="btn danger" onClick={onClearSession} disabled={clearBusy}>
                {clearBusy ? "Clearing..." : "Clear session"}
              </button>
              <button
                className="btn danger"
                onClick={onReset}
                disabled={resetBusy}
                title="Wipes stored broker secrets and status (use if SIGMALAB_ENCRYPTION_KEY changed)"
              >
                {resetBusy ? "Resetting..." : "Reset broker state"}
              </button>
            </div>
          </div>
        ) : null}

        <div className="subtle" style={{ marginTop: 12 }}>
          Notes:
          <div className="mono" style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
            - Secrets are never returned by the API; only masked values are shown above.
            {"\n"}- Flow: Enter api_key/api_secret → Open Zerodha Login → paste request_token → Connect Zerodha.
            {"\n"}- Instrument sync and historical backfill require a valid access token (created by the Connect step).
            {"\n"}- If SIGMALAB_ENCRYPTION_KEY changes, use Advanced → Reset broker state → re-save credentials.
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
