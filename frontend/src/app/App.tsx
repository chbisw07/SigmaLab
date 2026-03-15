import React from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import DashboardPage from "../pages/DashboardPage";
import WatchlistsPage from "../pages/WatchlistsPage";
import WatchlistDetailPage from "../pages/WatchlistDetailPage";
import StrategiesPage from "../pages/StrategiesPage";
import StrategyDetailPage from "../pages/StrategyDetailPage";
import BacktestNewPage from "../pages/BacktestNewPage";
import BacktestsListPage from "../pages/BacktestsListPage";
import BacktestRunDetailPage from "../pages/BacktestRunDetailPage";
import SettingsPage from "../pages/SettingsPage";
import InstrumentsPage from "../pages/InstrumentsPage";
import ResultsRunRedirect from "../pages/ResultsRunRedirect";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title">SigmaLab</div>
          <div className="brand-sub">Research Workbench</div>
        </div>
        <nav className="nav">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/watchlists">Watchlists</NavLink>
          <NavLink to="/strategies">Strategies</NavLink>
          <NavLink to="/backtests">Backtests</NavLink>
          <NavLink to="/results">Results</NavLink>
          <NavLink to="/instruments">Instruments</NavLink>
          <NavLink to="/settings">Settings</NavLink>
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
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />

          <Route path="/watchlists" element={<WatchlistsPage />} />
          <Route path="/watchlists/:watchlistId" element={<WatchlistDetailPage />} />

          <Route path="/strategies" element={<StrategiesPage />} />
          <Route path="/strategies/:slug" element={<StrategyDetailPage />} />

          <Route path="/backtests" element={<BacktestsListPage />} />
          <Route path="/backtests/new" element={<BacktestNewPage />} />
          <Route path="/backtests/:runId" element={<BacktestRunDetailPage />} />

          {/* UX alias: keep results discoverable while preserving PH8 route compatibility. */}
          <Route path="/results" element={<Navigate to="/backtests" replace />} />
          <Route path="/results/:runId" element={<ResultsRunRedirect />} />

          <Route path="/instruments" element={<InstrumentsPage />} />
          <Route path="/settings" element={<SettingsPage />} />

          <Route path="*" element={<div className="page">Not found</div>} />
        </Routes>
      </main>
    </div>
  );
}
