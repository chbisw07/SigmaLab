import React from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import BacktestsListPage from "../pages/BacktestsListPage";
import BacktestRunDetailPage from "../pages/BacktestRunDetailPage";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title">SigmaLab</div>
          <div className="brand-sub">Results UX (PH8)</div>
        </div>
        <nav className="nav">
          <NavLink to="/backtests">Backtests</NavLink>
        </nav>
        <div style={{ padding: "12px 10px", color: "rgba(255,255,255,0.55)", fontSize: 12 }}>
          API base:{" "}
          <span className="mono">
            {import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"}
          </span>
        </div>
      </aside>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/backtests" replace />} />
          <Route path="/backtests" element={<BacktestsListPage />} />
          <Route path="/backtests/:runId" element={<BacktestRunDetailPage />} />
          <Route path="*" element={<div className="page">Not found</div>} />
        </Routes>
      </main>
    </div>
  );
}

