import React, { useEffect, useState } from "react";
import { api } from "../app/api/client";
import PageHeader from "../app/ui/PageHeader";
import InlineError from "../app/ui/InlineError";

export default function SettingsPage() {
  const [health, setHealth] = useState<"ok" | "loading" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

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

  if (health === "error" && err) {
    return <InlineError title="Settings failed to load" error={err} />;
  }

  return (
    <div className="page">
      <PageHeader
        title="Settings"
        subtitle="Configuration and system status. PH6 shows what is truly available; broker login UX is later (PH7)."
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
              SigmaLab currently expects Kite credentials to be configured in backend `.env` (no UI-based secret storage yet).
            </div>
          </div>
        </div>
        <div className="subtle">
          Required env vars on the backend:
          <div className="mono" style={{ marginTop: 8 }}>
            SIGMALAB_KITE_API_KEY
            <br />
            SIGMALAB_KITE_ACCESS_TOKEN
          </div>
          <div style={{ marginTop: 10 }}>
            Instrument sync and historical backfill require valid Kite credentials.
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

